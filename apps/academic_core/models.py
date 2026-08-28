from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal


# --- Catálogos Generales ---

class EstadoCivil(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Nombre")
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden de visualización")

    class Meta:
        verbose_name = "Estado Civil"
        verbose_name_plural = "Estados Civiles"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Religion(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Nombre")
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden de visualización")

    class Meta:
        verbose_name = "Religión"
        verbose_name_plural = "Religiones"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Escolaridad(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Nombre")
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden de visualización")

    class Meta:
        verbose_name = "Escolaridad"
        verbose_name_plural = "Escolaridades"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Recorrido(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del recorrido / ruta")
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código de ruta")
    descripcion = models.TextField(blank=True, verbose_name="Descripción o ruta detallada")

    class Meta:
        verbose_name = "Recorrido"
        verbose_name_plural = "Recorridos"

    def __str__(self):
        return self.nombre


# --- Estructura Académica Base ---

class Nivel(models.Model):
    """
    Niveles educativos (ej: Preescolar, Primaria, Secundaria).
    """
    nombre = models.CharField(max_length=100, verbose_name="Nombre del nivel")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código de nivel")
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden jerárquico")
    config = models.JSONField(default=dict, blank=True, verbose_name="Configuración heredable")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Nivel Educativo"
        verbose_name_plural = "Niveles Educativos"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Asignatura(models.Model):
    """
    Catálogo general de materias o asignaturas.
    """
    nombre = models.CharField(max_length=150, verbose_name="Nombre de asignatura")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código de asignatura")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Asignatura"
        verbose_name_plural = "Asignaturas"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Escala(models.Model):
    """
    Escala de calificación (ej: Escala de 0 a 100, Escala Cualitativa/Literal).
    """
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la escala")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    escala = models.JSONField(
        default=dict, blank=True,
        verbose_name="Estructura de la escala (Rangos o Literales)",
        help_text="Ejemplo: {'A': [90, 100], 'B': [80, 89], 'C': [60, 79], 'F': [0, 59]}"
    )
    nota_minima_aprobatoria = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("60.00"), verbose_name="Nota mínima aprobatoria"
    )
    nota_maxima = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("100.00"), verbose_name="Nota máxima"
    )

    class Meta:
        verbose_name = "Escala de Calificación"
        verbose_name_plural = "Escalas de Calificación"

    def __str__(self):
        return f"{self.nombre} (Aprobatoria: {self.nota_minima_aprobatoria})"


# --- Períodos Lectivos y Tipos de Nota ---

class PeriodoLectivo(models.Model):
    """
    Período lectivo o año escolar (ej: Año Escolar 2026).
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del período")
    fecha_inicio = models.DateField(verbose_name="Fecha de inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de fin")
    activo = models.BooleanField(
        default=False, verbose_name="Activo",
        help_text="Marque como activo si es el período lectivo corriente del colegio."
    )
    abierto = models.BooleanField(
        default=True, verbose_name="Abierto a modificaciones",
        help_text="Si está cerrado, se bloquea el ingreso de calificaciones."
    )
    visible = models.BooleanField(
        default=True, verbose_name="Visible a usuarios",
        help_text="Controla si el período es visible en la interfaz para alumnos/padres."
    )
    config = models.JSONField(
        default=dict, blank=True, verbose_name="Configuración heredable del período"
    )

    class Meta:
        verbose_name = "Período Lectivo"
        verbose_name_plural = "Períodos Lectivos"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        estado = "Activo" if self.activo else "Inactivo"
        return f"{self.nombre} ({estado})"

    def clean(self):
        super().clean()
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin <= self.fecha_inicio:
            raise ValidationError({"fecha_fin": "La fecha de fin debe ser posterior a la fecha de inicio."})
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin > self.fecha_inicio:
            traslapes = PeriodoLectivo.objects.filter(
                fecha_inicio__lte=self.fecha_fin,
                fecha_fin__gte=self.fecha_inicio,
            )
            if self.pk:
                traslapes = traslapes.exclude(pk=self.pk)
            traslapado = traslapes.order_by("fecha_inicio").first()
            if traslapado:
                raise ValidationError(
                    {"fecha_inicio": f"El período se traslapa con {traslapado.nombre}."}
                )

    def copiar_estructura(self, nuevo_nombre, nueva_fecha_inicio, nueva_fecha_fin):
        """
        Copia integralmente este período lectivo con su cadena de TipoNota, Clases, Secciones y Materias asociadas (Traducción exacta de copiar! de Rails).
        """
        from django.db import transaction

        with transaction.atomic():
            nuevo_periodo = PeriodoLectivo.objects.create(
                nombre=nuevo_nombre,
                fecha_inicio=nueva_fecha_inicio,
                fecha_fin=nueva_fecha_fin,
                activo=False,
                abierto=True,
                visible=self.visible,
                config=self.config
            )
            
            # 1. Clonación de Tipos de Nota
            mapa_tipos = {}
            tipos_origen = self.tipos_notas.all().order_by("orden")
            
            for tipo in tipos_origen:
                nuevo_tipo = TipoNota.objects.create(
                    nombre=tipo.nombre,
                    periodo=nuevo_periodo,
                    padre=None,
                    es_consolidado=tipo.es_consolidado,
                    orden=tipo.orden,
                    peso=tipo.peso,
                    porcentaje=tipo.porcentaje,
                    numero_consolidados=tipo.numero_consolidados,
                    config=tipo.config
                )
                mapa_tipos[tipo.id] = nuevo_tipo
                
            for tipo in tipos_origen:
                if tipo.padre_id and tipo.padre_id in mapa_tipos:
                    hijo_clonado = mapa_tipos[tipo.id]
                    hijo_clonado.padre = mapa_tipos[tipo.padre_id]
                    hijo_clonado.save()

            # 2. Clonación de Clases, Secciones y Materias
            from apps.accounts.models import AsignacionUsuario

            for clase_orig in self.clases.all():
                nueva_clase = Clase.objects.create(
                    periodo=nuevo_periodo,
                    nivel=clase_orig.nivel,
                    nombre=clase_orig.nombre,
                    config=clase_orig.config
                )

                mapa_secciones = {}
                for sec_orig in clase_orig.secciones.all():
                    nueva_sec = Seccion.objects.create(
                        clase=nueva_clase,
                        nombre=sec_orig.nombre,
                        codigo=f"{sec_orig.codigo}_{nuevo_periodo.id}",
                        docente=sec_orig.docente,
                        capacidad_maxima=sec_orig.capacidad_maxima
                    )
                    mapa_secciones[sec_orig.id] = nueva_sec

                for mat_orig in clase_orig.materias.all():
                    sec_destino = mapa_secciones.get(mat_orig.seccion_id) if mat_orig.seccion_id else None
                    config_limpio = {
                        clave: valor for clave, valor in (mat_orig.config or {}).items()
                        if clave != "periodo_actual_hash"
                    }
                    nueva_mat = Materia.objects.create(
                        nombre=mat_orig.nombre,
                        asignatura=mat_orig.asignatura,
                        clase=nueva_clase,
                        seccion=sec_destino,
                        docente=mat_orig.docente,
                        config=config_limpio,
                        lock_version=0
                    )
                    # Copiar asignaciones auxiliares DocenteMateria si existen
                    for dm in mat_orig.asignaciones_docentes.all():
                        DocenteMateria.objects.create(
                            materia=nueva_mat,
                            docente=dm.docente,
                            es_titular=dm.es_titular
                        )

                    # Copiar horarios asociados si existen
                    for hor in mat_orig.horarios.all():
                        Horario.objects.create(
                            materia=nueva_mat,
                            dia_semana=hor.dia_semana,
                            hora_inicio=hor.hora_inicio,
                            hora_fin=hor.hora_fin,
                            aula=hor.aula
                        )

                # Copiar asignaciones contextuales de usuarios a nivel clase
                ct_clase = ContentType.objects.get_for_model(Clase)
                asignaciones_clase = AsignacionUsuario.objects.filter(
                    content_type=ct_clase,
                    object_id=clase_orig.id,
                    activo=True,
                ).select_related("usuario", "perfil")
                for au in asignaciones_clase:
                    AsignacionUsuario.objects.create(
                        usuario=au.usuario,
                        perfil=au.perfil,
                        content_type=ct_clase,
                        object_id=nueva_clase.id,
                        activo=True,
                        fecha_inicio=au.fecha_inicio,
                        fecha_fin=au.fecha_fin,
                    )

            return nuevo_periodo



class TipoNota(models.Model):
    """
    Estructura jerárquica de evaluaciones y consolidados (ej: Bloque -> Parcial 1 -> Examen).
    """
    nombre = models.CharField(max_length=100, verbose_name="Nombre del tipo de nota")
    periodo = models.ForeignKey(
        PeriodoLectivo, on_delete=models.CASCADE, related_name="tipos_notas", verbose_name="Período Lectivo"
    )
    padre = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="hijos", verbose_name="Tipo Nota Padre"
    )
    es_consolidado = models.BooleanField(
        default=False, verbose_name="Es un consolidado",
        help_text="Indica si este tipo de nota se calcula agregando las notas hijas."
    )
    orden = models.PositiveIntegerField(default=1, verbose_name="Orden de secuencia")
    peso = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("1.00"), verbose_name="Peso"
    )
    porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name="Porcentaje acumulado"
    )
    numero_consolidados = models.PositiveIntegerField(default=0, verbose_name="Número de consolidados")
    config = models.JSONField(default=dict, blank=True, verbose_name="Configuración adicional")

    class Meta:
        verbose_name = "Tipo de Nota"
        verbose_name_plural = "Tipos de Nota"
        ordering = ["periodo", "orden"]

    def __str__(self):
        padre_str = f" (Hijo de {self.padre.nombre})" if self.padre else ""
        return f"[{self.periodo.nombre}] {self.nombre}{padre_str}"


# --- Estructura Concreta: Clase, Sección, Materia y Horarios ---

class Clase(models.Model):
    """
    Clase o Grado académico específico en un período y nivel (ej: 5to Grado 2026).
    """
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la clase")
    periodo = models.ForeignKey(
        PeriodoLectivo, on_delete=models.CASCADE, related_name="clases", verbose_name="Período Lectivo"
    )
    nivel = models.ForeignKey(
        Nivel, on_delete=models.CASCADE, related_name="clases", verbose_name="Nivel Educativo"
    )
    config = models.JSONField(default=dict, blank=True, verbose_name="Configuración de la clase")

    class Meta:
        verbose_name = "Clase / Grado"
        verbose_name_plural = "Clases / Grados"
        ordering = ["periodo", "nivel__orden", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.periodo.nombre})"


class Seccion(models.Model):
    """
    Sección o grupo específico dentro de una Clase (ej: Sección A).
    """
    nombre = models.CharField(max_length=50, verbose_name="Nombre de sección")
    codigo = models.CharField(max_length=20, verbose_name="Código de sección")
    clase = models.ForeignKey(
        Clase, on_delete=models.CASCADE, related_name="secciones", verbose_name="Clase / Grado"
    )
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="secciones_como_guia", verbose_name="Docente Guía",
        help_text="Profesor guía responsable de la sección (equivalente a secciones.docente_id en Rails)."
    )
    capacidad_maxima = models.PositiveIntegerField(default=40, verbose_name="Capacidad máxima de estudiantes")

    class Meta:
        verbose_name = "Sección"
        verbose_name_plural = "Secciones"
        unique_together = ("clase", "codigo")
        ordering = ["clase", "codigo"]

    def __str__(self):
        return f"{self.clase.nombre} - {self.nombre}"


class Materia(models.Model):
    """
    Instancia de una Asignatura dictada en una Clase o Sección determinada.
    Incluye `lock_version` para bloqueo optimista ante edicion concurrente.
    """
    nombre = models.CharField(max_length=150, verbose_name="Nombre descriptivo de la materia")
    asignatura = models.ForeignKey(
        Asignatura, on_delete=models.CASCADE, related_name="materias", verbose_name="Asignatura Base"
    )
    clase = models.ForeignKey(
        Clase, on_delete=models.CASCADE, related_name="materias", verbose_name="Clase / Grado"
    )
    seccion = models.ForeignKey(
        Seccion, on_delete=models.SET_NULL, null=True, blank=True, related_name="materias", verbose_name="Sección específica"
    )
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="materias_impartidas", verbose_name="Docente Titular"
    )
    lock_version = models.IntegerField(
        default=0, verbose_name="Versión de Bloqueo Optimista",
        help_text="Controla actualizaciones concurrentes para evitar sobrescrituras accidentales."
    )
    config = models.JSONField(default=dict, blank=True, verbose_name="Configuración específica de la materia")

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"
        ordering = ["clase", "nombre"]

    def __str__(self):
        seccion_str = f" [{self.seccion.nombre}]" if self.seccion else ""
        return f"{self.nombre}{seccion_str} - {self.clase.nombre}"

    def save(self, *args, **kwargs):
        if self.pk:
            with transaction.atomic():
                original = Materia.objects.select_for_update().only("lock_version").get(pk=self.pk)
                if original.lock_version != self.lock_version:
                    raise ValidationError(
                        "Error de concurrencia: La materia ha sido modificada por otro usuario. Por favor recargue."
                    )
                self.lock_version = original.lock_version + 1
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)


class Horario(models.Model):
    """
    Horario de impartición de una materia.
    """
    DIA_CHOICES = [
        (1, "Lunes"),
        (2, "Martes"),
        (3, "Miércoles"),
        (4, "Jueves"),
        (5, "Viernes"),
        (6, "Sábado"),
        (7, "Domingo"),
    ]

    materia = models.ForeignKey(
        Materia, on_delete=models.CASCADE, related_name="horarios", verbose_name="Materia"
    )
    dia_semana = models.PositiveSmallIntegerField(choices=DIA_CHOICES, verbose_name="Día de la semana")
    hora_inicio = models.TimeField(verbose_name="Hora de inicio")
    hora_fin = models.TimeField(verbose_name="Hora de fin")
    aula = models.CharField(max_length=50, blank=True, verbose_name="Aula o espacio físico")

    class Meta:
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"
        ordering = ["dia_semana", "hora_inicio"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.hora_fin and self.hora_inicio and self.hora_fin <= self.hora_inicio:
            raise ValidationError("La hora de fin debe ser posterior a la hora de inicio.")
        
        if self.materia and self.materia.seccion_id:
            intersect = Horario.objects.filter(
                materia__seccion=self.materia.seccion,
                dia_semana=self.dia_semana,
                hora_inicio__lt=self.hora_fin,
                hora_fin__gt=self.hora_inicio
            )
            if self.pk:
                intersect = intersect.exclude(pk=self.pk)
            if intersect.exists():
                raise ValidationError("El horario se traslapa con otra entrada en la misma sección.")

    def __str__(self):
        return f"{self.get_dia_semana_display()}: {self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')} ({self.materia.nombre})"


class DocenteMateria(models.Model):
    """
    Asignación secundaria o compartida de docentes a una materia.
    """
    materia = models.ForeignKey(
        Materia, on_delete=models.CASCADE, related_name="asignaciones_docentes", verbose_name="Materia"
    )
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="asignaciones_materias", verbose_name="Docente"
    )
    es_titular = models.BooleanField(default=True, verbose_name="¿Es titular?")

    class Meta:
        verbose_name = "Docente por Materia"
        verbose_name_plural = "Docentes por Materia"
        unique_together = ("materia", "docente")

    def __str__(self):
        titular_str = " (Titular)" if self.es_titular else " (Auxiliar)"
        return f"{self.docente.get_full_name() or self.docente.username} -> {self.materia.nombre}{titular_str}"
