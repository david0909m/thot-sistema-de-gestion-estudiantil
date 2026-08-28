from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO
from datetime import date
from apps.academic_core.models import PeriodoLectivo, Nivel, Clase, Seccion
from apps.people.models import Estudiante, EstudianteClase
from apps.people.services import procesar_variantes_imagen, trasladar_estudiante, retirar_estudiante


class Fase1BPersonasTests(TestCase):
    def setUp(self):
        self.periodo = PeriodoLectivo.objects.create(
            nombre="2026", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 11, 30), activo=True
        )
        self.nivel = Nivel.objects.create(nombre="Primaria")
        self.clase = Clase.objects.create(periodo=self.periodo, nivel=self.nivel, nombre="1er Grado")
        self.seccion_a = Seccion.objects.create(clase=self.clase, codigo="SEC-1A", nombre="Sección A")
        self.seccion_b = Seccion.objects.create(clase=self.clase, codigo="SEC-1B", nombre="Sección B")

        self.estudiante = Estudiante.objects.create(
            codigo_estudiante="EST-2026-001",
            primer_nombre="Carlos",
            primer_apellido="Pérez",
            genero="M"
        )
        self.matricula = EstudianteClase.objects.create(
            estudiante=self.estudiante,
            periodo=self.periodo,
            clase=self.clase,
            seccion=self.seccion_a,
            estado="MATRICULADO"
        )

    def test_pillow_image_variant_generation(self):
        # Crear imagen sintética de prueba
        image = Image.new("RGB", (1200, 1600), color="blue")
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        uploaded_file = SimpleUploadedFile("test_foto.jpg", buffer.getvalue(), content_type="image/jpeg")

        variantes = procesar_variantes_imagen(uploaded_file)
        self.assertIsNotNone(variantes)
        self.assertIn("original", variantes)
        self.assertIn("normal", variantes)
        self.assertIn("thumb", variantes)

        # Inspeccionar dimensiones con Pillow
        img_thumb = Image.open(variantes["thumb"])
        self.assertLessEqual(img_thumb.width, 75)
        self.assertLessEqual(img_thumb.height, 100)

    def test_traslado_estudiante_updates_seccion_and_status(self):
        trasladar_estudiante(self.matricula, self.seccion_b)
        
        self.matricula.refresh_from_db()
        self.assertEqual(self.matricula.seccion, self.seccion_b)
        self.assertEqual(self.matricula.estado, "TRASLADADO")

    def test_retirar_estudiante_marks_retired(self):
        retirar_estudiante(self.matricula, motivo="Traslado de ciudad")

        self.matricula.refresh_from_db()
        self.estudiante.refresh_from_db()

        self.assertEqual(self.matricula.estado, "RETIRADO")
        self.assertTrue(self.estudiante.retirado)
        self.assertFalse(self.estudiante.activo)
        self.assertEqual(self.estudiante.motivo_retiro, "Traslado de ciudad")
