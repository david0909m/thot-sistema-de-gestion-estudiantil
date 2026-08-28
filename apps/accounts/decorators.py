from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .services_permissions import puede


def requiere_permiso(codigo_permiso: str, get_objeto_func=None):
    """
    Decorador para proteger vistas web en base a las políticas contextuales por ámbito (Fase 0).
    
    :param codigo_permiso: Código identificador del permiso (ej: 'academic.periodos_gestionar')
    :param get_objeto_func: Función opcional (request, *args, **kwargs) que extrae el objeto ámbito a evaluar
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")

            objeto = None
            if get_objeto_func and callable(get_objeto_func):
                objeto = get_objeto_func(request, *args, **kwargs)

            if not puede(request.user, codigo_permiso, objeto=objeto):
                messages.error(
                    request,
                    "Acceso denegado: No cuenta con las atribuciones o el ámbito necesario para realizar esta acción."
                )
                if request.META.get("HTTP_REFERER"):
                    return redirect(request.META.get("HTTP_REFERER"))
                return redirect("dashboard")

            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator
