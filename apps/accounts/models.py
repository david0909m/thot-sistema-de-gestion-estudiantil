from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from simple_history.models import HistoricalRecords


class User(AbstractUser):
    """
    Modelo de usuario personalizado para THOT / THOT.
    Sustituye Devise y gestiona requerimientos de seguridad heredados.
    """
    segundo_nombre = models.CharField(max_length=50, blank=True, verbose_name="Segundo nombre")
    segundo_apellido = models.CharField(max_length=50, blank=True, verbose_name="Segundo apellido")
    cedula_identidad = models.CharField(
        max_length=30, blank=True, null=True, unique=True, verbose_name="Cédula de identidad"
    )
    requiere_cambio_password = models.BooleanField(
        default=False,
        help_text="Indica si el usuario debe cambiar su contraseña en el próximo inicio de sesión (expired_password).",
        verbose_name="Requiere cambio de contraseña"
    )
    habilitado = models.BooleanField(
        default=True,
        help_text="Indica si el usuario está habilitado para acceder al sistema.",
        verbose_name="Habilitado"
    )
    ultimo_acceso_ip = models.GenericIPAddressField(
        blank=True, null=True, verbose_name="Última IP de acceso"
    )
    fecha_vencimiento_password = models.DateTimeField(
        blank=True, null=True, verbose_name="Fecha de vencimiento de contraseña"
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        full_name = self.get_full_name()
        return f"{self.username} - {full_name}" if full_name else self.username


class Perfil(models.Model):
    """
    Perfil funcional (ej: Administrador, Docente, Pariente, Alumno, Secretaría).
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del perfil")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código identificador")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

    def __str__(self):
        return self.nombre


class Permiso(models.Model):
    """
    Catálogo granular de capacidades del sistema (equivalente a permissions.yml).
    """
    nombre = models.CharField(max_length=150, verbose_name="Nombre del permiso")
    codigo = models.CharField(max_length=100, unique=True, verbose_name="Código del permiso")
    modulo = models.CharField(max_length=50, verbose_name="Módulo funcional")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"

    def __str__(self):
        return f"[{self.modulo}] {self.nombre} ({self.codigo})"


class Autorizacion(models.Model):
    """
    Asociación M2M entre Perfil y Permiso.
    """
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="autorizaciones")
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE, related_name="perfiles_autorizados")

    class Meta:
        verbose_name = "Autorización"
        verbose_name_plural = "Autorizaciones"
        unique_together = ("perfil", "permiso")

    def __str__(self):
        return f"{self.perfil.nombre} -> {self.permiso.codigo}"


class AsignacionUsuario(models.Model):
    """
    Asignación contextual de un usuario con un perfil sobre un objeto o ámbito específico
    (ej: Rol de Docente sobre la Clase 5A, o Pariente sobre un Estudiante concreto).
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="asignaciones")
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="asignaciones_usuario")
    
    # Referencia polimórfica al objeto ámbito (opcional; si es null, la asignación es global)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Tipo de objeto ámbito"
    )
    object_id = models.PositiveIntegerField(blank=True, null=True, verbose_name="ID de objeto ámbito")
    ambito_objeto = GenericForeignKey("content_type", "object_id")

    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_inicio = models.DateField(blank=True, null=True, verbose_name="Fecha de inicio")
    fecha_fin = models.DateField(blank=True, null=True, verbose_name="Fecha de fin")

    class Meta:
        verbose_name = "Asignación de Usuario"
        verbose_name_plural = "Asignaciones de Usuario"

    def __str__(self):
        ambito_str = f" en {self.ambito_objeto}" if self.ambito_objeto else " (Global)"
        return f"{self.usuario.username} como {self.perfil.nombre}{ambito_str}"
