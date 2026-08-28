from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from apps.accounts.models import User
from apps.academic_core.models import PeriodoLectivo, Nivel, Clase, Seccion, Asignatura, Materia
from apps.people.models import Estudiante, EstudianteClase
from apps.support.models import Incidencia, Mensaje


class FrontendUISmokeTests(TestCase):
    """
    Pruebas de humo para verificar el renderizado exitoso (HTTP 200 OK)
    de todas las pantallas principales del sistema THOT.
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="admin_ui", password="password", is_superuser=True, is_staff=True
        )
        self.periodo = PeriodoLectivo.objects.create(
            nombre="2026", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 11, 30), activo=True
        )
        self.nivel = Nivel.objects.create(nombre="Secundaria")
        self.clase = Clase.objects.create(periodo=self.periodo, nivel=self.nivel, nombre="7mo Grado")
        self.seccion = Seccion.objects.create(clase=self.clase, codigo="SEC-7A", nombre="Sección A")
        self.asignatura = Asignatura.objects.create(nombre="Historia", codigo="HIS101")
        self.materia = Materia.objects.create(
            nombre="Historia Universal", asignatura=self.asignatura, clase=self.clase, seccion=self.seccion
        )
        self.estudiante = Estudiante.objects.create(
            codigo_estudiante="EST-2026-UI", primer_nombre="Laura", primer_apellido="García", genero="F"
        )
        EstudianteClase.objects.create(
            estudiante=self.estudiante, periodo=self.periodo, clase=self.clase, seccion=self.seccion
        )
        self.incidencia = Incidencia.objects.create(
            estudiante=self.estudiante, periodo=self.periodo, tipo_incidencia="LEVE",
            descripcion="Incidencia de prueba", reportado_por=self.user
        )
        self.mensaje = Mensaje.objects.create(
            remitente=self.user, asunto="Mensaje de prueba", cuerpo="Contenido"
        )

    def test_all_web_screens_render_200_ok(self):
        self.client.force_login(self.user)

        routes = [
            ("dashboard", {}),
            ("configuracion_institucion", {}),
            ("periodos_list", {}),
            ("periodo_create", {}),
            ("clases_list", {}),
            ("clase_create", {}),
            ("seccion_create", {}),
            ("horarios_list", {}),
            ("asignaturas_list", {}),
            ("asignatura_create", {}),
            ("niveles_list", {}),
            ("nivel_create", {}),
            ("tipos_nota_list", {}),
            ("tipo_nota_create", {}),
            ("escalas_list", {}),
            ("escala_create", {}),
            ("catalogos_panel", {}),
            ("estudiantes_list", {}),
            ("estudiante_detail", {"estudiante_id": self.estudiante.id}),
            ("estudiante_create", {}),
            ("ficha_medica", {"estudiante_id": self.estudiante.id}),
            ("docentes_list", {}),
            ("docente_create", {}),
            ("parientes_list", {}),
            ("pariente_create", {}),
            ("matricula_create", {}),
            ("evaluaciones_list", {}),
            ("evaluacion_create", {}),
            ("consolidacion", {}),
            ("sabana_notas", {}),
            ("boletin_web", {"estudiante_id": self.estudiante.id}),
            ("usuarios_list", {}),
            ("usuario_create", {}),
            ("roles_list", {}),
            ("rol_create", {}),
            ("incidencias_list", {}),
            ("incidencia_detail", {"incidencia_id": self.incidencia.id}),
            ("mensajes_inbox", {}),
            ("mensaje_detail", {"mensaje_id": self.mensaje.id}),
            ("reportes_index", {}),
            ("auditoria_list", {}),
            ("admin:index", {}),
            ("admin:academic_core_clase_changelist", {}),
        ]

        for route_name, kwargs in routes:
            url = reverse(route_name, kwargs=kwargs)
            res = self.client.get(url)
            self.assertEqual(
                res.status_code,
                200,
                f"La ruta '{route_name}' ({url}) falló con código {res.status_code}"
            )
