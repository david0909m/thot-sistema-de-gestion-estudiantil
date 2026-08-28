from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.academic_core.models import (
    PeriodoLectivo, TipoNota, Nivel, Asignatura, Escala,
    Clase, Seccion, Materia, Horario, DocenteMateria
)


class AcademicCoreTests(TestCase):
    def test_periodo_lectivo_validation(self):
        periodo_invalido = PeriodoLectivo(
            nombre="Periodo Inválido",
            fecha_inicio=date(2026, 12, 31),
            fecha_fin=date(2026, 1, 1)
        )
        with self.assertRaises(ValidationError):
            periodo_invalido.clean()

    def test_copiar_estructura_periodo(self):
        periodo_2026 = PeriodoLectivo.objects.create(
            nombre="Año Escolar 2026",
            fecha_inicio=date(2026, 1, 15),
            fecha_fin=date(2026, 11, 30),
            activo=True
        )

        bloque = TipoNota.objects.create(
            nombre="Bloque 1",
            periodo=periodo_2026,
            es_consolidado=True,
            orden=1
        )

        parcial = TipoNota.objects.create(
            nombre="Parcial 1",
            periodo=periodo_2026,
            padre=bloque,
            es_consolidado=False,
            orden=1,
            peso=Decimal("1.00"),
            porcentaje=Decimal("50.00")
        )

        # Copiar estructura para el 2027
        periodo_2027 = periodo_2026.copiar_estructura(
            nuevo_nombre="Año Escolar 2027",
            nueva_fecha_inicio=date(2027, 1, 15),
            nueva_fecha_fin=date(2027, 11, 30)
        )

        self.assertEqual(periodo_2027.tipos_notas.count(), 2)
        bloque_clon = periodo_2027.tipos_notas.get(nombre="Bloque 1")
        parcial_clon = periodo_2027.tipos_notas.get(nombre="Parcial 1")

        self.assertIsNone(bloque_clon.padre)
        self.assertEqual(parcial_clon.padre, bloque_clon)
        self.assertEqual(parcial_clon.porcentaje, Decimal("50.00"))

    def test_materia_lock_version_concurrency(self):
        periodo = PeriodoLectivo.objects.create(
            nombre="Periodo Concurrente",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 11, 30)
        )
        nivel = Nivel.objects.create(nombre="Secundaria", codigo="SEC")
        asignatura = Asignatura.objects.create(nombre="Matemáticas", codigo="MAT")
        clase = Clase.objects.create(nombre="7mo A", periodo=periodo, nivel=nivel)

        materia = Materia.objects.create(
            nombre="Matemáticas 7mo",
            asignatura=asignatura,
            clase=clase
        )

        # Simular dos instancias cargadas concurrentemente
        instancia_a = Materia.objects.get(pk=materia.pk)
        instancia_b = Materia.objects.get(pk=materia.pk)

        # Primera modificación exitosa
        instancia_a.nombre = "Matemáticas I"
        instancia_a.save()
        self.assertEqual(instancia_a.lock_version, 1)
        self.assertEqual(Materia.objects.get(pk=materia.pk).lock_version, 1)

        # Segunda modificación concurrente con versión desactualizada -> debe lanzar ValidationError
        instancia_b.nombre = "Matemáticas Avanzada"
        with self.assertRaises(ValidationError):
            instancia_b.save()
