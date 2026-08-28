from django.test import TestCase
from datetime import date
from apps.accounts.models import User, Perfil, Permiso, Autorizacion, AsignacionUsuario
from apps.accounts.services_permissions import (
    puede,
    puede_leer_mensaje,
    estudiantes_visibles,
    materias_visibles,
    secciones_visibles,
)
from apps.academic_core.models import PeriodoLectivo, Nivel, Asignatura, Clase, Seccion, Materia, DocenteMateria
from apps.people.models import (
    Docente, Estudiante, Pariente, Responsable, EstudianteClase
)
from apps.support.models import Mensaje


class PermissionsPolicyTests(TestCase):
    def setUp(self):
        # Superusuario
        self.admin_user = User.objects.create_user(username="superadmin", password="password", is_superuser=True)
        
        # Usuarios estándar
        self.user_sin_permiso = User.objects.create_user(username="user_normal", password="password")
        self.docente_user = User.objects.create_user(
            username="profesor_juan", password="password", first_name="Juan", last_name="Pérez"
        )

        # Perfil y Permisos
        self.perfil_docente = Perfil.objects.create(nombre="Docente", codigo="DOCENTE")
        self.permiso_evaluar = Permiso.objects.create(
            nombre="Evaluar Materia", codigo="grading.evaluar", modulo="grading"
        )
        Autorizacion.objects.create(perfil=self.perfil_docente, permiso=self.permiso_evaluar)

        # Asignación global de perfil al docente
        AsignacionUsuario.objects.create(usuario=self.docente_user, perfil=self.perfil_docente)

        # Entidades académicas
        self.periodo = PeriodoLectivo.objects.create(
            nombre="2026", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 11, 30)
        )
        self.nivel = Nivel.objects.create(nombre="Secundaria")
        self.asignatura = Asignatura.objects.create(nombre="Matemáticas", codigo="MAT101")
        self.clase = Clase.objects.create(periodo=self.periodo, nivel=self.nivel, nombre="7mo Grado")
        self.seccion_a = Seccion.objects.create(clase=self.clase, codigo="SEC-A", nombre="A")
        self.seccion_b = Seccion.objects.create(clase=self.clase, codigo="SEC-B", nombre="B")

        self.docente = Docente.objects.create(
            usuario=self.docente_user, codigo_empleado="DOC-01"
        )

        self.materia_asignada = Materia.objects.create(
            clase=self.clase, seccion=self.seccion_a, asignatura=self.asignatura, docente=self.docente_user
        )
        self.materia_ajena = Materia.objects.create(
            clase=self.clase, seccion=self.seccion_b, asignatura=self.asignatura
        )

    def test_superuser_has_all_permissions(self):
        self.assertTrue(puede(self.admin_user, "grading.evaluar", self.materia_ajena))

    def test_user_without_permissions_is_denied(self):
        self.assertFalse(puede(self.user_sin_permiso, "grading.evaluar", self.materia_asignada))

    def test_docente_can_evaluar_own_materia(self):
        self.assertTrue(puede(self.docente_user, "grading.evaluar", self.materia_asignada))

    def test_docente_cannot_evaluar_other_materia(self):
        self.assertFalse(puede(self.docente_user, "grading.evaluar", self.materia_ajena))


