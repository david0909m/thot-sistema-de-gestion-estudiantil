from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from .models import Mensaje, MensajeUsuario, Adjunto, Incidencia
from apps.accounts.models import User
from apps.audit.services import registrar_evento


@transaction.atomic
def enviar_mensaje_interno(remitente, destinatario, asunto, cuerpo, ambito="USUARIO", archivo_adjunto=None):
    """
    Crea y envía un mensaje interno con soporte de archivos adjuntos. Cuando
    el destinatario es un usuario concreto, registra además su fila
    MensajeUsuario equivalente a mensaje_usuarios de Rails.
    """
    es_usuario_directo = isinstance(destinatario, User)
    ct = ContentType.objects.get_for_model(User) if es_usuario_directo else None
    object_id = destinatario.id if es_usuario_directo else None

    mensaje = Mensaje.objects.create(
        remitente=remitente,
        asunto=asunto,
        cuerpo=cuerpo,
        ambito_destinatario=ambito,
        content_type=ct,
        object_id=object_id
    )

    if es_usuario_directo:
        MensajeUsuario.objects.create(mensaje=mensaje, usuario=destinatario)

    if archivo_adjunto:
        ct_mensaje = ContentType.objects.get_for_model(Mensaje)
        Adjunto.objects.create(
            archivo=archivo_adjunto,
            nombre_original=archivo_adjunto.name,
            content_type=ct_mensaje,
            object_id=mensaje.id
        )

    registrar_evento(
        accion="ENVIO_MENSAJE_INTERNO",
        usuario=remitente,
        objeto_tipo="Mensaje",
        objeto_id=str(mensaje.id),
        descripcion=f"Mensaje enviado con asunto '{asunto}'"
    )

    return mensaje
