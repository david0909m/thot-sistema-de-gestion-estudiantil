from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from .services import registrar_evento


def obtener_historial_entidad(model_class, record_id):
    """
    Retorna la lista ordenada de versiones históricas registradas para una entidad
    (Estudiante, Docente, Pariente, User).
    """
    if not hasattr(model_class, "history"):
        raise AttributeError(f"El modelo {model_class.__name__} no posee historial activado (simple-history).")
    
    return model_class.history.filter(id=record_id).order_by("-history_date")


def consultar_estado_historico_por_fecha(model_class, record_id, fecha_objetivo):
    """
    Reconstruye el estado que poseía una entidad en una fecha/hora específica.
    """
    if not hasattr(model_class, "history"):
        raise AttributeError(f"El modelo {model_class.__name__} no posee historial activado (simple-history).")

    try:
        # as_of reconstruye la instancia tal como existía en la fecha indicada
        return model_class.history.as_of(fecha_objetivo).get(id=record_id)
    except ObjectDoesNotExist:
        return None


@transaction.atomic
def restaurar_version_historica(model_class, record_id, history_id, usuario=None):
    """
    Restaura el estado de una entidad al contenido registrado en una versión histórica específica.
    Emite un evento de auditoría global para trazabilidad.
    """
    if not hasattr(model_class, "history"):
        raise AttributeError(f"El modelo {model_class.__name__} no posee historial activado (simple-history).")

    historical_record = model_class.history.filter(id=record_id, history_id=history_id).first()
    if not historical_record:
        raise ObjectDoesNotExist(f"No se encontró la versión histórica {history_id} para {model_class.__name__} ID {record_id}.")

    # Reify convierte el registro histórico en una instancia del modelo actual
    instancia_restaurada = historical_record.instance
    instancia_restaurada.save()

    registrar_evento(
        accion="RESTAURAR_VERSION_HISTORICA",
        usuario=usuario,
        objeto_tipo=model_class.__name__,
        objeto_id=str(record_id),
        descripcion=f"Restaurada versión histórica history_id={history_id} (Fecha versión: {historical_record.history_date})"
    )

    return instancia_restaurada
