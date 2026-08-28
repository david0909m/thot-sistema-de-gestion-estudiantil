from .context import fijar_actor, limpiar_actor


class ActorAuditMiddleware:
    """
    Publica el usuario autenticado y su IP en el contexto hilo-local de
    auditoría para que señales y servicios atribuyan los eventos al actor
    real incluso cuando el disparador es un post_save.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        limpiar_actor()
        usuario = getattr(request, "user", None)
        if usuario is not None and not getattr(usuario, "is_authenticated", False):
            usuario = None
        fijar_actor(usuario, request.META.get("REMOTE_ADDR"))
        try:
            return self.get_response(request)
        finally:
            limpiar_actor()
