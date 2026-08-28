from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from datetime import date

from .models import (
    PeriodoLectivo, Nivel, Clase, Seccion, Asignatura,
    Materia, Horario, DocenteMateria, Escala, TipoNota,
    EstadoCivil, Religion, Escolaridad, Recorrido
)
from .forms import (
    ConfiguracionInstitucionForm, PeriodoLectivoForm, NivelForm,
    ClaseForm, SeccionForm, AsignaturaForm, EscalaForm, TipoNotaForm
)
from apps.reporting.models import ConfiguracionInstitucion
from apps.accounts.models import User
from apps.audit.services import registrar_evento
from apps.accounts.decorators import requiere_permiso


# =========================================================================
# CONFIGURACIÓN INSTITUCIONAL DE MARCA BLANCA
# =========================================================================

@login_required(login_url="login")
@requiere_permiso("academic.periodos_gestionar")
def configuracion_institucion_view(request):
    """
    Formulario para personalizar nombre, logo, lema e identidad institucional de marca blanca.
    """
    institucion = ConfiguracionInstitucion.get_solo()
    if request.method == "POST":
        form = ConfiguracionInstitucionForm(request.POST, request.FILES, instance=institucion)
        if form.is_valid():
            form.save()
            registrar_evento(
                accion="CONFIGURACION_INSTITUCIONAL",
                usuario=request.user,
                objeto_tipo="ConfiguracionInstitucion",
                objeto_id=str(institucion.id),
                descripcion=f"Identidad institucional actualizada: {institucion.nombre_institucion}"
            )
            messages.success(request, "Configuración institucional guardada exitosamente.")
            return redirect("configuracion_institucion")
    else:
        form = ConfiguracionInstitucionForm(instance=institucion)

    return render(request, "academic_core/configuracion_institucion.html", {"form": form, "institucion": institucion})


# =========================================================================
# PERÍODOS LECTIVOS
# =========================================================================

@login_required(login_url="login")
@requiere_permiso("academic.periodos_gestionar")
def periodos_list_view(request):
    """
    Lista de Períodos Lectivos y acción de clonación profunda de estructura.
    """
    periodos = PeriodoLectivo.objects.all().order_by("-fecha_inicio")

    if request.method == "POST" and "clonar_periodo_id" in request.POST:
        periodo_id = request.POST.get("clonar_periodo_id")
        nuevo_nombre = request.POST.get("nuevo_nombre", "").strip()
        periodo_origen = get_object_or_404(PeriodoLectivo, pk=periodo_id)

        if nuevo_nombre:
            nuevo_inicio = date(periodo_origen.fecha_inicio.year + 1, 1, 15)
            nuevo_fin = date(periodo_origen.fecha_fin.year + 1, 11, 30)

            periodo_clonado = periodo_origen.copiar_estructura(nuevo_nombre, nuevo_inicio, nuevo_fin)
            registrar_evento(
                accion="CLONAR_PERIODO_LECTIVO",
                usuario=request.user,
                objeto_tipo="PeriodoLectivo",
                objeto_id=str(periodo_clonado.id),
                descripcion=f"Estructura profunda clonada desde {periodo_origen.nombre} hacia {nuevo_nombre}"
            )
            messages.success(request, f"¡Estructura clonada exitosamente para el nuevo período '{nuevo_nombre}'!")
            return redirect("periodos_list")
        else:
            messages.error(request, "Por favor ingrese un nombre válido para el nuevo período.")

    return render(request, "academic_core/periodos_list.html", {"periodos": periodos})


