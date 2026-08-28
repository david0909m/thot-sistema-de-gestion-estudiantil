from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Avg

from .models import Evaluacion, Calificacion
from .forms import EvaluacionForm
from .services import (
    crear_evaluacion_con_calificaciones,
    consolidar_calificaciones_materia,
    reabrir_consolidado_materia,
    calcular_promedio_estudiante,
    convertir_nota_a_literal
)
from apps.academic_core.models import PeriodoLectivo, Clase, Seccion, Materia, TipoNota, Escala
from apps.people.models import Estudiante, EstudianteClase
from apps.reporting.models import ConfiguracionInstitucion
from apps.audit.services import registrar_evento
from apps.accounts.decorators import requiere_permiso
from apps.accounts.services_permissions import materias_visibles, secciones_visibles, puede


@login_required(login_url="login")
@requiere_permiso("grading.evaluaciones_gestionar")
def evaluaciones_list_view(request):
    """
    Creación y listado de Evaluaciones por Materia.
    """
    periodo = PeriodoLectivo.objects.filter(activo=True).first() or PeriodoLectivo.objects.first()
    materias = materias_visibles(
        request.user,
        Materia.objects.filter(clase__periodo=periodo)
    ) if periodo else Materia.objects.none()
    materias = materias.select_related("clase", "asignatura", "seccion")
    tipos_notas = TipoNota.objects.filter(periodo=periodo) if periodo else TipoNota.objects.none()

    materia_id = request.GET.get("materia_id")
    if materia_id:
        materia_seleccionada = get_object_or_404(materias, pk=materia_id)
    else:
        materia_seleccionada = materias.first()
    evaluaciones = Evaluacion.objects.filter(materia=materia_seleccionada).select_related("tipo_nota") if materia_seleccionada else []

    return render(
        request,
        "grading/evaluaciones_list.html",
        {
            "periodo": periodo,
            "materias": materias,
            "materia_seleccionada": materia_seleccionada,
            "tipos_notas": tipos_notas,
            "evaluaciones": evaluaciones,
        }
    )


@login_required(login_url="login")
@requiere_permiso("grading.evaluaciones_gestionar")
def evaluacion_create_view(request):
    """
    Formulario para crear una nueva evaluación académica e inicializar las calificaciones de los alumnos.
    """
    materia_id = request.GET.get("materia_id")
    initial_data = {}
    if materia_id:
        initial_data["materia"] = materia_id

    if request.method == "POST":
        form = EvaluacionForm(request.POST)
        if form.is_valid():
            materia = form.cleaned_data["materia"]
            tipo_nota = form.cleaned_data["tipo_nota"]
            nombre = form.cleaned_data["nombre"]
            fecha = form.cleaned_data["fecha"]
            porcentaje = form.cleaned_data["porcentaje"]
            descripcion = form.cleaned_data["descripcion"]

            if not puede(request.user, "grading.evaluaciones_gestionar", objeto=materia):
                registrar_evento(
                    accion="ACCESO_DENEGADO_EVALUACION",
                    usuario=request.user,
                    objeto_tipo="Materia",
                    objeto_id=str(materia.id),
                    descripcion=f"Intento de crear evaluación en materia ajena {materia.nombre}",
                    exito=False
                )
                messages.error(request, "No tiene permisos sobre esta materia.")
                return redirect("evaluaciones_list")

            try:
                evaluacion = crear_evaluacion_con_calificaciones(
                    materia=materia,
                    tipo_nota=tipo_nota,
                    nombre=nombre,
                    fecha=fecha,
                    porcentaje=porcentaje,
                    descripcion=descripcion,
                    usuario=request.user
                )
                messages.success(request, f"Evaluación '{nombre}' creada y lista para ingreso de notas.")
                return redirect(f"/evaluaciones/{evaluacion.id}/notas/")
            except ValidationError as e:
                messages.error(request, str(e.message if hasattr(e, 'message') else e))
    else:
        form = EvaluacionForm(initial=initial_data)

    return render(request, "grading/evaluacion_form.html", {"form": form, "title": "Nueva Evaluación Académica", "is_edit": False})


