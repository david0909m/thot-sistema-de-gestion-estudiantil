from django.contrib.contenttypes.models import ContentType
from apps.accounts.models import AsignacionUsuario, Autorizacion


def asignaciones_activas(usuario):
    return AsignacionUsuario.objects.filter(usuario=usuario, activo=True)


def _perfiles_ids(usuario):
    return list(
        asignaciones_activas(usuario).values_list("perfil_id", flat=True)
    )


def tiene_permiso_de_perfil(usuario, codigo_permiso) -> bool:
    perfiles = _perfiles_ids(usuario)
    if not perfiles:
        return False
    return Autorizacion.objects.filter(
        perfil_id__in=perfiles,
        permiso__codigo=codigo_permiso
    ).exists()


def es_usuario_global(usuario) -> bool:
    """
    Un usuario tiene alcance institucional cuando carece de identidad
    docente, pariente o estudiante y sus asignaciones activas son globales.
    La identidad acota el ámbito aunque el perfil se asigne sin objeto.
    """
    if usuario.is_superuser:
        return True
    if _docente_de(usuario) is not None:
        return False
    if _pariente_de(usuario) is not None:
        return False
    from apps.people.models import Estudiante
    if Estudiante.objects.filter(codigo_estudiante=usuario.username).exists():
        return False
    return not asignaciones_activas(usuario).exclude(
        content_type__isnull=True, object_id__isnull=True
    ).exists()


def _docente_de(usuario):
    docente = getattr(usuario, "perfil_docente", None)
    if docente is not None:
        return docente
    from apps.people.models import Docente
    return Docente.objects.filter(usuario=usuario).first()


def _pariente_de(usuario):
    pariente = getattr(usuario, "perfil_pariente", None)
    if pariente is not None:
        return pariente
    from apps.people.models import Pariente
    return Pariente.objects.filter(usuario=usuario).first()


def _secciones_del_docente(docente):
    """
    Secciones donde el docente es guía o imparte alguna materia.
    """
    from django.db.models import Q
    from apps.academic_core.models import Seccion, Materia
    return Seccion.objects.filter(
        Q(docente=docente.usuario) |
        Q(pk__in=Materia.objects.filter(
            asignaciones_docentes__docente=docente.usuario
        ).values_list("seccion_id", flat=True))
    ).distinct()


def puede(usuario, codigo_permiso: str, objeto=None) -> bool:
    """
    Evaluador central de permisos contextuales por objeto y ámbito.

    Política: denegar por defecto. Sólo el superusuario omite las reglas;
    `is_staff` no concede capacidades por sí mismo. Todo tipo de objeto no
    contemplado explícitamente se deniega.
    """
    if not usuario or not usuario.is_authenticated or not usuario.habilitado:
        return False

    if usuario.is_superuser:
        return True

    if not tiene_permiso_de_perfil(usuario, codigo_permiso):
        return False

    if objeto is None:
        return True

    from apps.academic_core.models import Materia, Seccion
    from apps.people.models import Estudiante, Docente
    from apps.support.models import Mensaje

    if isinstance(objeto, Mensaje):
        return puede_leer_mensaje(usuario, objeto)

    if isinstance(objeto, Materia):
        return _puede_sobre_materia(usuario, objeto)

    if isinstance(objeto, Estudiante):
        return _puede_sobre_estudiante(usuario, objeto)

    if isinstance(objeto, Seccion):
        return _puede_sobre_seccion(usuario, objeto)

    if isinstance(objeto, Docente):
        return _puede_sobre_docente(usuario, objeto)

    return False


def _asignacion_contextual_permite(usuario, objeto) -> bool:
    ct = ContentType.objects.get_for_model(type(objeto))
    return asignaciones_activas(usuario).filter(
        content_type=ct, object_id=objeto.id
    ).exists()


def _puede_sobre_materia(usuario, materia) -> bool:
    if materia.docente_id == usuario.id:
        return True

    docente = _docente_de(usuario)
    if docente:
        # Guía de la sección a la que pertenece la materia
        seccion = getattr(materia, "seccion", None)
        if seccion and seccion.docente_id == docente.usuario_id:
            return True
        # Docente auxiliar/asignado mediante DocenteMateria
        if materia.asignaciones_docentes.filter(docente_id=docente.usuario_id).exists():
            return True

    return _asignacion_contextual_permite(usuario, materia)


def _puede_sobre_seccion(usuario, seccion) -> bool:
    docente = _docente_de(usuario)
    if docente and seccion.docente_id == docente.usuario_id:
        return True
    return _asignacion_contextual_permite(usuario, seccion)


def _puede_sobre_docente(usuario, docente_obj) -> bool:
    propio = docente_obj.usuario_id == usuario.id
    if propio:
        return True
    # Usuarios de alcance institucional gestionan toda la planta docente;
    # los usuarios con ámbito contextual limitado sólo llegan a lo suyo.
    if es_usuario_global(usuario):
        return True
    return _asignacion_contextual_permite(usuario, docente_obj)