class PermissionsScopeMatrixTests(TestCase):
    """
    Matriz positiva/negativa de la política denegar-por-defecto y ámbitos.
    """

    def setUp(self):
        from django.test import Client

        self.client = Client()

        self.admin = User.objects.create_user(username="root", password="password", is_superuser=True)

        # Staff sin perfil asignado: NO obtiene capacidades por ser staff.
        self.staff_sin_perfil = User.objects.create_user(username="staffx", password="password", is_staff=True)

        # Docente con perfil y permisos
        self.docente_user = User.objects.create_user(username="profe", password="password", first_name="Ana")
        self.perfil_docente = Perfil.objects.create(nombre="Docente Mtx", codigo="DOC_MTX")
        for codigo in ("grading.evaluar", "people.estudiantes_ver", "people.estudiantes_gestionar"):
            permiso, _ = Permiso.objects.get_or_create(
                codigo=codigo,
                defaults={"nombre": codigo, "modulo": codigo.split(".")[0]},
            )
            Autorizacion.objects.create(perfil=self.perfil_docente, permiso=permiso)
        AsignacionUsuario.objects.create(usuario=self.docente_user, perfil=self.perfil_docente)
        self.docente = Docente.objects.create(usuario=self.docente_user, codigo_empleado="DOC-MTX")

        # Pariente con perfil de sólo lectura
        self.pariente_user = User.objects.create_user(username="mama_lucia", password="password")
        self.perfil_lector = Perfil.objects.create(nombre="Lector", codigo="LECTOR")
        permiso_ver, _ = Permiso.objects.get_or_create(
            codigo="people.estudiantes_ver",
            defaults={"nombre": "people.estudiantes_ver", "modulo": "people"},
        )
        Autorizacion.objects.create(perfil=self.perfil_lector, permiso=permiso_ver)
        AsignacionUsuario.objects.create(usuario=self.pariente_user, perfil=self.perfil_lector)
        self.pariente = Pariente.objects.create(
            usuario=self.pariente_user,
            primer_nombre="Lucía",
            primer_apellido="Gómez",
            parentesco="MADRE",
            cedula_identidad="1712345678",
        )

        # Estructura académica
        self.periodo = PeriodoLectivo.objects.create(
            nombre="2026M", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 11, 30), activo=True
        )
        self.nivel = Nivel.objects.create(nombre="Básica")
        self.asignatura = Asignatura.objects.create(nombre="Química", codigo="QUI101")
        self.clase = Clase.objects.create(periodo=self.periodo, nivel=self.nivel, nombre="8vo")

        self.seccion_guia = Seccion.objects.create(
            clase=self.clase, codigo="SG-A", nombre="A", docente=self.docente_user
        )
        self.seccion_ajena = Seccion.objects.create(clase=self.clase, codigo="SG-B", nombre="B")

        self.materia_propia = Materia.objects.create(
            clase=self.clase, seccion=self.seccion_guia, asignatura=self.asignatura, docente=self.docente_user
        )
        self.materia_ajena = Materia.objects.create(
            clase=self.clase, seccion=self.seccion_ajena, asignatura=self.asignatura
        )

        # Estudiantes
        self.hijo = Estudiante.objects.create(
            codigo_estudiante="EST-HIJO",
            primer_nombre="Pedro",
            primer_apellido="Gómez",
            genero="M",
        )
        EstudianteClase.objects.create(
            estudiante=self.hijo, clase=self.clase, seccion=self.seccion_guia, periodo=self.periodo
        )
        Responsable.objects.create(estudiante=self.hijo, pariente=self.pariente)

        self.otro_estudiante = Estudiante.objects.create(
            codigo_estudiante="EST-OTRO",
            primer_nombre="María",
            primer_apellido="López",
            genero="F",
        )
        EstudianteClase.objects.create(
            estudiante=self.otro_estudiante, clase=self.clase, seccion=self.seccion_ajena, periodo=self.periodo
        )

    def _crear_mensaje(self, remitente, ambito, target=None):
        mensaje = Mensaje(remitente=remitente, asunto="Saludos", cuerpo="Cuerpo", ambito_destinatario=ambito)
        if target is not None:
            from django.contrib.contenttypes.models import ContentType
            mensaje.content_type = ContentType.objects.get_for_model(type(target))
            mensaje.object_id = target.id
        mensaje.save()
        return mensaje

    # --- Política base -------------------------------------------------

    def test_staff_sin_perfil_denegado(self):
        self.assertFalse(puede(self.staff_sin_perfil, "grading.evaluar"))
        self.assertFalse(puede(self.staff_sin_perfil, "grading.evaluar", objeto=None))

    def test_objeto_de_tipo_desconocido_denegado(self):
        # Con permiso de perfil vigente, un tipo no contemplado se deniega.
        self.assertTrue(puede(self.docente_user, "grading.evaluar", objeto=None))
        self.assertFalse(puede(self.docente_user, "grading.evaluar", objeto=self.periodo))
        self.assertFalse(puede(self.pariente_user, "people.estudiantes_ver", objeto=self.periodo))

    def test_usuario_inhabilitado_denegado(self):
        self.pariente_user.habilitado = False
        self.pariente_user.save()
        self.assertFalse(puede(self.pariente_user, "people.estudiantes_ver", objeto=self.hijo))

    # --- Ámbito docente -------------------------------------------------

    def test_docente_guia_accede_por_seccion(self):
        self.assertTrue(secciones_visibles(self.docente_user).filter(pk=self.seccion_guia.pk).exists())
        self.assertFalse(secciones_visibles(self.docente_user).filter(pk=self.seccion_ajena.pk).exists())
        self.assertTrue(puede(self.docente_user, "people.estudiantes_ver", objeto=self.hijo))
        self.assertFalse(puede(self.docente_user, "people.estudiantes_ver", objeto=self.otro_estudiante))

    def test_docente_auxiliar_accede_por_docentemateria(self):
        DocenteMateria.objects.create(materia=self.materia_ajena, docente=self.docente_user, es_titular=False)
        self.assertTrue(puede(self.docente_user, "grading.evaluar", objeto=self.materia_ajena))
        self.assertIn(self.materia_ajena, materias_visibles(self.docente_user))
        # Al impartir en la sección ajena alcanza también a sus estudiantes.
        self.assertTrue(puede(self.docente_user, "people.estudiantes_ver", objeto=self.otro_estudiante))

    def test_materias_visibles_del_pariente_vacias(self):
        self.assertEqual(list(materias_visibles(self.pariente_user)), [])

    def test_estudiantes_visibles_docente_acota_secciones(self):
        visibles = estudiantes_visibles(self.docente_user)
        self.assertIn(self.hijo, visibles)
        self.assertNotIn(self.otro_estudiante, visibles)

    # --- Ámbito pariente -------------------------------------------------

    def test_pariente_lee_hijo_y_no_otros(self):
        self.assertTrue(puede(self.pariente_user, "people.estudiantes_ver", objeto=self.hijo))
        self.assertFalse(puede(self.pariente_user, "people.estudiantes_ver", objeto=self.otro_estudiante))
        visibles = estudiantes_visibles(self.pariente_user)
        self.assertIn(self.hijo, visibles)
        self.assertNotIn(self.otro_estudiante, visibles)

    def test_post_detalle_estudiante_denegado_con_solo_lectura(self):
        self.client.force_login(self.pariente_user)
        response = self.client.post(
            f"/estudiantes/{self.hijo.id}/",
            {"matricula_id": self.hijo.inscripciones.first().id, "motivo_retiro": "cambio de ciudad"},
        )
        self.assertEqual(response.status_code, 302)
        self.hijo.refresh_from_db()
        self.assertFalse(self.hijo.retirado)

    # --- Privacidad de mensajes -----------------------------------------

    def test_mensaje_remitente_puede_leer(self):
        mensaje = self._crear_mensaje(self.docente_user, "USUARIO", target=self.pariente_user)
        self.assertTrue(puede_leer_mensaje(self.docente_user, mensaje))

    def test_mensaje_destinatario_puede_leer(self):
        mensaje = self._crear_mensaje(self.admin, "USUARIO", target=self.pariente_user)
        self.assertTrue(puede_leer_mensaje(self.pariente_user, mensaje))

    def test_mensaje_global_visible_para_autenticados(self):
        mensaje = self._crear_mensaje(self.admin, "GLOBAL")
        self.assertTrue(puede_leer_mensaje(self.pariente_user, mensaje))

    def test_mensaje_ajeno_denegado(self):
        mensaje = self._crear_mensaje(self.admin, "USUARIO", target=self.docente_user)
        self.assertFalse(puede_leer_mensaje(self.pariente_user, mensaje))
