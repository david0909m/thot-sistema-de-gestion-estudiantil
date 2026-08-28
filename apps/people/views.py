from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import Docente, Pariente, Estudiante, EstudianteClase, Responsable, Estudio, Experiencia, FichaMedica
from .forms import (
    DocenteForm, ParienteForm, EstudianteForm, ResponsableForm,
    MatriculaEstudianteForm, EstudioDocenteForm, ExperienciaDocenteForm, FichaMedicaForm
)
from apps.academic_core.models import Seccion, Materia, Horario, PeriodoLectivo
from apps.people.services import trasladar_estudiante, retirar_estudiante, procesar_variantes_imagen
from apps.support.models import Incidencia
from apps.grading.models import ResumenAcademicoEstudiante
from apps.audit.services import registrar_evento
from apps.accounts.decorators import requiere_permiso
from apps.accounts.services_permissions import (
    puede, estudiantes_visibles, _docente_de
)

User = get_user_model()


def _get_estudiante_obj(request, estudiante_id):
    return get_object_or_404(Estudiante, pk=estudiante_id)


def _get_docente_obj(request, docente_id):
    return get_object_or_404(Docente, pk=docente_id)


# =========================================================================
# GESTIÓN DE ESTUDIANTES
# =========================================================================

@login_required(login_url="login")
@requiere_permiso("people.estudiantes_ver")
def estudiantes_list_view(request):
    """
    Listado interactivo de estudiantes con buscador HTMX y filtros.
    """
    query = request.GET.get("q", "").strip()
    estudiantes = estudiantes_visibles(request.user)

    if query:
        estudiantes = estudiantes.filter(
            Q(codigo_estudiante__icontains=query) |
            Q(primer_nombre__icontains=query) |
            Q(primer_apellido__icontains=query) |
            Q(cedula_identidad__icontains=query)
        )

    estudiantes = estudiantes.order_by("primer_apellido", "primer_nombre")[:100]
    return render(request, "people/estudiantes_list.html", {"estudiantes": estudiantes, "query": query})


@login_required(login_url="login")
@requiere_permiso("people.estudiantes_gestionar")
def estudiante_create_view(request):
    """
    Formulario web para dar de alta a un nuevo estudiante.
    """
    if request.method == "POST":
        form = EstudianteForm(request.POST, request.FILES)
        if form.is_valid():
            estudiante = form.save(commit=False)
            if "foto" in request.FILES:
                variantes = procesar_variantes_imagen(request.FILES["foto"])
                if variantes:
                    estudiante.foto.save(variantes["original"].name, variantes["original"], save=False)
                    estudiante.foto_normal.save(variantes["normal"].name, variantes["normal"], save=False)
                    estudiante.foto_thumb.save(variantes["thumb"].name, variantes["thumb"], save=False)
            estudiante.save()

            messages.success(request, f"Estudiante {estudiante.get_full_name()} creado con éxito.")
            return redirect("estudiante_detail", estudiante_id=estudiante.id)
    else:
        form = EstudianteForm()

    return render(request, "people/estudiante_form.html", {"form": form, "title": "Registrar Nuevo Estudiante", "is_edit": False})


@login_required(login_url="login")
@requiere_permiso("people.estudiantes_gestionar", get_objeto_func=_get_estudiante_obj)
def estudiante_edit_view(request, estudiante_id):
    """
    Formulario web para editar los datos de un estudiante existente.
    """
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    if request.method == "POST":
        form = EstudianteForm(request.POST, request.FILES, instance=estudiante)
        if form.is_valid():
            estudiante = form.save(commit=False)
            if "foto" in request.FILES:
                variantes = procesar_variantes_imagen(request.FILES["foto"])
                if variantes:
                    estudiante.foto.save(variantes["original"].name, variantes["original"], save=False)
                    estudiante.foto_normal.save(variantes["normal"].name, variantes["normal"], save=False)
                    estudiante.foto_thumb.save(variantes["thumb"].name, variantes["thumb"], save=False)
            estudiante.save()

            messages.success(request, f"Datos de {estudiante.get_full_name()} actualizados correctamente.")
            return redirect("estudiante_detail", estudiante_id=estudiante.id)
    else:
        form = EstudianteForm(instance=estudiante)

    return render(request, "people/estudiante_form.html", {"form": form, "estudiante": estudiante, "title": f"Editar Estudiante: {estudiante.get_full_name()}", "is_edit": True})