def _puede_sobre_estudiante(usuario, estudiante) -> bool:
    if getattr(estudiante, "usuario_id", None) == usuario.id:
        return True
    if estudiante.codigo_estudiante == usuario.username:
        return True

    pariente = _pariente_de(usuario)
    if pariente:
        from apps.people.models import Responsable
        if Responsable.objects.filter(pariente=pariente, estudiante=estudiante).exists():
            return True

    docente = _docente_de(usuario)
    if docente and estudiante_en_secciones_del_docente(estudiante, docente):
        return True

    return _asignacion_contextual_permite(usuario, estudiante)


def estudiante_en_secciones_del_docente(estudiante, docente) -> bool:
    from apps.people.models import EstudianteClase
    return EstudianteClase.objects.filter(
        estudiante=estudiante,
        seccion_id__in=_secciones_del_docente(docente).values_list("id", flat=True)
    ).exists()


def estudiantes_visibles(usuario):
    """
    QuerySet de estudiantes alcanzables por el usuario según su ámbito.
    Superusuarios y usuarios de alcance institucional ven todo; docentes,
    parientes y estudiantes quedan limitados a su ámbito.
    """
    from apps.people.models import Estudiante

    if not usuario or not usuario.is_authenticated or not usuario.habilitado:
        return Estudiante.objects.none()

    if usuario.is_superuser or es_usuario_global(usuario):
        return Estudiante.objects.all()

    from django.db.models import Q
    filtro = Q(pk__in=Estudiante.objects.none().values_list("pk", flat=True))

    pariente = _pariente_de(usuario)
    if pariente:
        filtro |= Q(responsables__pariente=pariente)

    docente = _docente_de(usuario)
    if docente:
        secciones_ids = _secciones_del_docente(docente).values_list("id", flat=True)
        filtro |= Q(inscripciones__seccion_id__in=secciones_ids)

    filtro |= Q(codigo_estudiante=usuario.username)

    ct_estudiante = ContentType.objects.get_for_model(Estudiante)
    ids_contextuales = asignaciones_activas(usuario).filter(
        content_type=ct_estudiante
    ).values_list("object_id", flat=True)
    filtro |= Q(id__in=ids_contextuales)

    return Estudiante.objects.filter(filtro).distinct()


def materias_visibles(usuario, queryset=None):
    """
    Filtra un queryset de materias al alcance del usuario. Para superusuarios
    y usuarios globales no altera el queryset recibido.
    """
    from apps.academic_core.models import Materia

    queryset = queryset if queryset is not None else Materia.objects.all()

    if not usuario or not usuario.is_authenticated or not usuario.habilitado:
        return queryset.none()

    if usuario.is_superuser or es_usuario_global(usuario):
        return queryset

    docente = _docente_de(usuario)
    if not docente:
        return queryset.none()

    from django.db.models import Q
    filtro = (
        Q(docente=docente.usuario) |
        Q(asignaciones_docentes__docente=docente.usuario) |
        Q(seccion__docente=docente.usuario)
    )
    return queryset.filter(filtro).distinct()


def secciones_visibles(usuario, queryset=None):
    """
    Filtra un queryset de secciones al alcance del usuario: guía o docente
    de alguna materia impartida en ella. Usuarios globales no ven alterado
    el queryset; el resto queda acotado a su ámbito.
    """
    from apps.academic_core.models import Seccion

    queryset = queryset if queryset is not None else Seccion.objects.all()

    if not usuario or not usuario.is_authenticated or not usuario.habilitado:
        return queryset.none()

    if usuario.is_superuser or es_usuario_global(usuario):
        return queryset

    docente = _docente_de(usuario)
    if not docente:
        return queryset.none()

    return queryset.filter(pk__in=_secciones_del_docente(docente).values_list("pk", flat=True))


def puede_leer_mensaje(usuario, mensaje) -> bool:
    """
    Regla de privacidad de mensajería: remitente, destinatario directo o
    audiencia global. Traduce la regla genérica de mensajes en Ability.rb.
    """
    if not usuario or not usuario.is_authenticated or not usuario.habilitado:
        return False
    if usuario.is_superuser:
        return True

    if mensaje.remitente_id == usuario.id:
        return True

    if mensaje.ambito_destinatario == "GLOBAL":
        return True

    from apps.support.models import MensajeUsuario
    if MensajeUsuario.objects.filter(mensaje=mensaje, usuario=usuario).exists():
        return True

    if mensaje.ambito_destinatario == "USUARIO":
        from django.contrib.auth import get_user_model
        ct_user = ContentType.objects.get_for_model(get_user_model())
        if mensaje.content_type_id == ct_user.id and mensaje.object_id == usuario.id:
            return True

    return False
