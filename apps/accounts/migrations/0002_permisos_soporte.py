# Migración de datos: catálogo de permisos operativos del módulo de soporte.
# El catálogo Permiso se administra por Admin; esta migración garantiza que
# los permisos exigidos por las vistas existan en despliegues existentes.
from django.db import migrations


PERMISOS = [
    {
        "codigo": "support.incidencias_gestionar",
        "nombre": "Gestionar Incidencias",
        "modulo": "support",
    },
    {
        "codigo": "support.mensajes_enviar",
        "nombre": "Enviar Mensajes",
        "modulo": "support",
    },
]


def crear_permisos(apps, schema_editor):
    Permiso = apps.get_model("accounts", "Permiso")
    for datos in PERMISOS:
        Permiso.objects.get_or_create(codigo=datos["codigo"], defaults=datos)


def eliminar_permisos(apps, schema_editor):
    Permiso = apps.get_model("accounts", "Permiso")
    for datos in PERMISOS:
        Permiso.objects.filter(codigo=datos["codigo"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(crear_permisos, eliminar_permisos),
    ]