@login_required(login_url="login")
@requiere_permiso("academic.periodos_gestionar")
def periodo_create_view(request):
    """
    Formulario web para crear un nuevo período lectivo.
    """
    if request.method == "POST":
        form = PeriodoLectivoForm(request.POST)
        if form.is_valid():
            periodo = form.save()
            registrar_evento(
                accion="CREAR_PERIODO",
                usuario=request.user,
                objeto_tipo="PeriodoLectivo",
                objeto_id=str(periodo.id),
                descripcion=f"Período lectivo '{periodo.nombre}' creado."
            )
            messages.success(request, f"Período '{periodo.nombre}' creado correctamente.")
            return redirect("periodos_list")
    else:
        form = PeriodoLectivoForm()

    return render(request, "academic_core/periodo_form.html", {"form": form, "title": "Crear Nuevo Período Lectivo", "is_edit": False})


@login_required(login_url="login")
@requiere_permiso("academic.periodos_gestionar")
def periodo_edit_view(request, periodo_id):
    """
    Formulario web para editar un período lectivo existente.
    """
    periodo = get_object_or_404(PeriodoLectivo, pk=periodo_id)
    if request.method == "POST":
        form = PeriodoLectivoForm(request.POST, instance=periodo)
        if form.is_valid():
            periodo = form.save()
            registrar_evento(
                accion="EDITAR_PERIODO",
                usuario=request.user,
                objeto_tipo="PeriodoLectivo",
                objeto_id=str(periodo.id),
                descripcion=f"Período lectivo '{periodo.nombre}' actualizado."
            )
            messages.success(request, f"Período '{periodo.nombre}' actualizado con éxito.")
            return redirect("periodos_list")
    else:
        form = PeriodoLectivoForm(instance=periodo)

    return render(request, "academic_core/periodo_form.html", {"form": form, "periodo": periodo, "title": f"Editar Período: {periodo.nombre}", "is_edit": True})


# =========================================================================
# CLASES, SECCIONES Y MATERIAS
# =========================================================================

@login_required(login_url="login")
@requiere_permiso("academic.clases_ver")
def clases_list_view(request):
    """
    Jerarquía completa de Clases / Grados, Secciones y Materias asignadas.
    """
    periodo = PeriodoLectivo.objects.filter(activo=True).first() or PeriodoLectivo.objects.first()
    clases = Clase.objects.filter(periodo=periodo).prefetch_related("secciones", "materias").select_related("nivel") if periodo else []

    return render(
        request,
        "academic_core/clases_list.html",
        {
            "periodo": periodo,
            "clases": clases,
        }
    )


@login_required(login_url="login")
@requiere_permiso("academic.clases_gestionar")
def clase_create_view(request):
    """
    Formulario web para crear una nueva clase/grado escolar.
    """
    if request.method == "POST":
        form = ClaseForm(request.POST)
        if form.is_valid():
            clase = form.save()
            messages.success(request, f"Grado / Clase '{clase.nombre}' creado exitosamente.")
            return redirect("clases_list")
    else:
        form = ClaseForm()

    return render(request, "academic_core/clase_form.html", {"form": form, "title": "Crear Nuevo Grado / Clase", "is_edit": False})


@login_required(login_url="login")
@requiere_permiso("academic.clases_gestionar")
def clase_edit_view(request, clase_id):
    """
    Formulario web para editar una clase/grado escolar.
    """
    clase = get_object_or_404(Clase, pk=clase_id)
    if request.method == "POST":
        form = ClaseForm(request.POST, instance=clase)
        if form.is_valid():
            form.save()
            messages.success(request, f"Grado / Clase '{clase.nombre}' actualizado correctamente.")
            return redirect("clases_list")
    else:
        form = ClaseForm(instance=clase)

    return render(request, "academic_core/clase_form.html", {"form": form, "clase": clase, "title": f"Editar Grado: {clase.nombre}", "is_edit": True})


@login_required(login_url="login")
@requiere_permiso("academic.clases_gestionar")
def seccion_create_view(request):
    """
    Formulario web para registrar una nueva sección con cupo máximo.
    """
    if request.method == "POST":
        form = SeccionForm(request.POST)
        if form.is_valid():
            seccion = form.save()
            messages.success(request, f"Sección '{seccion.nombre}' agregada a {seccion.clase.nombre}.")
            return redirect("clases_list")
    else:
        form = SeccionForm()

    return render(request, "academic_core/seccion_form.html", {"form": form, "title": "Crear Nueva Sección", "is_edit": False})


