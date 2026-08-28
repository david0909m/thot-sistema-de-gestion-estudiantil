# Migración de consolidación del expediente médico (hallazgo 5).
# Copia el contenido de support.RegistroMedico hacia people.FichaMedica
# (modelo canónico) y elimina el modelo duplicado.
from django.db import migrations


def copiar_a_ficha_medica(apps, schema_editor):
    RegistroMedico = apps.get_model("support", "RegistroMedico")
    FichaMedica = apps.get_model("people", "FichaMedica")

    for registro in RegistroMedico.objects.all().iterator():
        FichaMedica.objects.update_or_create(
            estudiante_id=registro.estudiante_id,
            defaults={
                "tipo_sangre": registro.grupo_sanguineo,
                "alergias": registro.alergias,
                "padecimientos_cronicos": registro.padecimientos,
                "medicamentos_permanentes": registro.medicamentos,
                "contacto_emergencia_nombre": registro.contacto_emergencia,
                "contacto_emergencia_telefono": registro.telefono_emergencia,
                "observaciones": registro.observaciones,
            },
        )


def deshacer_copia(apps, schema_editor):
    # No se restauran filas: la tabla origen se elimina en la operación
    # siguiente y la ficha canónica conserva los datos consolidados.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("support", "0001_initial"),
        ("people", "0003_fichamedica"),
    ]

    operations = [
        migrations.RunPython(copiar_a_ficha_medica, deshacer_copia),
        migrations.DeleteModel(
            name="RegistroMedico",
        ),
    ]
