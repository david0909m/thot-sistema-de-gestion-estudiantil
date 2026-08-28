from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from .models import Incidencia, Mensaje, Adjunto
from .services import enviar_mensaje_interno
from apps.people.models import Estudiante
from apps.academic_core.models import PeriodoLectivo
from apps.accounts.models import User
from apps.accounts.decorators import requiere_permiso
from apps.accounts.services_permissions import (
    puede, estudiantes_visibles, puede_leer_mensaje
)
from apps.audit.services import registrar_evento


def _incidencias_visibles(usuario, periodo):
    """
    Incidencias del período alcanzables según el ámbito del usuario.
    """
    incidencias = Incidencia.objects.filter(periodo=periodo) if periodo else Incidencia.objects.none()
    return incidencias.filter(
        estudiante__in=estudiantes_visibles(usuario)
    ).select_related("estudiante", "reportado_por")


@login_required(login_url="login")
@requiere_permiso("support.incidencias_ver")
def incidencias_list_view(request):
    """
    Lista y registro de incidencias disciplinarias y reconocimientos de estudiantes.
    """
    periodo = PeriodoLectivo.objects.filter(activo=True).first() or PeriodoLectivo.objects.first()
    incidencias = _incidencias_visibles(request.user, periodo)
    estudiantes = estudiantes_visibles(request.user).filter(activo=True)

    if request.method == "POST" and "crear_incidencia" in request.POST:
        estudiante_id = request.POST.get("estudiante_id")
        tipo = request.POST.get("tipo_incidencia")
        descripcion = request.POST.get("descripcion", "").strip()
        sancion = request.POST.get("sancion", "").strip()

        estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
        if not puede(request.user, "support.incidencias_gestionar", objeto=estudiante):
            messages.error(request, "Acceso denegado: no cuenta con atribuciones para registrar incidencias en este ámbito.")
            return redirect("incidencias_list")

        incidencia = Incidencia.objects.create(
            estudiante=estudiante,
            periodo=periodo,
            tipo_incidencia=tipo,
            descripcion=descripcion,
            sancion=sancion,
            reportado_por=request.user
        )

        messages.success(request, f"Incidencia registrada exitosamente para {estudiante.get_full_name()}.")
        return redirect("incidencias_list")

    return render(
        request,
        "support/incidencias_list.html",
        {
            "periodo": periodo,
            "incidencias": incidencias,
            "estudiantes": estudiantes,
        }
    )


@login_required(login_url="login")
@requiere_permiso("support.incidencias_ver")
def incidencia_detail_view(request, incidencia_id):
    """
    Expediente de seguimiento y detalle de una incidencia disciplinaria o mérito.
    La actualización de sanción exige atribución de gestión, no de lectura.
    """
    incidencia = get_object_or_404(
        Incidencia.objects.select_related("estudiante", "periodo", "reportado_por"), pk=incidencia_id
    )
    if not puede(request.user, "support.incidencias_ver", objeto=incidencia.estudiante):
        messages.error(request, "Acceso denegado: la incidencia pertenece a un estudiante fuera de su ámbito.")
        return redirect("incidencias_list")

    if request.method == "POST" and "actualizar_sancion" in request.POST:
        if not puede(request.user, "support.incidencias_gestionar", objeto=incidencia.estudiante):
            messages.error(request, "Acceso denegado: no cuenta con atribuciones para modificar esta incidencia.")
            return redirect("incidencia_detail", incidencia_id=incidencia.id)

        sancion = request.POST.get("sancion", "").strip()
        incidencia.sancion = sancion
        incidencia.save()
        registrar_evento(
            accion="EDITAR_INCIDENCIA",
            usuario=request.user,
            objeto_tipo="Incidencia",
            objeto_id=str(incidencia.id),
            descripcion=f"Sanción actualizada en incidencia de {incidencia.estudiante.codigo_estudiante}"
        )
        messages.success(request, "Medida disciplinaria y sanción actualizadas.")
        return redirect("incidencia_detail", incidencia_id=incidencia.id)

    return render(request, "support/incidencia_detail.html", {"incidencia": incidencia})


@login_required(login_url="login")
@requiere_permiso("support.mensajes_ver")
def mensajes_inbox_view(request):
    """
    Bandeja de entrada personalizada y redactar mensaje interno.
    """
    ct_user = ContentType.objects.get_for_model(User)
    mensajes_recibidos = Mensaje.objects.filter(
        Q(remitente=request.user) |
        Q(content_type=ct_user, object_id=request.user.id) |
        Q(destinatarios__usuario=request.user) |
        Q(ambito_destinatario="GLOBAL")
    ).select_related("remitente").distinct()[:50]

    usuarios = User.objects.exclude(id=request.user.id)

    if request.method == "POST" and "enviar_mensaje" in request.POST:
        destinatario_id = request.POST.get("destinatario_id")
        asunto = request.POST.get("asunto", "").strip()
        cuerpo = request.POST.get("cuerpo", "").strip()
        archivo = request.FILES.get("archivo_adjunto")

        if not puede(request.user, "support.mensajes_enviar"):
            messages.error(request, "Acceso denegado: no cuenta con atribuciones para enviar mensajes.")
            return redirect("mensajes_inbox")

        destinatario = get_object_or_404(User, pk=destinatario_id) if destinatario_id else None
        enviar_mensaje_interno(request.user, destinatario, asunto, cuerpo, archivo_adjunto=archivo)

        messages.success(request, "Mensaje enviado exitosamente.")
        return redirect("mensajes_inbox")

    return render(
        request,
        "support/mensajes_inbox.html",
        {
            "mensajes_recibidos": mensajes_recibidos,
            "usuarios": usuarios,
        }
    )


@login_required(login_url="login")
@requiere_permiso("support.mensajes_ver")
def mensaje_detail_view(request, mensaje_id):
    """
    Lectura completa de un mensaje interno con visualizador y descarga de archivos adjuntos.
    Sólo el remitente, el destinatario directo o una audiencia global pueden leerlo;
    se bloquea el acceso por URL directa a mensajes ajenos.
    """
    mensaje = get_object_or_404(Mensaje.objects.select_related("remitente"), pk=mensaje_id)

    if not puede_leer_mensaje(request.user, mensaje):
        registrar_evento(
            accion="ACCESO_MENSAJE_DENEGADO",
            usuario=request.user,
            objeto_tipo="Mensaje",
            objeto_id=str(mensaje.id),
            descripcion="Intento de lectura de mensaje ajeno mediante URL directa.",
            exito=False
        )
        messages.error(request, "Acceso denegado: el mensaje no le corresponde.")
        return redirect("mensajes_inbox")

    ct_mensaje = ContentType.objects.get_for_model(Mensaje)
    adjuntos = Adjunto.objects.filter(content_type=ct_mensaje, object_id=mensaje.id)

    return render(
        request,
        "support/mensaje_detail.html",
        {
            "mensaje": mensaje,
            "adjuntos": adjuntos,
        }
    )
