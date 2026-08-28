from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.people.models import Estudiante
from apps.grading.models import Evaluacion
from apps.support.models import Incidencia
from .services import registrar_evento


@receiver(post_save, sender=Estudiante)
def auditar_guardado_estudiante(sender, instance, created, **kwargs):
    accion = "CREAR_ESTUDIANTE" if created else "ACTUALIZAR_ESTUDIANTE"
    registrar_evento(
        accion=accion,
        origen="SISTEMA",
        objeto_tipo="Estudiante",
        objeto_id=str(instance.id),
        descripcion=f"{'Creación' if created else 'Actualización'} del expediente de estudiante {instance.codigo_estudiante}"
    )


@receiver(post_delete, sender=Estudiante)
def auditar_eliminacion_estudiante(sender, instance, **kwargs):
    registrar_evento(
        accion="ELIMINAR_ESTUDIANTE",
        origen="SISTEMA",
        objeto_tipo="Estudiante",
        objeto_id=str(instance.id),
        descripcion=f"Eliminación del expediente del estudiante {instance.codigo_estudiante}"
    )


@receiver(post_save, sender=Incidencia)
def auditar_guardado_incidencia(sender, instance, created, **kwargs):
    if created:
        registrar_evento(
            accion="CREAR_INCIDENCIA",
            origen="SISTEMA",
            objeto_tipo="Incidencia",
            objeto_id=str(instance.id),
            descripcion=f"Incidencia {instance.tipo_incidencia} registrada para {instance.estudiante.codigo_estudiante}"
        )


@receiver(post_save, sender=Evaluacion)
def auditar_guardado_evaluacion(sender, instance, created, **kwargs):
    accion = "CREAR_EVALUACION" if created else "ACTUALIZAR_EVALUACION"
    registrar_evento(
        accion=accion,
        origen="SISTEMA",
        objeto_tipo="Evaluacion",
        objeto_id=str(instance.id),
        descripcion=f"{'Creación' if created else 'Actualización'} de la evaluación '{instance.nombre}' en {instance.materia.nombre}"
    )


@receiver(post_delete, sender=Evaluacion)
def auditar_eliminacion_evaluacion(sender, instance, **kwargs):
    registrar_evento(
        accion="ELIMINAR_EVALUACION",
        origen="SISTEMA",
        objeto_tipo="Evaluacion",
        objeto_id=str(instance.id),
        descripcion=f"Eliminación de la evaluación '{instance.nombre}' de {instance.materia.nombre}"
    )
