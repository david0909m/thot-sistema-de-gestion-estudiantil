import os
from PIL import Image
from io import BytesIO
from datetime import date
from django.core.files.base import ContentFile
from django.db import transaction
from .models import Estudiante, EstudianteClase, Seccion
from apps.audit.services import registrar_evento


def procesar_variantes_imagen(image_file):
    """
    Recibe una imagen cargada y devuelve un diccionario con 3 variantes procesadas con Pillow
    (Traducción exacta de CarrierWave / foto_uploader.rb):
    - 'original': 600x800 max (JPEG Calidad 95)
    - 'normal': 375x500 max
    - 'thumb': 75x100 max
    """
    if not image_file:
        return None

    img = Image.open(image_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    sizes = {
        "original": (600, 800),
        "normal": (375, 500),
        "thumb": (75, 100)
    }

    variantes = {}
    base_name = os.path.splitext(os.path.basename(image_file.name))[0]

    for name, size in sizes.items():
        img_copy = img.copy()
        img_copy.thumbnail(size, Image.Resampling.LANCZOS)
        buffer = BytesIO()
        quality = 95 if name == "original" else 85
        img_copy.save(buffer, format="JPEG", quality=quality)
        filename = f"{name}_{base_name}.jpg"
        variantes[name] = ContentFile(buffer.getvalue(), name=filename)

    return variantes


@transaction.atomic
def trasladar_estudiante(estudiante_clase, nueva_seccion, usuario=None):
    """
    Ejecuta el traslado de un estudiante a una nueva sección dentro del mismo período.
    Actualiza la matrícula indicando la nueva sección y la marca de estado TRASLADADO.
    """
    seccion_anterior = estudiante_clase.seccion
    if seccion_anterior == nueva_seccion:
        return estudiante_clase

    estudiante_clase.seccion = nueva_seccion
    estudiante_clase.clase = nueva_seccion.clase
    estudiante_clase.estado = "TRASLADADO"
    estudiante_clase.save()

    # Registrar evento de auditoría
    registrar_evento(
        accion="TRASLADO_ESTUDIANTE",
        usuario=usuario,
        objeto_tipo="Estudiante",
        objeto_id=str(estudiante_clase.estudiante.id),
        descripcion=f"Traslado de estudiante {estudiante_clase.estudiante.codigo_estudiante} de {seccion_anterior} a {nueva_seccion}"
    )

    return estudiante_clase


@transaction.atomic
def retirar_estudiante(estudiante_clase, motivo, usuario=None):
    """
    Ejecuta el retiro de un estudiante del colegio o período lectivo.
    """
    estudiante_clase.estado = "RETIRADO"
    estudiante_clase.save()

    estudiante = estudiante_clase.estudiante
    estudiante.retirado = True
    estudiante.fecha_retiro = date.today()
    estudiante.motivo_retiro = motivo
    estudiante.activo = False
    estudiante.save()

    registrar_evento(
        accion="RETIRO_ESTUDIANTE",
        usuario=usuario,
        objeto_tipo="Estudiante",
        objeto_id=str(estudiante.id),
        descripcion=f"Retiro de estudiante {estudiante.codigo_estudiante}. Motivo: {motivo}"
    )

    return estudiante_clase
