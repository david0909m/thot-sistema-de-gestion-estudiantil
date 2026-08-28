from .context import obtener_actor
from .models import AuditEvent


def registrar_evento(
    accion,
    usuario=None,
    username_log="",
    ip_address=None,
    origen="WEB",
    objeto_tipo="",
    objeto_id="",
    descripcion="",
    detalles=None,
    exito=True
):
    """
    Función de servicio centralizada para registrar eventos inmutables de auditoría.
    Garantiza sanitización básica para no incluir contraseñas o secretos en `detalles`.
    Cuando no se reciben actor o IP explícitos, los toma del contexto de la
    petición actual (thread-local fijado por ActorAuditMiddleware).
    """
    if usuario is None or ip_address is None:
        ctx_usuario, ctx_ip = obtener_actor()
        if usuario is None:
            usuario = ctx_usuario
        if ip_address is None:
            ip_address = ctx_ip

    if detalles is None:
        detalles = {}

    # Sanitización de secretos en el diccionario de detalles
    keys_to_sanitize = ["password", "token", "secret", "clave", "contrasena"]
    sanitized_details = {}
    if isinstance(detalles, dict):
        for key, value in detalles.items():
            if any(s in key.lower() for s in keys_to_sanitize):
                sanitized_details[key] = "[PROTEGIDO]"
            else:
                sanitized_details[key] = value
    else:
        sanitized_details = {"raw": str(detalles)}

    username = username_log
    if not username and usuario and hasattr(usuario, "username"):
        username = usuario.username

    event = AuditEvent.objects.create(
        accion=accion,
        usuario=usuario,
        username_log=username,
        ip_address=ip_address,
        origen=origen,
        objeto_tipo=objeto_tipo,
        objeto_id=str(objeto_id) if objeto_id else "",
        descripcion=descripcion,
        detalles=sanitized_details,
        exito=exito
    )
    return event