@login_required(login_url="login")
@requiere_permiso("grading.evaluaciones_gestionar")
def evaluacion_edit_view(request, evaluacion_id):
    """
    Formulario para editar datos de una evaluación académica existente.
    """
    evaluacion = get_object_or_404(Evaluacion, pk=evaluacion_id)
    if not puede(request.user, "grading.evaluaciones_gestionar", objeto=evaluacion.materia):
        messages.error(request, "No tiene permisos sobre esta materia.")
        return redirect("evaluaciones_list")

    if request.method == "POST":
        form = EvaluacionForm(request.POST, instance=evaluacion)
        if form.is_valid():
            form.save()
            messages.success(request, f"Evaluación '{evaluacion.nombre}' actualizada exitosamente.")
            return redirect(f"/evaluaciones/?materia_id={evaluacion.materia.id}")
    else:
        form = EvaluacionForm(instance=evaluacion)

    return render(request, "grading/evaluacion_form.html", {"form": form, "evaluacion": evaluacion, "title": f"Editar Evaluación: {evaluacion.nombre}", "is_edit": True})


@login_required(login_url="login")
@requiere_permiso("grading.notas_ingresar")
def evaluacion_ingreso_notas_view(request, evaluacion_id):
    """
    Planilla rápida interactiva para ingresar y actualizar calificaciones masivamente.
    """
    evaluacion = get_object_or_404(Evaluacion.objects.select_related("materia", "tipo_nota"), pk=evaluacion_id)
    if not puede(request.user, "grading.notas_ingresar", objeto=evaluacion.materia):
        messages.error(request, "No tiene permisos sobre esta materia.")
        return redirect("evaluaciones_list")

    # Asegurar que existan registros de Calificación para todos los alumnos matriculados
    if evaluacion.materia.seccion:
        matriculas = EstudianteClase.objects.filter(seccion=evaluacion.materia.seccion, estado="INSCRITO").select_related("estudiante")
    else:
        matriculas = EstudianteClase.objects.filter(clase=evaluacion.materia.clase, estado="INSCRITO").select_related("estudiante")

    for m in matriculas:
        Calificacion.objects.get_or_create(
            estudiante=m.estudiante,
            evaluacion=evaluacion,
            defaults={
                "materia": evaluacion.materia,
                "tipo_nota": evaluacion.tipo_nota,
                "resultado": Decimal("0.00")
            }
        )

    calificaciones = Calificacion.objects.filter(evaluacion=evaluacion).select_related("estudiante").order_by("estudiante__primer_apellido", "estudiante__primer_nombre")

    if request.method == "POST":
        actualizadas = 0
        for calif in calificaciones:
            input_name = f"nota_{calif.id}"
            if input_name in request.POST:
                val = request.POST.get(input_name, "").strip()
                if val != "":
                    try:
                        calif.resultado = Decimal(val)
                        calif.save()
                        actualizadas += 1
                    except Exception:
                        pass

        registrar_evento(
            accion="INGRESO_MASIVO_NOTAS",
            usuario=request.user,
            objeto_tipo="Evaluacion",
            objeto_id=str(evaluacion.id),
            descripcion=f"Ingreso masivo de {actualizadas} notas en evaluación '{evaluacion.nombre}'"
        )
        messages.success(request, f"¡{actualizadas} calificaciones guardadas exitosamente!")
        return redirect(f"/evaluaciones/{evaluacion.id}/notas/")

    return render(
        request,
        "grading/evaluacion_ingreso_notas.html",
        {
            "evaluacion": evaluacion,
            "calificaciones": calificaciones,
        }
    )


