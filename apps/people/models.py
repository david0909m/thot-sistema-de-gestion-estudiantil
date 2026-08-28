from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords
from apps.academic_core.models import (
    EstadoCivil, Religion, Escolaridad, Recorrido,
    PeriodoLectivo, Clase, Seccion
)


class Docente(models.Model):
    """
    Expediente extendido del profesor.
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil_docente", verbose_name="Usuario de acceso"
    )
    codigo_empleado = models.CharField(max_length=50, unique=True, verbose_name="Código de empleado")
    especialidad = models.CharField(max_length=150, blank=True, verbose_name="Especialidad o área principal")
    telefono = models.CharField(max_length=30, blank=True, verbose_name="Teléfono de contacto")
    direccion = models.TextField(blank=True, verbose_name="Dirección de residencia")
    foto = models.ImageField(upload_to="docentes/fotos/", blank=True, null=True, verbose_name="Fotografía")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Docente / Profesor"
        verbose_name_plural = "Docentes / Profesores"

    def __str__(self):
        full_name = self.usuario.get_full_name() or self.usuario.username
        return f"{self.codigo_empleado} - {full_name}"


class Pariente(models.Model):
    """
    Registro de familiar, padre, madre o tutor legal.
    """
    PARENTESCO_CHOICES = [
        ("PADRE", "Padre"),
        ("MADRE", "Madre"),
        ("TUTOR", "Tutor Legal"),
        ("ABUELO", "Abuelo/a"),
        ("TIO", "Tío/a"),
        ("OTRO", "Otro"),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="perfil_pariente", verbose_name="Usuario de acceso (Opcional)"
    )
    primer_nombre = models.CharField(max_length=50, verbose_name="Primer nombre")
    segundo_nombre = models.CharField(max_length=50, blank=True, verbose_name="Segundo nombre")
    primer_apellido = models.CharField(max_length=50, verbose_name="Primer apellido")
    segundo_apellido = models.CharField(max_length=50, blank=True, verbose_name="Segundo apellido")
    cedula_identidad = models.CharField(
        max_length=30, blank=True, null=True, unique=True, verbose_name="Cédula de identidad"
    )
    parentesco = models.CharField(max_length=50, choices=PARENTESCO_CHOICES, verbose_name="Relación / Parentesco")
    telefono = models.CharField(max_length=30, blank=True, verbose_name="Teléfono de contacto")
    email = models.EmailField(blank=True, verbose_name="Correo electrónico")
    direccion = models.TextField(blank=True, verbose_name="Dirección de residencia")
    lugar_trabajo = models.CharField(max_length=150, blank=True, verbose_name="Lugar de trabajo")
    profesion = models.CharField(max_length=100, blank=True, verbose_name="Profesión u ocupación")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Pariente / Tutor"
        verbose_name_plural = "Parientes / Tutores"

    def get_full_name(self):
        nombres = f"{self.primer_nombre} {self.segundo_nombre}".strip()
        apellidos = f"{self.primer_apellido} {self.segundo_apellido}".strip()
        return f"{nombres} {apellidos}".strip()

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_parentesco_display()})"


class Estudiante(models.Model):
    """
    Expediente único del estudiante.
    """
    GENERO_CHOICES = [
        ("M", "Masculino"),
        ("F", "Femenino"),
    ]

    codigo_estudiante = models.CharField(
        max_length=50, unique=True, verbose_name="Código de estudiante (Carnet)"
    )
    primer_nombre = models.CharField(max_length=50, verbose_name="Primer nombre")
    segundo_nombre = models.CharField(max_length=50, blank=True, verbose_name="Segundo nombre")
    primer_apellido = models.CharField(max_length=50, verbose_name="Primer apellido")
    segundo_apellido = models.CharField(max_length=50, blank=True, verbose_name="Segundo apellido")
    cedula_identidad = models.CharField(
        max_length=30, blank=True, null=True, unique=True, verbose_name="Cédula / Identificación"
    )
    fecha_nacimiento = models.DateField(blank=True, null=True, verbose_name="Fecha de nacimiento")
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, verbose_name="Género")
    
    estado_civil = models.ForeignKey(
        EstadoCivil, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Estado Civil"
    )
    religion = models.ForeignKey(
        Religion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Religión"
    )
    escolaridad = models.ForeignKey(
        Escolaridad, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Escolaridad de Origen"
    )
    recorrido = models.ForeignKey(
        Recorrido, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ruta de Transporte"
    )

    foto = models.ImageField(upload_to="estudiantes/fotos/", blank=True, null=True, verbose_name="Fotografía (Original 600x800)")
    foto_normal = models.ImageField(upload_to="estudiantes/fotos/normal/", blank=True, null=True, verbose_name="Fotografía (Normal 375x500)")
    foto_thumb = models.ImageField(upload_to="estudiantes/fotos/thumb/", blank=True, null=True, verbose_name="Fotografía (Miniatura 75x100)")
    activo = models.BooleanField(default=True, verbose_name="Estudiante Activo")
    retirado = models.BooleanField(default=False, verbose_name="Estado Retirado")
    fecha_retiro = models.DateField(blank=True, null=True, verbose_name="Fecha de retiro")
    motivo_retiro = models.TextField(blank=True, verbose_name="Motivo de retiro")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ["primer_apellido", "primer_nombre"]

    def get_full_name(self):
        nombres = f"{self.primer_nombre} {self.segundo_nombre}".strip()
        apellidos = f"{self.primer_apellido} {self.segundo_apellido}".strip()
        return f"{nombres} {apellidos}".strip()

    def __str__(self):
        return f"{self.codigo_estudiante} - {self.get_full_name()}"


class Responsable(models.Model):
    """
    Vínculo entre un Estudiante y un Pariente.
    """
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name="responsables", verbose_name="Estudiante"
    )
    pariente = models.ForeignKey(
        Pariente, on_delete=models.CASCADE, related_name="estudiantes_a_cargo", verbose_name="Pariente / Tutor"
    )
    es_representante_legal = models.BooleanField(default=True, verbose_name="Es Representante Legal")
    es_responsable_financiero = models.BooleanField(default=True, verbose_name="Es Responsable Financiero")
    convive_con_estudiante = models.BooleanField(default=True, verbose_name="Convive con el estudiante")

    class Meta:
        verbose_name = "Responsable de Estudiante"
        verbose_name_plural = "Responsables de Estudiantes"
        unique_together = ("estudiante", "pariente")

    def __str__(self):
        return f"{self.pariente.get_full_name()} -> {self.estudiante.get_full_name()}"


class EstudianteClase(models.Model):
    """
    Matrícula o inscripción del estudiante en una Clase y Sección dentro de un Período.
    """
    ESTADO_CHOICES = [
        ("INSCRITO", "Inscrito Normal"),
        ("TRASLADADO", "Trasladado de Sección"),
        ("RETIRADO", "Retirado"),
        ("REPITENTE", "Repitente"),
    ]

    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name="inscripciones", verbose_name="Estudiante"
    )
    clase = models.ForeignKey(
        Clase, on_delete=models.CASCADE, related_name="estudiantes_inscritos", verbose_name="Clase / Grado"
    )
    seccion = models.ForeignKey(
        Seccion, on_delete=models.CASCADE, related_name="estudiantes_inscritos", verbose_name="Sección"
    )
    periodo = models.ForeignKey(
        PeriodoLectivo, on_delete=models.CASCADE, related_name="inscripciones", verbose_name="Período Lectivo"
    )
    fecha_inscripcion = models.DateField(auto_now_add=True, verbose_name="Fecha de Inscripción")
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default="INSCRITO", verbose_name="Estado de Matrícula"
    )

    class Meta:
        verbose_name = "Matrícula de Estudiante (EstudianteClase)"
        verbose_name_plural = "Matrículas de Estudiantes"
        unique_together = ("estudiante", "periodo")

    def __str__(self):
        return f"{self.estudiante.codigo_estudiante} en {self.seccion} ({self.periodo.nombre})"


class Estudio(models.Model):
    """
    Estudios o títulos académicos de docentes/usuarios.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="estudios", verbose_name="Usuario"
    )
    titulo = models.CharField(max_length=150, verbose_name="Título o Grado Obtenido")
    institucion = models.CharField(max_length=150, verbose_name="Institución Educativa")
    fecha_obtencion = models.DateField(blank=True, null=True, verbose_name="Fecha de Obtención")

    class Meta:
        verbose_name = "Estudio / Título Academic"
        verbose_name_plural = "Estudios / Títulos Académicos"

    def __str__(self):
        return f"{self.titulo} - {self.institucion}"


