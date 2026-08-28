from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import AuditEvent
from apps.accounts.decorators import requiere_permiso


@login_required(login_url="login")
@requiere_permiso("audit.ver_bitacora")
def auditoria_list_view(request):
    """
    Visor completo de la bitácora global de auditoría protegido por políticas de permisos.
    """
    query = request.GET.get("q", "").strip()
    eventos = AuditEvent.objects.all()

    if query:
        eventos = eventos.filter(
            Q(accion__icontains=query) |
            Q(username_log__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(ip_address__icontains=query)
        )

    eventos = eventos.order_by("-timestamp")[:100]
    return render(request, "audit/list.html", {"eventos": eventos, "query": query})