@login_required(login_url="login")
@requiere_permiso("people.estudiantes_ver", get_objeto_func=_get_estudiante_obj)
def estudiante_detail_view(request, estudiante_id):
    """
    Expediente 360° del estudiante con variantes Pillow de foto, traslados y retiros.
    """
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)

    if request.method == "POST":
        # Las acciones de escritura exigen atribución de gestión sobre el expediente,
        # no basta el permiso de lectura con el que se consulta el detalle.
        if not puede(request.user, "people.estudiantes_gestionar", objeto=estudiante):
            messages.error(request, "Acceso denegado: no cuenta con atribuciones para modificar este expediente.")
            return redirect("estudiante_detail", estudiante_id=estudiante.id)

        # 1. Carga de Fotografía
        if "nueva_foto" in request.FILES:
            foto_file = request.FILES["nueva_foto"]
            variantes = procesar_variantes_imagen(foto_file)
            if variantes:
                estudiante.foto.save(variantes["original"].name, variantes["original"], save=False)
                estudiante.foto_normal.save(variantes["normal"].name, variantes["normal"], save=False)
                estudiante.foto_thumb.save(variantes["thumb"].name, variantes["thumb"], save=True)

                registrar_evento(
                    accion="ACTUALIZAR_FOTO_ESTUDIANTE",
                    usuario=request.user,
                    objeto_tipo="Estudiante",
                    objeto_id=str(estudiante.id),
                    descripcion=f"Fotografía y variantes actualizadas para {estudiante.codigo_estudiante}"
                )
                messages.success(request, "Fotografía y miniaturas procesadas exitosamente con Pillow.")
                return redirect("estudiante_detail", estudiante_id=estudiante.id)

        # 2. Traslado de Sección
        elif "nueva_seccion_id" in request.POST:
            nueva_seccion_id = request.POST.get("nueva_seccion_id")
            matricula_id = request.POST.get("matricula_id")
            
            matricula = get_object_or_404(EstudianteClase, pk=matricula_id, estudiante=estudiante)
            nueva_seccion = get_object_or_404(Seccion, pk=nueva_seccion_id)

            trasladar_estudiante(matricula, nueva_seccion, usuario=request.user)
            messages.success(request, f"Estudiante trasladado exitosamente a {nueva_seccion.clase.nombre} ({nueva_seccion.nombre}).")
            return redirect("estudiante_detail", estudiante_id=estudiante.id)

        # 3. Retiro del Estudiante
        elif "motivo_retiro" in request.POST:
            matricula_id = request.POST.get("matricula_id")
            motivo = request.POST.get("motivo_retiro", "").strip()
            
            matricula = get_object_or_404(EstudianteClase, pk=matricula_id, estudiante=estudiante)
            retirar_estudiante(matricula, motivo, usuario=request.user)
            messages.warning(request, f"Estudiante {estudiante.get_full_name()} marcado como RETIRADO.")
            return redirect("estudiante_detail", estudiante_id=estudiante.id)

    responsables = Responsable.objects.filter(estudiante=estudiante).select_related("pariente")
    matriculas = EstudianteClase.objects.filter(estudiante=estudiante).select_related("clase", "seccion", "periodo")
    incidencias = Incidencia.objects.filter(estudiante=estudiante).order_by("-fecha")
    ficha_medica = FichaMedica.objects.filter(estudiante=estudiante).first()
    resumenes = ResumenAcademicoEstudiante.objects.filter(estudiante=estudiante).select_related("periodo")
    secciones_disponibles = Seccion.objects.all()

    return render(
        request,
        "people/estudiante_detail.html",
        {
            "estudiante": estudiante,
            "responsables": responsables,
            "matriculas": matriculas,
            "incidencias": incidencias,
            "ficha_medica": ficha_medica,
            "resumenes": resumenes,
            "secciones_disponibles": secciones_disponibles,
        }
    )


# =========================================================================
# ASISTENTE DE MATRÍCULA E INSCRIPCIÓN
# =========================================================================