@login_required(login_url="login")
@requiere_permiso("academic.clases_gestionar")
def seccion_edit_view(request, seccion_id):
    """
    Formulario web para editar una sección.
    """
    seccion = get_object_or_404(Seccion, pk=seccion_id)
    if request.method == "POST":
        form = SeccionForm(request.POST, instance=seccion)
        if form.is_valid():
            form.save()
            messages.success(request, f"Sección '{seccion.nombre}' actualizada.")
            return redirect("clases_list")
    else:
        form = SeccionForm(instance=seccion)

    return render(request, "academic_core/seccion_form.html", {"form": form, "seccion": seccion, "title": f"Editar Sección: {seccion.nombre}", "is_edit": True})


@login_required(login_url="login")
@requiere_permiso("academic.materias_gestionar")
def materia_detail_view(request, materia_id):
    """
    Edición de Materia con control de concurrencia mediante `lock_version`.
    """
    materia = get_object_or_404(Materia, pk=materia_id)
    docentes = User.objects.filter(is_staff=True)

    if request.method == "POST":
        lock_version_post = int(request.POST.get("lock_version", 0))
        docente_id = request.POST.get("docente_id")
        nombre = request.POST.get("nombre", "").strip()

        try:
            materia.nombre = nombre
            materia.docente_id = docente_id if docente_id else None
            materia.lock_version = lock_version_post
            materia.save()

            registrar_evento(
                accion="EDITAR_MATERIA",
                usuario=request.user,
                objeto_tipo="Materia",
                objeto_id=str(materia.id),
                descripcion=f"Materia {materia.nombre} actualizada a versión de bloqueo {materia.lock_version}"
            )
            messages.success(request, f"Materia '{materia.nombre}' actualizada exitosamente.")
            return redirect("clases_list")
        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, 'message') else e))

    return render(
        request,
        "academic_core/materia_detail.html",
        {
            "materia": materia,
            "docentes": docentes,
        }
    )


@login_required(login_url="login")
@requiere_permiso("academic.horarios_gestionar")
def horarios_list_view(request):
    """
    Programación visual de Horarios por Sección con validación de traslapes.
    """
    periodo = PeriodoLectivo.objects.filter(activo=True).first() or PeriodoLectivo.objects.first()
    secciones = Seccion.objects.filter(clase__periodo=periodo).select_related("clase") if periodo else []
    
    seccion_id = request.GET.get("seccion_id")
    seccion_seleccionada = get_object_or_404(Seccion, pk=seccion_id) if seccion_id else (secciones.first() if secciones else None)
    
    horarios = Horario.objects.filter(materia__seccion=seccion_seleccionada).select_related("materia") if seccion_seleccionada else []
    materias_seccion = Materia.objects.filter(seccion=seccion_seleccionada) if seccion_seleccionada else []

    if request.method == "POST" and "crear_horario" in request.POST:
        materia_id = request.POST.get("materia_id")
        dia_semana = int(request.POST.get("dia_semana"))
        hora_inicio = request.POST.get("hora_inicio")
        hora_fin = request.POST.get("hora_fin")
        aula = request.POST.get("aula", "").strip()

        materia = get_object_or_404(Materia, pk=materia_id)
        horario = Horario(
            materia=materia,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            aula=aula
        )
        try:
            horario.full_clean()
            horario.save()
            messages.success(request, "Horario programado exitosamente.")
            return redirect(f"/academic/horarios/?seccion_id={seccion_seleccionada.id}")
        except ValidationError as e:
            messages.error(request, f"Error en horario: {e.messages[0] if hasattr(e, 'messages') else e}")

    return render(
        request,
        "academic_core/horarios.html",
        {
            "periodo": periodo,
            "secciones": secciones,
            "seccion_seleccionada": seccion_seleccionada,
            "horarios": horarios,
            "materias_seccion": materias_seccion,
        }
    )


