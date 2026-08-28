import threading


_contexto = threading.local()


def fijar_actor(usuario=None, ip_address=None):
    """
    Registra el actor de la petición actual (usuario e IP) en un almacen
    hilo-local para que las señales de auditoría puedan atribuir los cambios.
    """
    _contexto.usuario = usuario
    _contexto.ip_address = ip_address


def limpiar_actor():
    _contexto.usuario = None
    _contexto.ip_address = None


def obtener_actor():
    """
    Devuelve (usuario, ip_address) del hilo actual; (None, None) si no hay
    contexto de petición (tareas de consola o Celery).
    """
    return (
        getattr(_contexto, "usuario", None),
        getattr(_contexto, "ip_address", None),
    )
