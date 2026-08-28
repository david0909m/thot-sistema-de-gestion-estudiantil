from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone


class PasswordExpirationMiddleware:
    """
    Middleware que intercepta peticiones HTTP para obligar al usuario
    a cambiar su contraseña si su campo `requiere_cambio_password` es True
    o si su `fecha_vencimiento_password` ha expirado.
    (Equivalente a check_password_expiration! de Rails / PassController).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            expired_by_flag = getattr(request.user, "requiere_cambio_password", False)
            expired_by_date = False
            vencimiento = getattr(request.user, "fecha_vencimiento_password", None)
            if vencimiento and timezone.now() > vencimiento:
                expired_by_date = True

            if expired_by_flag or expired_by_date:
                # Excepciones permitidas mientras requiere cambio de clave
                allowed_paths = [
                    reverse("cambiar_password"),
                    reverse("logout"),
                    "/static/",
                ]
                path = request.path_info
                
                if not any(path.startswith(p) for p in allowed_paths):
                    messages.warning(
                        request,
                        "Su contraseña ha caducado o requiere cambio obligatorio por seguridad antes de continuar."
                    )
                    return redirect("cambiar_password")

        response = self.get_response(request)
        return response
