from datetime import date

from django.test import TestCase, Client

from apps.accounts.models import User
from apps.academic_core.models import PeriodoLectivo
from apps.people.models import Estudiante
from apps.support.models import Incidencia
from apps.audit.models import AuditEvent
from apps.audit.context import fijar_actor, limpiar_actor
from apps.audit.services import registrar_evento


def crear_estudiante(codigo):
    return Estudiante.objects.create(
        codigo_estudiante=codigo,
        primer_nombre="Ana",
        primer_apellido="Rojas",
        genero="F",
    )


class InmutabilidadAuditEventTests(TestCase):
    def test_origen_sistema_valido_en_choices(self):
        self.assertIn(("SISTEMA", "Sistema / Señales Internas"), AuditEvent.ORIGEN_CHOICES)
        evento = registrar_evento(accion="PRUEBA", origen="SISTEMA")
        self.assertEqual(evento.origen, "SISTEMA")

    def test_evento_no_permite_actualizacion(self):
        evento = registrar_evento(accion="PRUEBA")
        evento.accion = "MODIFICADA"
        with self.assertRaises(RuntimeError):
            evento.save()

    def test_evento_no_permite_delete_ni_queryset_delete(self):
        evento = registrar_evento(accion="PRUEBA")
        with self.assertRaises(RuntimeError):
            evento.delete()
        with self.assertRaises(RuntimeError):
            AuditEvent.objects.all().delete()
        self.assertTrue(AuditEvent.objects.filter(accion="PRUEBA").exists())


class ActorYIpEnSenalesTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username="auditor", password="Password123!")

    def tearDown(self):
        limpiar_actor()

    def test_senal_atribuye_actor_e_ip_del_contexto(self):
        fijar_actor(self.usuario, "10.0.0.5")
        estudiante = crear_estudiante("EST-AUD-01")

        evento = AuditEvent.objects.filter(accion="CREAR_ESTUDIANTE", objeto_id=str(estudiante.id)).get()
        self.assertEqual(evento.usuario_id, self.usuario.id)
        self.assertEqual(evento.ip_address, "10.0.0.5")
        self.assertEqual(evento.origen, "SISTEMA")

    def test_senal_sin_contexto_registra_usuario_nulo(self):
        estudiante = crear_estudiante("EST-AUD-02")
        evento = AuditEvent.objects.filter(accion="CREAR_ESTUDIANTE", objeto_id=str(estudiante.id)).get()
        self.assertIsNone(evento.usuario_id)

    def test_actor_explcito_gana_sobre_contexto(self):
        otro = User.objects.create_user(username="otro", password="Password123!")
        fijar_actor(otro, "9.9.9.9")
        evento = registrar_evento(
            accion="PRUEBA_EXPLICITO",
            usuario=self.usuario,
            ip_address="1.1.1.1",
        )
        self.assertEqual(evento.usuario_id, self.usuario.id)
        self.assertEqual(evento.ip_address, "1.1.1.1")


class DeduplicacionEventosTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username="dedupe_admin", password="Password123!", is_superuser=True)
        self.periodo = PeriodoLectivo.objects.create(
            nombre="2026A",
            fecha_inicio=date(2026, 1, 10),
            fecha_fin=date(2026, 11, 20),
            activo=True,
        )
        self.estudiante = crear_estudiante("EST-DEDUPE")

    def test_crear_incidencia_registra_un_solo_evento(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            "/support/incidencias/",
            {
                "crear_incidencia": "1",
                "estudiante_id": self.estudiante.id,
                "tipo_incidencia": "LEVE",
                "descripcion": "Llegada tardía repetida",
                "sancion": "",
            },
        )
        self.assertEqual(response.status_code, 302)

        eventos = AuditEvent.objects.filter(accion="CREAR_INCIDENCIA")
        self.assertEqual(eventos.count(), 1)
        evento = eventos.get()
        self.assertEqual(evento.usuario_id, self.admin.id)
        self.assertEqual(evento.ip_address, "127.0.0.1")

    def test_crear_evaluacion_web_registra_un_solo_evento(self):
        from apps.academic_core.models import Nivel, Asignatura, Clase, Materia, TipoNota
        from apps.grading.models import Evaluacion
        from decimal import Decimal

        nivel = Nivel.objects.create(nombre="Primaria Dedupe")
        asignatura = Asignatura.objects.create(nombre="Ciencias Dedupe", codigo="CIE-D1")
        clase = Clase.objects.create(periodo=self.periodo, nivel=nivel, nombre="4to D")
        materia = Materia.objects.create(
            clase=clase, asignatura=asignatura, nombre="Ciencias 4to D"
        )
        tipo = TipoNota.objects.create(nombre="Bloque D", periodo=self.periodo)

        self.client.force_login(self.admin)
        response = self.client.post(
            "/evaluaciones/nueva/",
            {
                "materia": materia.id,
                "tipo_nota": tipo.id,
                "nombre": "Quiz D1",
                "fecha": "2026-03-01",
                "porcentaje": "20.00",
                "descripcion": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Evaluacion.objects.count(), 1)

        eventos = AuditEvent.objects.filter(accion="CREAR_EVALUACION")
        self.assertEqual(eventos.count(), 1)
        evento = eventos.get()
        self.assertEqual(evento.usuario_id, self.admin.id)
        self.assertEqual(evento.origen, "SISTEMA")

    def test_incidencia_signal_sin_duplicado_de_senal(self):
        """La acción CREAR_INCIDENCIA_SIGNAL ya no debe existir."""
        Incidencia.objects.create(
            estudiante=self.estudiante,
            periodo=self.periodo,
            tipo_incidencia="MERITO",
            descripcion="Ayuda a compañero",
        )
        self.assertFalse(AuditEvent.objects.filter(accion="CREAR_INCIDENCIA_SIGNAL").exists())
        self.assertTrue(AuditEvent.objects.filter(accion="CREAR_INCIDENCIA", origen="SISTEMA").exists())