@login_required(login_url="login")
@requiere_permiso("people.estudiantes_gestionar")
def matricular_estudiante_view(request, estudiante_id=None):
    """
    Asistente web de matrícula e inscripción en un período, clase y sección.
    """
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id) if estudiante_id else None

    if request.method == "POST":
        form = MatriculaEstudianteForm(request.POST)
        selected_estudiante_id = request.POST.get("estudiante_id") or (estudiante.id if estudiante else None)
        selected_estudiante = get_object_or_404(Estudiante, pk=selected_estudiante_id)

        if form.is_valid():
            matricula = form.save(commit=False)
            matricula.estudiante = selected_estudiante
            matricula.save()

            registrar_evento(
                accion="MATRICULAR_ESTUDIANTE",
                usuario=request.user,
                objeto_tipo="EstudianteClase",
                objeto_id=str(matricula.id),
                descripcion=f"Estudiante {selected_estudiante.codigo_estudiante} matriculado en {matricula.seccion} ({matricula.periodo.nombre})."
            )
            messages.success(request, f"Estudiante {selected_estudiante.get_full_name()} matriculado exitosamente en {matricula.seccion}.")
            return redirect("estudiante_detail", estudiante_id=selected_estudiante.id)
    else:
        form = MatriculaEstudianteForm()

    estudiantes = Estudiante.objects.filter(activo=True) if not estudiante else [estudiante]
    return render(
        request,
        "people/matricular_form.html",
        {
            "form": form,
            "estudiante": estudiante,
            "estudiantes": estudiantes,
            "title": f"Matricular Estudiante: {estudiante.get_full_name()}" if estudiante else "Matricular Estudiante"
        }
    )


# =========================================================================
# GESTIÓN DE FAMILIARES / PARIENTES Y RESPONSABLES
# =========================================================================

@login_required(login_url="login")
@requiere_permiso("people.parientes_ver")
def parientes_list_view(request):
    """
    Directorio de parientes y tutores con buscador HTMX.
    """
    query = request.GET.get("q", "").strip()
    parientes = Pariente.objects.all().prefetch_related("estudiantes_a_cargo__estudiante")

    if query:
        parientes = parientes.filter(
            Q(primer_nombre__icontains=query) |
            Q(primer_apellido__icontains=query) |
            Q(cedula_identidad__icontains=query) |
            Q(telefono__icontains=query) |
            Q(email__icontains=query)
        )

    parientes = parientes.order_by("primer_apellido", "primer_nombre")[:100]
    return render(request, "people/parientes_list.html", {"parientes": parientes, "query": query})


@login_required(login_url="login")
@requiere_permiso("people.parientes_gestionar")
def pariente_create_view(request):
    """
    Formulario web para crear un nuevo pariente o tutor legal.
    """
    if request.method == "POST":
        form = ParienteForm(request.POST)
        if form.is_valid():
            pariente = form.save()
            registrar_evento(
                accion="CREAR_PARIENTE",
                usuario=request.user,
                objeto_tipo="Pariente",
                objeto_id=str(pariente.id),
                descripcion=f"Pariente {pariente.get_full_name()} registrado exitosamente."
            )
            messages.success(request, f"Familiar {pariente.get_full_name()} registrado correctamente.")
            return redirect("parientes_list")
    else:
        form = ParienteForm()

    return render(request, "people/pariente_form.html", {"form": form, "title": "Registrar Nuevo Familiar / Tutor", "is_edit": False})


@login_required(login_url="login")
@requiere_permiso("people.parientes_gestionar")
def pariente_edit_view(request, pariente_id):
    """
    Formulario web para editar los datos de un pariente existente.
    """
    pariente = get_object_or_404(Pariente, pk=pariente_id)
    if request.method == "POST":
        form = ParienteForm(request.POST, instance=pariente)
        if form.is_valid():
            pariente = form.save()
            registrar_evento(
                accion="EDITAR_PARIENTE",
                usuario=request.user,
                objeto_tipo="Pariente",
                objeto_id=str(pariente.id),
                descripcion=f"Datos de pariente {pariente.get_full_name()} actualizados."
            )
            messages.success(request, f"Familiar {pariente.get_full_name()} actualizado con éxito.")
            return redirect("parientes_list")
    else:
        form = ParienteForm(instance=pariente)

    return render(request, "people/pariente_form.html", {"form": form, "pariente": pariente, "title": f"Editar Familiar: {pariente.get_full_name()}", "is_edit": True})