class Experiencia(models.Model):
    """
    Experiencia laboral previa de docentes/usuarios.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="experiencias", verbose_name="Usuario"
    )
    cargo = models.CharField(max_length=150, verbose_name="Cargo o Puesto")
    institucion = models.CharField(max_length=150, verbose_name="Empresa u Organización")
    fecha_inicio = models.DateField(verbose_name="Fecha de inicio")
    fecha_fin = models.DateField(blank=True, null=True, verbose_name="Fecha de fin")

    class Meta:
        verbose_name = "Experiencia Laboral"
        verbose_name_plural = "Experiencias Laborales"

    def __str__(self):
        return f"{self.cargo} en {self.institucion}"


class FichaMedica(models.Model):
    """
    Expediente clínico y de salud del estudiante.
    """
    SANGRE_CHOICES = [
        ("O+", "O Positivo (O+)"),
        ("O-", "O Negativo (O-)"),
        ("A+", "A Positivo (A+)"),
        ("A-", "A Negativo (A-)"),
        ("B+", "B Positivo (B+)"),
        ("B-", "B Negativo (B-)"),
        ("AB+", "AB Positivo (AB+)"),
        ("AB-", "AB Negativo (AB-)"),
    ]

    estudiante = models.OneToOneField(
        Estudiante, on_delete=models.CASCADE, related_name="ficha_medica", verbose_name="Estudiante"
    )
    tipo_sangre = models.CharField(max_length=5, choices=SANGRE_CHOICES, blank=True, verbose_name="Tipo de Sangre")
    alergias = models.TextField(blank=True, verbose_name="Alergias a Medicamentos o Alimentos")
    padecimientos_cronicos = models.TextField(blank=True, verbose_name="Padecimientos o Enfermedades Crónicas")
    medicamentos_permanentes = models.TextField(blank=True, verbose_name="Medicamentos de Uso Permanente")
    seguro_medico = models.CharField(max_length=150, blank=True, verbose_name="Compañía de Seguro Médico")
    numero_poliza = models.CharField(max_length=50, blank=True, verbose_name="Número de Póliza / Carnet")
    contacto_emergencia_nombre = models.CharField(max_length=150, blank=True, verbose_name="Contacto de Emergencia")
    contacto_emergencia_telefono = models.CharField(max_length=50, blank=True, verbose_name="Teléfono de Emergencia")
    autoriza_traslado_hospital = models.BooleanField(default=True, verbose_name="Autoriza Traslado Hospitalario de Emergencia")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones Médicas y Restricciones Físicas")

    class Meta:
        verbose_name = "Ficha Médica y de Salud"
        verbose_name_plural = "Fichas Médicas"

    def __str__(self):
        return f"Ficha Médica: {self.estudiante.get_full_name()} ({self.tipo_sangre or 'Sin tipo'})"

