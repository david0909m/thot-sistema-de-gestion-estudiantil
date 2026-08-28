from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.people.models import Estudiante
from apps.academic_core.models import PeriodoLectivo


class Incidencia(models.Model):
    """
    Registro disciplinario, de conducta o reconocimientos por estudiante.
    """
    TIPO_CHOICES = [
        ("LEVE", "Falta Leve"),
        ("GRAVE", "Falta Grave"),
        ("VERY_GRAVE", "Falta Muy Grave"),
        ("MERITO", "Mérito / Reconocimiento"),
    ]

    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name="incidencias", verbose_name="Estudiante"
    )
    periodo = models.ForeignKey(
        PeriodoLectivo, on_delete=models.CASCADE, related_name="incidencias", verbose_name="Período Lectivo"
    )
    fecha = models.DateField(auto_now_add=True, verbose_name="Fecha del suceso")
    tipo_incidencia = models.CharField(
        max_length=20, choices=TIPO_CHOICES, default="LEVE", verbose_name="Tipo de Incidencia"
    )
    descripcion = models.TextField(verbose_name="Descripción detallada de la incidencia")
    sancion = models.TextField(blank=True, verbose_name="Sanción o medidas tomadas")
    reportado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="incidencias_reportadas", verbose_name="Reportado Por"
    )

    class Meta:
        verbose_name = "Incidencia Disciplinaria / Mérito"
        verbose_name_plural = "Incidencias / Méritos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"[{self.get_tipo_incidencia_display()}] {self.estudiante.codigo_estudiante} - {self.fecha}"


class Mensaje(models.Model):
    """
    Mensajería interna con soporte de envío por ámbito.
    """
    AMBITO_CHOICES = [
        ("GLOBAL", "Todos los Usuarios"),
        ("PERIODO", "Todo el Período Lectivo"),
        ("NIVEL", "Por Nivel Educativo"),
        ("CLASE", "Por Clase / Grado"),
        ("SECCION", "Por Sección"),
        ("USUARIO", "Usuario Específico"),
    ]

    remitente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mensajes_enviados", verbose_name="Remitente"
    )
    asunto = models.CharField(max_length=200, verbose_name="Asunto")
    cuerpo = models.TextField(verbose_name="Cuerpo del mensaje")
    fecha_envio = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora de envío")
    ambito_destinatario = models.CharField(
        max_length=30, choices=AMBITO_CHOICES, default="USUARIO", verbose_name="Ámbito de Destino"
    )

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Tipo de objeto destino"
    )
    object_id = models.PositiveIntegerField(blank=True, null=True, verbose_name="ID de objeto destino")
    target_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = "Mensaje Interno"
        verbose_name_plural = "Mensajes Internos"
        ordering = ["-fecha_envio"]

    def __str__(self):
        return f"[{self.get_ambito_destinatario_display()}] {self.asunto} (de {self.remitente.username})"


class MensajeUsuario(models.Model):
    """
    Relación por destinatario equivalente a mensaje_usuarios de Rails: cada
    usuario alcanzado por un mensaje tiene su propia fila con estado de lectura.
    """
    mensaje = models.ForeignKey(
        Mensaje, on_delete=models.CASCADE, related_name="destinatarios", verbose_name="Mensaje"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mensajes_recibidos",
        verbose_name="Usuario Destinatario"
    )
    leido = models.BooleanField(default=False, verbose_name="Leído")
    fecha_leido = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de lectura")

    class Meta:
        verbose_name = "Mensaje por Usuario"
        verbose_name_plural = "Mensajes por Usuario"
        unique_together = ("mensaje", "usuario")

    def __str__(self):
        return f"{self.usuario.username} <- '{self.mensaje.asunto}' ({'leído' if self.leido else 'pendiente'})"


class Adjunto(models.Model):
    """
    Archivos adjuntos genéricos para Mensajes o Incidencias.
    """
    archivo = models.FileField(upload_to="support/adjuntos/", verbose_name="Archivo Adjunto")
    nombre_original = models.CharField(max_length=255, verbose_name="Nombre Original del Archivo")

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = "Archivo Adjunto"
        verbose_name_plural = "Archivos Adjuntos"

    def __str__(self):
        return self.nombre_original