@login_required(login_url="login")
@requiere_permiso("people.parientes_gestionar")
def asignar_responsable_view(request, estudiante_id):
    """
    Vincula un pariente existente como responsable legal o financiero de un estudiante.
    """
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    if request.method == "POST":
        form = ResponsableForm(request.POST)
        if form.is_valid():
            responsable = form.save(commit=False)
            responsable.estudiante = estudiante
            responsable.save()

            registrar_evento(
                accion="ASIGNAR_RESPONSABLE",
                usuario=request.user,
                objeto_tipo="Responsable",
                objeto_id=str(responsable.id),
                descripcion=f"Pariente {responsable.pariente.get_full_name()} asignado a {estudiante.codigo_estudiante}."
            )
            messages.success(request, f"{responsable.pariente.get_full_name()} vinculado como tutor de {estudiante.get_full_name()}.")
            return redirect("estudiante_detail", estudiante_id=estudiante.id)
    else:
        form = ResponsableForm()

    parientes = Pariente.objects.all().order_by("primer_apellido")
    return render(request, "people/asignar_responsable_modal.html", {"form": form, "estudiante": estudiante, "parientes": parientes})


# =========================================================================
# GESTIÓN DE DOCENTES / PROFESORES
# =========================================================================

@login_required(login_url="login")
@requiere_permiso("people.docentes_ver")
def docentes_list_view(request):
    """
    Directorio de la planta docente con buscador HTMX y métricas.
    """
    query = request.GET.get("q", "").strip()
    docentes = Docente.objects.all().select_related("usuario")

    # Ámbito: los usuarios con identidad docente sólo alcanzan su propio expediente;
    # el alcance institucional consulta la planta completa.
    if not request.user.is_superuser:
        docente_propio = _docente_de(request.user)
        if docente_propio:
            docentes = Docente.objects.filter(pk=docente_propio.pk)

    if query:
        docentes = docentes.filter(
            Q(codigo_empleado__icontains=query) |
            Q(usuario__first_name__icontains=query) |
            Q(usuario__last_name__icontains=query) |
            Q(especialidad__icontains=query) |
            Q(telefono__icontains=query)
        )

    docentes = docentes.order_by("usuario__last_name", "usuario__first_name")[:100]
    return render(request, "people/docentes_list.html", {"docentes": docentes, "query": query})


@login_required(login_url="login")
@requiere_permiso("people.docentes_ver", get_objeto_func=_get_docente_obj)
def docente_detail_view(request, docente_id):
    """
    Expediente integral del profesor: datos personales, materias asignadas, carga horaria, títulos y experiencias.
    """
    docente = get_object_or_404(Docente.objects.select_related("usuario"), pk=docente_id)
    materias_titular = Materia.objects.filter(docente=docente.usuario).select_related("clase", "seccion", "asignatura")
    horarios = Horario.objects.filter(materia__docente=docente.usuario).select_related("materia", "materia__seccion").order_by("dia_semana", "hora_inicio")
    estudios = Estudio.objects.filter(usuario=docente.usuario).order_by("-fecha_obtencion")
    experiencias = Experiencia.objects.filter(usuario=docente.usuario).order_by("-fecha_inicio")

    form_estudio = EstudioDocenteForm()
    form_experiencia = ExperienciaDocenteForm()

    return render(
        request,
        "people/docente_detail.html",
        {
            "docente": docente,
            "materias_titular": materias_titular,
            "horarios": horarios,
            "estudios": estudios,
            "experiencias": experiencias,
            "form_estudio": form_estudio,
            "form_experiencia": form_experiencia,
        }
    )


@login_required(login_url="login")
@requiere_permiso("people.docentes_gestionar")
def docente_create_view(request):
    """
    Formulario de alta de docente con creación automática o vinculación de usuario.
    """
    if request.method == "POST":
        form = DocenteForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            first_name = form.cleaned_data.get("first_name")
            last_name = form.cleaned_data.get("last_name")
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")

            # Crear o vincular usuario
            if username:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={"first_name": first_name, "last_name": last_name, "email": email}
                )
                if created and password:
                    user.set_password(password)
                    user.save()
            else:
                user = User.objects.create_user(
                    username=f"doc_{form.cleaned_data['codigo_empleado'].lower()}",
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password=password or "Temporal2026!"
                )

            docente = form.save(commit=False)
            docente.usuario = user
            docente.save()

            registrar_evento(
                accion="CREAR_DOCENTE",
                usuario=request.user,
                objeto_tipo="Docente",
                objeto_id=str(docente.id),
                descripcion=f"Docente {docente.codigo_empleado} - {docente.usuario.get_full_name()} registrado exitosamente."
            )
            messages.success(request, f"Docente {docente.usuario.get_full_name()} registrado correctamente.")
            return redirect("docente_detail", docente_id=docente.id)
    else:
        form = DocenteForm()

    return render(request, "people/docente_form.html", {"form": form, "title": "Registrar Nuevo Docente", "is_edit": False})


