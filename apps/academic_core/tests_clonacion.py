from datetime import date, time

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.accounts.models import AsignacionUsuario, Perfil
from apps.academic_core.models import (
    PeriodoLectivo,
    Nivel,
    Asignatura,
    Clase,
    Seccion,
    Materia,
    TipoNota,
    DocenteMateria,
    Horario,
)


class DeepCloningPeriodoTests(TestCase):
    def setUp(self):
        self.periodo = PeriodoLectivo.objects.create(
            nombre="2025", fecha_inicio=date(2025, 1, 15), fecha_fin=date(2025, 11, 30), activo=True
        )
        self.tipo_bloque = TipoNota.objects.create(nombre="Bloque I", periodo=self.periodo, es_consolidado=True, orden=1)
        self.tipo_parcial = TipoNota.objects.create(nombre="Parcial 1", periodo=self.periodo, padre=self.tipo_bloque, orden=2)

        self.nivel = Nivel.objects.create(nombre="Primaria")
        self.clase = Clase.objects.create(periodo=self.periodo, nivel=self.nivel, nombre="1er Grado")
        self.seccion = Seccion.objects.create(clase=self.clase, codigo="SEC-1A", nombre="Sección A")
        self.asignatura = Asignatura.objects.create(nombre="Español", codigo="ESP101")
        self.materia = Materia.objects.create(
            nombre="Español 1A", asignatura=self.asignatura, clase=self.clase, seccion=self.seccion
        )

    def test_deep_cloning_clones_classes_sections_and_materias(self):
        nuevo_p = self.periodo.copiar_estructura("2026", date(2026, 1, 15), date(2026, 11, 30))

        self.assertEqual(nuevo_p.nombre, "2026")
        self.assertEqual(nuevo_p.tipos_notas.count(), 2)
        self.assertEqual(nuevo_p.clases.count(), 1)

        nueva_clase = nuevo_p.clases.first()
        self.assertEqual(nueva_clase.nombre, "1er Grado")
        self.assertEqual(nueva_clase.secciones.count(), 1)
        self.assertEqual(nueva_clase.materias.count(), 1)

        nueva_materia = nueva_clase.materias.first()
        self.assertEqual(nueva_materia.nombre, "Español 1A")
        self.assertEqual(nueva_materia.asignatura, self.asignatura)


class CopiarEstructuraParidadTests(TestCase):
    """
    Verifica que copiar_estructura preserve todos los datos de la cadena
    Clase -> Seccion -> Materia -> DocenteMateria/Horario/AsignacionUsuario,
    con paridad respecto al copiar! del legado Rails.
    """

    def setUp(self):
        User = get_user_model()
        self.periodo = PeriodoLectivo.objects.create(
            nombre="2025", fecha_inicio=date(2025, 1, 15), fecha_fin=date(2025, 11, 30), activo=True
        )
        self.nivel = Nivel.objects.create(nombre="Primaria CLN", codigo="PRI_CLN")
        self.asignatura = Asignatura.objects.create(nombre="Matemáticas", codigo="MATCLN")

        self.docente_guia = User.objects.create_user(username="guia25", password="clave12345")
        self.docente_aux = User.objects.create_user(username="aux25", password="clave12345")

        self.perfil = Perfil.objects.create(nombre="Profesor CLN", codigo="PROF_CLN")

        self.clase = Clase.objects.create(
            periodo=self.periodo, nivel=self.nivel, nombre="2do Grado",
            config={"regla": "asistencia_obligatoria"}
        )
        self.seccion = Seccion.objects.create(
            clase=self.clase, codigo="SEC-2A", nombre="Sección A",
            docente=self.docente_guia,
        )
        self.materia = Materia.objects.create(
            nombre="Mates 2A",
            asignatura=self.asignatura,
            clase=self.clase,
            seccion=self.seccion,
            docente=self.docente_guia,
            config={"periodo_actual_hash": "hash_viejo", "boletin_estilo": "compacto"},
        )
        DocenteMateria.objects.create(materia=self.materia, docente=self.docente_aux, es_titular=False)
        self.horario = Horario.objects.create(
            materia=self.materia,
            dia_semana=1,
            hora_inicio=time(8, 0),
            hora_fin=time(9, 0),
            aula="Aula 3",
        )
        ct_clase = ContentType.objects.get_for_model(Clase)
        self.asignacion_origen = AsignacionUsuario.objects.create(
            usuario=self.docente_guia,
            perfil=self.perfil,
            content_type=ct_clase,
            object_id=self.clase.id,
        )

    def test_copia_docente_guia_configs_titularidades_horarios_y_asignaciones(self):
        nuevo_p = self.periodo.copiar_estructura("2026B", date(2026, 1, 15), date(2026, 11, 30))

        nueva_clase = nuevo_p.clases.get(nombre="2do Grado")
        self.assertEqual(nueva_clase.config, {"regla": "asistencia_obligatoria"})

        nueva_seccion = nueva_clase.secciones.get(codigo=f"SEC-2A_{nuevo_p.id}")
        self.assertEqual(nueva_seccion.docente, self.docente_guia)

        nueva_materia = nueva_clase.materias.get(nombre="Mates 2A")
        self.assertEqual(nueva_materia.config, {"boletin_estilo": "compacto"})
        self.assertNotIn("periodo_actual_hash", nueva_materia.config)
        self.assertEqual(nueva_materia.docente, self.docente_guia)

        dm_nueva = nueva_materia.asignaciones_docentes.get(docente=self.docente_aux)
        self.assertFalse(dm_nueva.es_titular)

        horario_nuevo = nueva_materia.horarios.get(dia_semana=1)
        self.assertEqual(horario_nuevo.aula, "Aula 3")

        ct_clase = ContentType.objects.get_for_model(Clase)
        asignacion_nueva = AsignacionUsuario.objects.get(
            content_type=ct_clase, object_id=nueva_clase.id
        )
        self.assertEqual(asignacion_nueva.usuario, self.docente_guia)
        self.assertEqual(asignacion_nueva.perfil, self.perfil)
        self.assertTrue(asignacion_nueva.activo)

        self.assertTrue(
            AsignacionUsuario.objects.filter(
                content_type=ct_clase, object_id=self.clase.id
            ).exists(),
            "La asignación original no debe alterarse",
        )


class TraslapePeriodosTests(TestCase):
    def test_clean_detecta_traslape_con_periodo_existente(self):
        p1 = PeriodoLectivo.objects.create(
            nombre="2026 Ene-Jun", fecha_inicio=date(2026, 2, 1), fecha_fin=date(2026, 6, 30)
        )
        traslapado = PeriodoLectivo(
            nombre="2026 Jun-Dic", fecha_inicio=date(2026, 6, 1), fecha_fin=date(2026, 12, 31)
        )
        with self.assertRaises(ValidationError) as ctx:
            traslapado.full_clean()
        self.assertIn(p1.nombre, str(ctx.exception))

    def test_clean_permite_periodos_disjuntos_y_edicion_del_propio(self):
        PeriodoLectivo.objects.create(
            nombre="2026 Ene-Jun", fecha_inicio=date(2026, 2, 1), fecha_fin=date(2026, 6, 30)
        )
        disjunto = PeriodoLectivo(
            nombre="2026 Jul-Dic", fecha_inicio=date(2026, 7, 1), fecha_fin=date(2026, 12, 31)
        )
        disjunto.full_clean()

        existente = PeriodoLectivo.objects.get(nombre="2026 Ene-Jun")
        existente.nombre = "Renombrado"
        existente.full_clean()