@login_required(login_url="login")
@requiere_permiso("grading.consolidar")
def consolidacion_view(request):
    """
    Consolidación recursiva ponderada de notas, reapertura y cálculo de promedios.
    """
    periodo = PeriodoLectivo.objects.filter(activo=True).first() or PeriodoLectivo.objects.first()
    materias = materias_visibles(
        request.user,
        Materia.objects.filter(clase__periodo=periodo)
    ) if periodo else Materia.objects.none()
    materias = materias.select_related("clase")
    tipos_notas = TipoNota.objects.filter(periodo=periodo) if periodo else TipoNota.objects.none()

    materia_id = request.GET.get("materia_id")
    tipo_nota_id = request.GET.get("tipo_nota_id")

    if materia_id:
        materia = get_object_or_404(materias, pk=materia_id)
    else:
        materia = materias.first()
    tipo_nota = get_object_or_404(TipoNota, pk=tipo_nota_id) if tipo_nota_id else (tipos_notas.first() if tipos_notas else None)

    calificaciones = Calificacion.objects.filter(
        materia=materia, tipo_nota=tipo_nota
    ).select_related("estudiante", "evaluacion") if materia and tipo_nota else []

    if request.method == "POST":
        # 1. Guardar Notas Ingresadas Directamente
        if "guardar_calificaciones" in request.POST:
            for key, val in request.POST.items():
                if key.startswith("calif_"):
                    calif_id = key.replace("calif_", "")
                    if val.strip():
                        calif_obj = Calificacion.objects.filter(pk=calif_id).first()
                        if calif_obj:
                            calif_obj.resultado = Decimal(val)
                            calif_obj.save()
            messages.success(request, "Calificaciones guardadas exitosamente.")
            return redirect(f"/consolidacion/?materia_id={materia.id}&tipo_nota_id={tipo_nota.id}")

        # 2. Ejecutar Consolidación Recursiva
        elif "consolidar" in request.POST:
            redondear = request.POST.get("redondear") == "on"
            consolidados = consolidar_calificaciones_materia(materia, tipo_nota, redondear=redondear, usuario=request.user)

            # Recalcular promedios generales de los estudiantes
            estudiantes = set(c.estudiante for c in consolidados)
            for est in estudiantes:
                calcular_promedio_estudiante(est, periodo)

            messages.success(request, f"¡Consolidación calculada exitosamente para {len(consolidados)} estudiantes!")
            return redirect(f"/consolidacion/?materia_id={materia.id}&tipo_nota_id={tipo_nota.id}")

        # 3. Reabrir Consolidado
        elif "reabrir" in request.POST:
            reabrir_consolidado_materia(materia, tipo_nota, usuario=request.user)
            messages.warning(request, f"Consolidado de {tipo_nota.nombre} reabierto para edición.")
            return redirect(f"/consolidacion/?materia_id={materia.id}&tipo_nota_id={tipo_nota.id}")

    return render(
        request,
        "grading/consolidacion.html",
        {
            "periodo": periodo,
            "materias": materias,
            "tipos_notas": tipos_notas,
            "materia_seleccionada": materia,
            "tipo_nota_seleccionado": tipo_nota,
            "calificaciones": calificaciones,
        }
    )