# =========================================================================
# ASIGNATURAS Y NIVELES EDUCATIVOS
# =========================================================================

@login_required(login_url="login")
@requiere_permiso("academic.clases_ver")
def asignaturas_list_view(request):
    """
    Catálogo general de asignaturas curriculares.
    """
    query = request.GET.get("q", "").strip()
    asignaturas = Asignatura.objects.all()
    if query:
        asignaturas = asignaturas.filter(Q(nombre__icontains=query) | Q(codigo__icontains=query))
    return render(request, "academic_core/asignaturas_list.html", {"asignaturas": asignaturas, "query": query})


@login_required(login_url="login")
@requiere_permiso("academic.clases_gestionar")
def asignatura_create_view(request):
    if request.method == "POST":
        form = AsignaturaForm(request.POST)
        if form.is_valid():
            asig = form.save()
            messages.success(request, f"Asignatura '{asig.nombre}' creada.")
            return redirect("asignaturas_list")
    else:
        form = AsignaturaForm()
    return render(request, "academic_core/asignatura_form.html", {"form": form, "title": "Crear Asignatura", "is_edit": False})


@login_required(login_url="login")
@requiere_permiso("academic.clases_gestionar")
def asignatura_edit_view(request, asignatura_id):
    asig = get_object_or_404(Asignatura, pk=asignatura_id)
    if request.method == "POST":
        form = AsignaturaForm(request.POST, instance=asig)
        if form.is_valid():
            form.save()
            messages.success(request, f"Asignatura '{asig.nombre}' actualizada.")
            return redirect("asignaturas_list")
    else:
        form = AsignaturaForm(instance=asig)
    return render(request, "academic_core/asignatura_form.html", {"form": form, "asignatura": asig, "title": f"Editar Asignatura: {asig.nombre}", "is_edit": True})


@login_required(login_url="login")
@requiere_permiso("academic.clases_ver")
def niveles_list_view(request):
    """
    Catálogo de Niveles Educativos (Preescolar, Primaria, Secundaria, etc.)
    """
    niveles = Nivel.objects.all().order_by("orden")
    return render(request, "academic_core/niveles_list.html", {"niveles": niveles})


@login_required(login_url="login")
@requiere_permiso("academic.clases_gestionar")
def nivel_create_view(request):
    if request.method == "POST":
        form = NivelForm(request.POST)
        if form.is_valid():
            nivel = form.save()
            messages.success(request, f"Nivel Educativo '{nivel.nombre}' creado.")
            return redirect("niveles_list")
    else:
        form = NivelForm()
    return render(request, "academic_core/nivel_form.html", {"form": form, "title": "Crear Nivel Educativo", "is_edit": False})


@login_required(login_url="login")
@requiere_permiso("academic.clases_gestionar")
def nivel_edit_view(request, nivel_id):
    nivel = get_object_or_404(Nivel, pk=nivel_id)
    if request.method == "POST":
        form = NivelForm(request.POST, instance=nivel)
        if form.is_valid():
            form.save()
            messages.success(request, f"Nivel Educativo '{nivel.nombre}' actualizado.")
            return redirect("niveles_list")
    else:
        form = NivelForm(instance=nivel)
    return render(request, "academic_core/nivel_form.html", {"form": form, "nivel": nivel, "title": f"Editar Nivel: {nivel.nombre}", "is_edit": True})


# =========================================================================
# TIPOS DE NOTA Y ESCALAS DE CALIFICACIÓN
# =========================================================================

