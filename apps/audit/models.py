from django.db import models
from django.db.models import QuerySet
from django.conf import settings


class AuditEventQuerySet(QuerySet):
    def delete(self):
        raise RuntimeError(
            "La bitácora de auditoría es inmutable: no se permite eliminación de eventos."
        )


class AuditEvent(models.Model):
    """
    Bitácora global de eventos inmutables (equivalente a Suceso en Rails).
    Registra eventos globales como inicios de sesión, cambios de contraseña,
    consolidaciones, reaperturas de evaluaciones, auditorías de tareas Celery, etc.
    """
    ORIGEN_CHOICES = [
        ("WEB", "Petición Web"),
        ("CELERY", "Tarea Asíncrona (Celery)"),
        ("CLI", "Comando de Consola / ETL"),
        ("SISTEMA", "Sistema / Señales Internas"),
    ]

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Fecha y hora")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="audit_events",
        verbose_name="Usuario"
    )
    username_log = models.CharField(
        max_length=150, blank=True, verbose_name="Nombre de usuario registrado",
        help_text="Útil cuando la acción falla o es un intento de login de un usuario inexistente"
    )
    ip_address = models.GenericIPAddressField(
        blank=True, null=True, verbose_name="Dirección IP"
    )
    accion = models.CharField(
        max_length=100, db_index=True, verbose_name="Acción / Evento"
    )
    origen = models.CharField(
        max_length=20, choices=ORIGEN_CHOICES, default="WEB", verbose_name="Origen de ejecución"
    )
    objeto_tipo = models.CharField(
        max_length=100, blank=True, verbose_name="Tipo de objeto afectado"
    )
    objeto_id = models.CharField(
        max_length=100, blank=True, verbose_name="ID de objeto afectado"
    )
    descripcion = models.TextField(
        blank=True, verbose_name="Descripción o detalle descriptivo"
    )
    detalles = models.JSONField(
        default=dict, blank=True, verbose_name="Metadatos JSON (Sanitizados)"
    )
    exito = models.BooleanField(
        default=True, verbose_name="¿Ejecución Exitosa?"
    )

    class Meta:
        verbose_name = "Evento de Auditoría"
        verbose_name_plural = "Bitácora Global de Auditoría (AuditEvent)"
        ordering = ["-timestamp"]

    objects = AuditEventQuerySet.as_manager()

    def save(self, *args, **kwargs):
        if self.pk:
            raise RuntimeError(
                "La bitácora de auditoría es inmutable: los eventos no pueden modificarse."
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError(
            "La bitácora de auditoría es inmutable: no se permite eliminar eventos."
        )

    def __str__(self):
        user_str = self.usuario.username if self.usuario else (self.username_log or "Sistema")
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {user_str} - {self.accion}"
