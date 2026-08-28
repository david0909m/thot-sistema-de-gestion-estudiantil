from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.academic_core.models import TipoNota, PeriodoLectivo, Escala
from apps.people.models import EstudianteClase
from apps.audit.services import registrar_evento
from .models import Evaluacion, Calificacion, ResumenAcademicoEstudiante


def convertir_nota_a_literal(nota_decimal, escala=None):
    """
    Convierte una calificación numérica decimal a su representación literal según la Escala configurada.
    """
    if nota_decimal is None:
        return ""

    if not escala:
        if nota_decimal >= Decimal("90.00"):
            return "A"
        elif nota_decimal >= Decimal("80.00"):
            return "B"
        elif nota_decimal >= Decimal("70.00"):
            return "C"
        elif nota_decimal >= Decimal("60.00"):
            return "D"
        else:
            return "F"

    # Si existe un objeto Escala en la base de datos
    config_escala = getattr(escala, "escala", None) or getattr(escala, "config", None)
    if isinstance(config_escala, dict):
        for literal, rango in config_escala.items():
            if isinstance(rango, (list, tuple)) and len(rango) == 2:
                if Decimal(str(rango[0])) <= nota_decimal <= Decimal(str(rango[1])):
                    return str(literal)
        rangos = config_escala.get("rangos", [])
        for r in rangos:
            min_val = Decimal(str(r.get("minimo", 0)))
            max_val = Decimal(str(r.get("maximo", 100)))
            if min_val <= nota_decimal <= max_val:
                return str(r.get("literal", ""))

    return "A" if nota_decimal >= Decimal("90.00") else "F"


@transaction.atomic
def crear_evaluacion_con_calificaciones(
    materia,
    tipo_nota,
    nombre,
    fecha,
    porcentaje=Decimal("0.00"),
    nota_maxima=Decimal("100.00"),
    es_examen=False,
    es_reparacion=False,
    descripcion="",
    usuario=None
):
    """
    Crea una evaluación y autogenera filas de calificación iniciales (vacías)
    para todos los estudiantes matriculados activamente en el curso.
    """
    # Validar suma de porcentajes acumulados de evaluaciones bajo este tipo_nota
    evaluaciones_existentes = Evaluacion.objects.filter(materia=materia, tipo_nota=tipo_nota)
    porcentaje_acumulado = sum(e.porcentaje for e in evaluaciones_existentes)
    if porcentaje_acumulado + porcentaje > Decimal("100.00"):
        raise ValidationError(
            f"El porcentaje total de evaluaciones para {tipo_nota.nombre} superaría el 100% "
            f"(Actual: {porcentaje_acumulado}%, Nueva: {porcentaje}%)."
        )

    evaluacion = Evaluacion.objects.create(
        materia=materia,
        tipo_nota=tipo_nota,
        nombre=nombre,
        fecha=fecha,
        porcentaje=porcentaje,
        nota_maxima=nota_maxima,
        es_examen=es_examen,
        es_reparacion=es_reparacion,
        descripcion=descripcion
    )

    # Buscar alumnos matriculados en la clase/sección de la materia
    inscripciones = EstudianteClase.objects.filter(
        clase=materia.clase,
        periodo=materia.clase.periodo
    )
    if materia.seccion:
        inscripciones = inscripciones.filter(seccion=materia.seccion)

    calificaciones = [
        Calificacion(
            evaluacion=evaluacion,
            estudiante=inscripcion.estudiante,
            materia=materia,
            tipo_nota=tipo_nota,
            resultado=None,
            es_consolidado=False,
            modificado_por=usuario
        )
        for inscripcion in inscripciones
    ]
    Calificacion.objects.bulk_create(calificaciones)

    return evaluacion


