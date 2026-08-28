from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from axes.models import AccessAttempt

from apps.people.models import Estudiante, Docente
from apps.academic_core.models import Clase, PeriodoLectivo
from apps.audit.models import AuditEvent
from apps.audit.services import registrar_evento
from apps.reporting.services import generar_resumen_docentes_xlsx
from apps.accounts.decorators import requiere_permiso
from apps.accounts.services_permissions import es_usuario_global
from .models import Perfil, Permiso, Autorizacion, AsignacionUsuario
from .forms import LoginForm, CambiarPasswordForm, UserAccountForm, PerfilForm

User = get_user_model()


def login_view(request):
    """
    Vista de inicio de sesión utilizando Django Forms y Django Messages.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        # Login por nombre de usuario o correo electrónico (paridad Rails Devise).
        user = authenticate(request, username=username, password=password)
        if user is None and username and "@" in username:
            UserModel = get_user_model()
            usuario_por_correo = UserModel.objects.filter(email__iexact=username).order_by("id").first()
            if usuario_por_correo is not None:
                user = authenticate(request, username=usuario_por_correo.username, password=password)
        if user is not None:
            if user.habilitado:
                login(request, user)
                registrar_evento(
                    accion="LOGIN_EXITOSO",
                    usuario=user,
                    ip_address=request.META.get("REMOTE_ADDR"),
                    origen="WEB",
                    descripcion=f"Inicio de sesión exitoso de {username}"
                )
                if user.requiere_cambio_password:
                    messages.warning(request, "Su cuenta requiere actualización obligatoria de contraseña.")
                    return redirect("cambiar_password")

                messages.success(request, f"¡Bienvenido de nuevo, {user.first_name or user.username}!")
                return redirect("dashboard")
            else:
                messages.error(request, "Su cuenta de usuario se encuentra deshabilitada.")
                registrar_evento(
                    accion="LOGIN_DESHABILITADO",
                    ip_address=request.META.get("REMOTE_ADDR"),
                    origen="WEB",
                    descripcion=f"Intento de acceso con usuario deshabilitado: {username}",
                    exito=False
                )
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
            registrar_evento(
                accion="LOGIN_FALLIDO",
                ip_address=request.META.get("REMOTE_ADDR"),
                origen="WEB",
                descripcion=f"Intento de acceso fallido para usuario: {username}",
                exito=False
            )

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    """
    Cierre de sesión seguro con auditoría y mensajes.
    """
    if request.user.is_authenticated:
        registrar_evento(
            accion="LOGOUT",
            usuario=request.user,
            ip_address=request.META.get("REMOTE_ADDR"),
            origen="WEB",
            descripcion=f"Cierre de sesión del usuario {request.user.username}"
        )
        logout(request)
        messages.info(request, "Ha cerrado su sesión correctamente.")
    return redirect("login")


@login_required(login_url="login")
def cambiar_password_view(request):
    """
    Vista de cambio obligatorio de contraseña (PassController de Rails).
    """
    user = request.user
    form = CambiarPasswordForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        current_password = form.cleaned_data["current_password"]
        new_password = form.cleaned_data["new_password"]

        if not user.check_password(current_password):
            messages.error(request, "La contraseña actual no es válida.")
        else:
            # La nueva contraseña debe pasar los validadores de Django (settings.AUTH_PASSWORD_VALIDATORS).
            try:
                validate_password(new_password, user=user)
            except ValidationError as errores:
                for error in errores.messages:
                    messages.error(request, error)
                return render(request, "accounts/cambiar_password.html", {"form": form})

            user.set_password(new_password)
            user.requiere_cambio_password = False
            # Renovación del ciclo de vencimiento de contraseña (Paridad Rails).
            user.fecha_vencimiento_password = timezone.now() + timedelta(
                days=getattr(settings, "PASSWORD_EXPIRATION_DAYS", 180)
            )
            user.save()

            update_session_auth_hash(request, user)
            registrar_evento(
                accion="CAMBIO_PASSWORD",
                usuario=user,
                ip_address=request.META.get("REMOTE_ADDR"),
                origen="WEB",
                descripcion=f"Cambio obligatorio de contraseña completado para {user.username}"
            )
            messages.success(request, "¡Su contraseña ha sido actualizada exitosamente!")
            return redirect("dashboard")

    return render(request, "accounts/cambiar_password.html", {"form": form})


@login_required(login_url="login")
def dashboard_view(request):
    """
    Dashboard ejecutivo con métricas de rendimiento y auditoría reciente.
    """
    stats = {
        "total_estudiantes": Estudiante.objects.count(),
        "total_docentes": Docente.objects.count(),
        "total_clases": Clase.objects.count(),
        "total_auditorias": AuditEvent.objects.count(),
    }

    eventos_recientes = AuditEvent.objects.all().order_by("-timestamp")[:10]

    return render(
        request,
        "dashboard/index.html",
        {
            "stats": stats,
            "eventos_recientes": eventos_recientes,
        }
    )


@login_required(login_url="login")
def descargar_reporte_docentes_view(request):
    """
    Descarga del reporte XLSX de Carga Académica Docente.
    """
    if not es_usuario_global(request.user):
        messages.error(request, "El reporte de carga docente es de alcance institucional.")
        return redirect("dashboard")

    periodo = PeriodoLectivo.objects.filter(activo=True).first() or PeriodoLectivo.objects.first()
    if not periodo:
        messages.error(request, "No existen períodos lectivos registrados para generar el reporte.")
        return redirect("dashboard")

    buffer = generar_resumen_docentes_xlsx(periodo)
    filename = f"Carga_Docente_{periodo.nombre.replace(' ', '_')}.xlsx"

    messages.success(request, f"Reporte XLSX generado exitosamente para {periodo.nombre}.")
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# =========================================================================
# GESTIÓN DE USUARIOS Y ROLES (SECCIÓN D)
# =========================================================================

@login_required(login_url="login")
@requiere_permiso("admin.usuarios_ver")
def usuarios_list_view(request):
    """
    Directorio administrativo de cuentas de usuario con buscador y estado.
    """
    query = request.GET.get("q", "").strip()
    usuarios = User.objects.all().prefetch_related("asignaciones__perfil").order_by("-is_superuser", "username")

    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(cedula_identidad__icontains=query)
        )

    # Identificar si hay usuarios con intentos fallidos registrados en Axes
    bloqueos_dict = {att.username_accessor: att for att in AccessAttempt.objects.all()}

    return render(
        request,
        "accounts/usuarios_list.html",
        {
            "usuarios": usuarios,
            "query": query,
            "bloqueos_dict": bloqueos_dict,
        }
    )


@login_required(login_url="login")
@requiere_permiso("admin.usuarios_gestionar")
def usuario_create_view(request):
    """
    Alta de nuevas cuentas de usuario del sistema.
    """
    if request.method == "POST":
        form = UserAccountForm(request.POST)
        if form.is_valid():
            user = form.save()
            registrar_evento(
                accion="CREAR_USUARIO",
                usuario=request.user,
                objeto_tipo="User",
                objeto_id=str(user.id),
                descripcion=f"Cuenta de usuario '{user.username}' creada."
            )
            messages.success(request, f"Usuario '{user.username}' creado exitosamente.")
            return redirect("usuarios_list")
    else:
        form = UserAccountForm()

    return render(request, "accounts/usuario_form.html", {"form": form, "title": "Crear Nueva Cuenta de Usuario", "is_edit": False})


@login_required(login_url="login")
@requiere_permiso("admin.usuarios_gestionar")
def usuario_edit_view(request, user_id):
    """
    Edición de cuenta de usuario y reseteo de credenciales.
    """
    target_user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = UserAccountForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            registrar_evento(
                accion="EDITAR_USUARIO",
                usuario=request.user,
                objeto_tipo="User",
                objeto_id=str(target_user.id),
                descripcion=f"Cuenta de usuario '{target_user.username}' actualizada."
            )
            messages.success(request, f"Usuario '{target_user.username}' actualizado.")
            return redirect("usuarios_list")
    else:
        form = UserAccountForm(instance=target_user)

    return render(request, "accounts/usuario_form.html", {"form": form, "target_user": target_user, "title": f"Editar Usuario: {target_user.username}", "is_edit": True})


@login_required(login_url="login")
@requiere_permiso("admin.usuarios_gestionar")
def usuario_unlock_axes_view(request, username):
    """
    Desbloqueo de seguridad de cuenta reseteando los intentos fallidos de Axes.
    """
    AccessAttempt.objects.filter(username_accessor=username).delete()
    registrar_evento(
        accion="DESBLOQUEO_SEGURIDAD_AXES",
        usuario=request.user,
        descripcion=f"Desbloqueo manual de intentos fallidos para usuario {username}"
    )
    messages.success(request, f"¡Seguridad y bloqueos reseteados para '{username}'!")
    return redirect("usuarios_list")


@login_required(login_url="login")
@requiere_permiso("admin.roles_ver")
def roles_list_view(request):
    """
    Matriz centralizada de roles (Perfiles) y capacidades/permisos asociados.
    """
    perfiles = Perfil.objects.prefetch_related("autorizaciones__permiso").all()
    permisos_total = Permiso.objects.count()

    return render(
        request,
        "accounts/roles_list.html",
        {
            "perfiles": perfiles,
            "permisos_total": permisos_total,
        }
    )


@login_required(login_url="login")
@requiere_permiso("admin.roles_gestionar")
def rol_create_view(request):
    """
    Creación de nuevo rol institucional con asignación granular de permisos.
    """
    if request.method == "POST":
        form = PerfilForm(request.POST)
        if form.is_valid():
            perfil = form.save()
            permisos_seleccionados = form.cleaned_data.get("permisos", [])
            for perm in permisos_seleccionados:
                Autorizacion.objects.create(perfil=perfil, permiso=perm)

            registrar_evento(
                accion="CREAR_ROL",
                usuario=request.user,
                objeto_tipo="Perfil",
                objeto_id=str(perfil.id),
                descripcion=f"Rol '{perfil.nombre}' creado con {len(permisos_seleccionados)} permisos."
            )
            messages.success(request, f"Rol '{perfil.nombre}' creado exitosamente.")
            return redirect("roles_list")
    else:
        form = PerfilForm()

    return render(request, "accounts/rol_form.html", {"form": form, "title": "Crear Nuevo Perfil / Rol", "is_edit": False})


@login_required(login_url="login")
@requiere_permiso("admin.roles_gestionar")
def rol_edit_view(request, rol_id):
    """
    Edición de rol institucional y actualización de su matriz de permisos.
    """
    perfil = get_object_or_404(Perfil, pk=rol_id)
    if request.method == "POST":
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            perfil = form.save()
            permisos_seleccionados = form.cleaned_data.get("permisos", [])
            Autorizacion.objects.filter(perfil=perfil).delete()
            for perm in permisos_seleccionados:
                Autorizacion.objects.create(perfil=perfil, permiso=perm)

            registrar_evento(
                accion="EDITAR_ROL",
                usuario=request.user,
                objeto_tipo="Perfil",
                objeto_id=str(perfil.id),
                descripcion=f"Rol '{perfil.nombre}' actualizado con {len(permisos_seleccionados)} permisos."
            )
            messages.success(request, f"Rol '{perfil.nombre}' actualizado.")
            return redirect("roles_list")
    else:
        permisos_actuales = Permiso.objects.filter(perfiles_autorizados__perfil=perfil)
        form = PerfilForm(instance=perfil, initial={"permisos": permisos_actuales})

    return render(request, "accounts/rol_form.html", {"form": form, "perfil": perfil, "title": f"Editar Rol: {perfil.nombre}", "is_edit": True})