@login_required(login_url="login")
@requiere_permiso("people.docentes_gestionar", get_objeto_func=_get_docente_obj)
def docente_edit_view(request, docente_id):
    """
    Formulario de edición de expediente de docente.
    """
    docente = get_object_or_404(Docente.objects.select_related("usuario"), pk=docente_id)
    if request.method == "POST":
        form = DocenteForm(request.POST, request.FILES, instance=docente)
        if form.is_valid():
            docente = form.save()
            if docente.usuario:
                docente.usuario.first_name = form.cleaned_data.get("first_name", docente.usuario.first_name)
                docente.usuario.last_name = form.cleaned_data.get("last_name", docente.usuario.last_name)
                docente.usuario.email = form.cleaned_data.get("email", docente.usuario.email)
                password = form.cleaned_data.get("password")
                if password:
                    docente.usuario.set_password(password)
                docente.usuario.save()

            registrar_evento(
                accion="EDITAR_DOCENTE",
                usuario=request.user,
                objeto_tipo="Docente",
                objeto_id=str(docente.id),
                descripcion=f"Expediente del docente {docente.codigo_empleado} actualizado."
            )
            messages.success(request, f"Expediente de {docente.usuario.get_full_name()} actualizado con éxito.")
            return redirect("docente_detail", docente_id=docente.id)
    else:
        form = DocenteForm(instance=docente)

    return render(request, "people/docente_form.html", {"form": form, "docente": docente, "title": f"Editar Docente: {docente.usuario.get_full_name()}", "is_edit": True})


@login_required(login_url="login")
@requiere_permiso("people.docentes_gestionar", get_objeto_func=_get_docente_obj)
def docente_estudio_add_view(request, docente_id):
    """
    Agrega un título o grado académico al expediente del docente.
    """
    docente = get_object_or_404(Docente, pk=docente_id)
    if request.method == "POST":
        form = EstudioDocenteForm(request.POST)
        if form.is_valid():
            estudio = form.save(commit=False)
            estudio.usuario = docente.usuario
            estudio.save()
            messages.success(request, f"Título '{estudio.titulo}' agregado al expediente.")
    return redirect("docente_detail", docente_id=docente.id)


@login_required(login_url="login")
@requiere_permiso("people.docentes_gestionar", get_objeto_func=_get_docente_obj)
def docente_experiencia_add_view(request, docente_id):
    """
    Agrega una experiencia laboral previa al expediente del docente.
    """
    docente = get_object_or_404(Docente, pk=docente_id)
    if request.method == "POST":
        form = ExperienciaDocenteForm(request.POST)
        if form.is_valid():
            experiencia = form.save(commit=False)
            experiencia.usuario = docente.usuario
            experiencia.save()
            messages.success(request, f"Experiencia '{experiencia.cargo}' agregada al expediente.")
    return redirect("docente_detail", docente_id=docente.id)


@login_required(login_url="login")
@requiere_permiso("people.estudiantes_ver", get_objeto_func=_get_estudiante_obj)
def ficha_medica_view(request, estudiante_id):
    """
    Expediente clínico y ficha médica integral del estudiante.
    """
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    ficha, _ = FichaMedica.objects.get_or_create(estudiante=estudiante)

    if request.method == "POST":
        if not puede(request.user, "people.estudiantes_gestionar", objeto=estudiante):
            messages.error(request, "Acceso denegado: no cuenta con atribuciones para modificar la ficha médica.")
            return redirect("ficha_medica", estudiante_id=estudiante.id)
        form = FichaMedicaForm(request.POST, instance=ficha)
        if form.is_valid():
            form.save()
            registrar_evento(
                accion="ACTUALIZAR_FICHA_MEDICA",
                usuario=request.user,
                objeto_tipo="FichaMedica",
                objeto_id=str(ficha.id),
                descripcion=f"Ficha médica actualizada para {estudiante.get_full_name()}"
            )
            messages.success(request, "Ficha médica y de salud guardada exitosamente.")
            return redirect("ficha_medica", estudiante_id=estudiante.id)
    else:
        form = FichaMedicaForm(instance=ficha)

    return render(
        request,
        "people/ficha_medica.html",
        {
            "estudiante": estudiante,
            "ficha": ficha,
            "form": form,
        }
    )