@login_required(login_url="login")
@requiere_permiso("grading.evaluaciones_gestionar")
def sabana_notas_view(request):
    """
    Sábana General de Calificaciones por Grado / Sección en formato matricial.
    """
    periodo = PeriodoLectivo.objects.filter(activo=True).first() or PeriodoLectivo.objects.first()
    secciones = secciones_visibles(
        request.user,
        Seccion.objects.filter(clase__periodo=periodo)
    ) if periodo else Seccion.objects.none()
    secciones = secciones.select_related("clase")

    seccion_id = request.GET.get("seccion_id")
    if seccion_id:
        seccion_seleccionada = get_object_or_404(secciones, pk=seccion_id)
    else:
        seccion_seleccionada = secciones.first()

    estudiantes = []
    materias = []
    matriz = []

    if seccion_seleccionada:
        matriculas = EstudianteClase.objects.filter(seccion=seccion_seleccionada, estado="INSCRITO").select_related("estudiante").order_by("estudiante__primer_apellido", "estudiante__primer_nombre")
        estudiantes = [m.estudiante for m in matriculas]
        materias = Materia.objects.filter(seccion=seccion_seleccionada).select_related("asignatura")

        # Construir matriz
        for est in estudiantes:
            fila_notas = []
            suma = Decimal("0.00")
            count = 0
            for mat in materias:
                # Tomar la última calificación o promedio consolidado
                calif = Calificacion.objects.filter(estudiante=est, materia=mat, es_consolidado=True).first()
                if not calif:
                    calif = Calificacion.objects.filter(estudiante=est, materia=mat).first()
                
                if calif and calif.resultado is not None:
                    fila_notas.append(calif.resultado)
                    suma += calif.resultado
                    count += 1
                else:
                    fila_notas.append(None)
            
            promedio = round(suma / Decimal(count), 2) if count > 0 else Decimal("0.00")
            matriz.append({
                "estudiante": est,
                "notas": fila_notas,
                "promedio": promedio,
                "aprobado": promedio >= Decimal("60.00")
            })

    return render(
        request,
        "grading/sabana_notas.html",
        {
            "periodo": periodo,
            "secciones": secciones,
            "seccion_seleccionada": seccion_seleccionada,
            "materias": materias,
            "matriz": matriz,
        }
    )


@login_required(login_url="login")
@requiere_permiso("grading.evaluaciones_gestionar")
def boletin_web_view(request, estudiante_id):
    """
    Vista Web oficial del Boletín / Libreta de Calificaciones del estudiante con membrete institucional.
    """
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    if not puede(request.user, "grading.evaluaciones_gestionar", objeto=estudiante):
        messages.error(request, "No tiene permisos para ver este boletín.")
        return redirect("dashboard")

    institucion = ConfiguracionInstitucion.get_solo()
    matricula = EstudianteClase.objects.filter(estudiante=estudiante).select_related("periodo", "clase", "seccion").first()

    periodo = matricula.periodo if matricula else (PeriodoLectivo.objects.filter(activo=True).first() or PeriodoLectivo.objects.first())
    tipos_nota = TipoNota.objects.filter(periodo=periodo, padre__isnull=True).order_by("orden") if periodo else []
    
    materias_data = []
    if matricula:
        materias = Materia.objects.filter(clase=matricula.clase).select_related("asignatura")
        if matricula.seccion:
            materias = materias.filter(seccion=matricula.seccion)

        for mat in materias:
            notas_bloques = []
            suma_mat = Decimal("0.00")
            count_mat = 0
            for tn in tipos_nota:
                calif = Calificacion.objects.filter(estudiante=estudiante, materia=mat, tipo_nota=tn).first()
                nota_val = calif.resultado if calif else None
                if nota_val is not None:
                    suma_mat += nota_val
                    count_mat += 1
                notas_bloques.append(nota_val)

            prom_mat = round(suma_mat / Decimal(count_mat), 2) if count_mat > 0 else Decimal("0.00")
            materias_data.append({
                "materia": mat,
                "notas": notas_bloques,
                "promedio": prom_mat,
                "aprobado": prom_mat >= Decimal("60.00")
            })

    promedio_general = Decimal("0.00")
    if materias_data:
        suma_gral = sum(m["promedio"] for m in materias_data)
        promedio_general = round(suma_gral / Decimal(len(materias_data)), 2)

    return render(
        request,
        "grading/boletin_web.html",
        {
            "estudiante": estudiante,
            "institucion": institucion,
            "matricula": matricula,
            "periodo": periodo,
            "tipos_nota": tipos_nota,
            "materias_data": materias_data,
            "promedio_general": promedio_general,
        }
    )