@transaction.atomic
def consolidar_calificaciones_materia(materia, tipo_nota, redondear=False, usuario=None):
    """
    Ejecuta el cálculo recursivo de consolidación de calificaciones para una materia y tipo de nota.
    Mantiene la precisión de `Decimal` de extremo a extremo y genera los registros consolidados.
    """
    calificaciones_materia = Calificacion.objects.filter(materia=materia).select_related("estudiante")
    estudiantes_ids = set(calificaciones_materia.values_list("estudiante_id", flat=True))

    consolidados_generados = []

    for est_id in estudiantes_ids:
        total_acumulado = Decimal("0.00")
        tiene_notas = False

        hijos = tipo_nota.hijos.all()
        if hijos.exists():
            for hijo in hijos:
                nota_hijo = Calificacion.objects.filter(
                    materia=materia, tipo_nota=hijo, estudiante_id=est_id, es_consolidado=True
                ).first()
                if nota_hijo and nota_hijo.resultado is not None:
                    tiene_notas = True
                    peso_hijo = hijo.porcentaje / Decimal("100.00") if hijo.porcentaje > Decimal("0") else hijo.peso
                    total_acumulado += nota_hijo.resultado * peso_hijo

        evaluaciones = tipo_nota.evaluaciones.filter(materia=materia)
        if evaluaciones.exists():
            for eval_item in evaluaciones:
                calif_eval = Calificacion.objects.filter(
                    evaluacion=eval_item, estudiante_id=est_id
                ).first()
                if calif_eval and calif_eval.resultado is not None:
                    tiene_notas = True
                    factor_escalar = Decimal("100.00") / eval_item.nota_maxima if eval_item.nota_maxima > Decimal("0") else Decimal("1")
                    nota_normalizada = calif_eval.resultado * factor_escalar
                    peso_eval = eval_item.porcentaje / Decimal("100.00") if eval_item.porcentaje > Decimal("0") else Decimal("1.00")
                    total_acumulado += nota_normalizada * peso_eval

        resultado_final = None
        if tiene_notas:
            if redondear:
                resultado_final = total_acumulado.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            else:
                resultado_final = total_acumulado.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        padre_obj = None
        if tipo_nota.padre:
            padre_obj = Calificacion.objects.filter(
                materia=materia, tipo_nota=tipo_nota.padre, estudiante_id=est_id, es_consolidado=True
            ).first()

        consolidado, _ = Calificacion.objects.update_or_create(
            materia=materia,
            tipo_nota=tipo_nota,
            estudiante_id=est_id,
            es_consolidado=True,
            defaults={
                "resultado": resultado_final,
                "calificacion_padre": padre_obj,
                "modificado_por": usuario,
                "observacion": f"Consolidado calculado ({'Redondeado' if redondear else 'Decimal Exacto'})"
            }
        )
        consolidados_generados.append(consolidado)

    registrar_evento(
        accion="CONSOLIDAR_CALIFICACIONES",
        usuario=usuario,
        objeto_tipo="Materia",
        objeto_id=str(materia.id),
        descripcion=f"Consolidación completada para {materia.nombre} - {tipo_nota.nombre} ({len(consolidados_generados)} alumnos)."
    )

    return consolidados_generados


@transaction.atomic
def reabrir_consolidado_materia(materia, tipo_nota, usuario=None):
    """
    Reabre la edición de evaluaciones consolidadas permitiendo modificaciones posteriores de notas.
    """
    filas_afectadas = Calificacion.objects.filter(
        materia=materia, tipo_nota=tipo_nota, es_consolidado=True
    ).update(resultado=None, observacion="Reabierto para modificación")

    registrar_evento(
        accion="REABRIR_CONSOLIDADO",
        usuario=usuario,
        objeto_tipo="Materia",
        objeto_id=str(materia.id),
        descripcion=f"Reapertura de consolidado {tipo_nota.nombre} en {materia.nombre} ({filas_afectadas} registros reseteados)."
    )

    return filas_afectadas


@transaction.atomic
def calcular_promedio_estudiante(estudiante, periodo):
    """
    Calcula el promedio general acumulado de un estudiante para un período lectivo dado
    consultando sus notas consolidadas finales de cada materia.
    """
    consolidados_finales = Calificacion.objects.filter(
        estudiante=estudiante,
        materia__clase__periodo=periodo,
        es_consolidado=True,
        resultado__isnull=False
    )

    if not consolidados_finales.exists():
        return None

    suma_notas = sum(c.resultado for c in consolidados_finales)
    cantidad = Decimal(consolidados_finales.count())
    promedio = (suma_notas / cantidad).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    reprobadas = consolidados_finales.filter(resultado__lt=Decimal("60.00")).count()

    resumen, _ = ResumenAcademicoEstudiante.objects.update_or_create(
        estudiante=estudiante,
        periodo=periodo,
        defaults={
            "promedio_general": promedio,
            "materias_reprobadas": reprobadas
        }
    )

    return resumen