@login_required(login_url="login")
@requiere_permiso("academic.periodos_gestionar")
def tipos_nota_list_view(request):
    """
    Gestión del árbol jerárquico de Tipos de Nota y evaluaciones.
    """
    periodo = PeriodoLectivo.objects.filter(activo=True).first() or PeriodoLectivo.objects.first()
    tipos_nota = TipoNota.objects.filter(periodo=periodo).order_by("orden") if periodo else []
    return render(request, "academic_core/tipos_nota_list.html", {"periodo": periodo, "tipos_nota": tipos_nota})


@login_required(login_url="login")
@requiere_permiso("academic.periodos_gestionar")
def tipo_nota_create_view(request):
    if request.method == "POST":
        form = TipoNotaForm(request.POST)
        if form.is_valid():
            tipo = form.save()
            messages.success(request, f"Tipo de Nota '{tipo.nombre}' creado.")
            return redirect("tipos_nota_list")
    else:
        form = TipoNotaForm()
    return render(request, "academic_core/tipo_nota_form.html", {"form": form, "title": "Crear Tipo de Nota", "is_edit": False})


@login_required(login_url="login")
@requiere_permiso("academic.periodos_gestionar")
def tipo_nota_edit_view(request, tipo_id):
    tipo = get_object_or_404(TipoNota, pk=tipo_id)
    if request.method == "POST":
        form = TipoNotaForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, f"Tipo de Nota '{tipo.nombre}' actualizado.")
            return redirect("tipos_nota_list")
    else:
        form = TipoNotaForm(instance=tipo)
    return render(request, "academic_core/tipo_nota_form.html", {"form": form, "tipo": tipo, "title": f"Editar Tipo de Nota: {tipo.nombre}", "is_edit": True})


@login_required(login_url="login")
@requiere_permiso("academic.periodos_gestionar")
def escalas_list_view(request):
    """
    Gestión de Escalas de Calificación cuantitativas y cualitativas.
    """
    escalas = Escala.objects.all()
    return render(request, "academic_core/escalas_list.html", {"escalas": escalas})


@login_required(login_url="login")
@requiere_permiso("academic.periodos_gestionar")
def escala_create_view(request):
    if request.method == "POST":
        form = EscalaForm(request.POST)
        if form.is_valid():
            escala = form.save()
            messages.success(request, f"Escala '{escala.nombre}' creada.")
            return redirect("escalas_list")
    else:
        form = EscalaForm()
    return render(request, "academic_core/escala_form.html", {"form": form, "title": "Crear Escala de Calificación", "is_edit": False})


@login_required(login_url="login")
@requiere_permiso("academic.periodos_gestionar")
def escala_edit_view(request, escala_id):
    escala = get_object_or_404(Escala, pk=escala_id)
    if request.method == "POST":
        form = EscalaForm(request.POST, instance=escala)
        if form.is_valid():
            form.save()
            messages.success(request, f"Escala '{escala.nombre}' actualizada.")
            return redirect("escalas_list")
    else:
        form = EscalaForm(instance=escala)
    return render(request, "academic_core/escala_form.html", {"form": form, "escala": escala, "title": f"Editar Escala: {escala.nombre}", "is_edit": True})


# =========================================================================
# PANEL CENTRAL DE CATÁLOGOS AUXILIARES
# =========================================================================

@login_required(login_url="login")
@requiere_permiso("academic.clases_ver")
def catalogos_panel_view(request):
    """
    Panel centralizado para consulta de catálogos generales:
    Estados Civiles, Religiones, Escolaridades y Rutas de Transporte.
    """
    estados_civiles = EstadoCivil.objects.all()
    religiones = Religion.objects.all()
    escolaridades = Escolaridad.objects.all()
    recorridos = Recorrido.objects.all()

    return render(
        request,
        "academic_core/catalogos_panel.html",
        {
            "estados_civiles": estados_civiles,
            "religiones": religiones,
            "escolaridades": escolaridades,
            "recorridos": recorridos,
        }
    )
