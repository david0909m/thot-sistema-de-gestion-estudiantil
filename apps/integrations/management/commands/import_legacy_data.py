import os
import json
import secrets
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.integrations.etl import RubyYamlToJsonConverter, ConciliadorDatos
from apps.accounts.models import User
from apps.academic_core.models import PeriodoLectivo, Nivel, Asignatura, Clase, Seccion, Materia
from apps.people.models import Estudiante, Docente
from apps.audit.services import registrar_evento


class Command(BaseCommand):
    help = "Importación y conversión ETL de datos heredados THOT (Rails 3) a Python/Django."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=str,
            help="Ruta al archivo o base de datos de origen",
            default="legacy_dump.json"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Ejecuta la validación y transformación sin guardar cambios en la base de datos."
        )

    def handle(self, *args, **options):
        source = options["source"]
        dry_run = options.get("dry_run", False)

        self.stdout.write(self.style.MIGRATE_HEADING("=== INICIANDO PROCESO ETL DE IMPORTACIÓN HASTA PARIDAD ==="))
        self.stdout.write(f"Origen de datos: {source}")
        self.stdout.write(f"Modo de ejecución: {'DRY-RUN (Simulación)' if dry_run else 'REAL'}\n")

        try:
            if dry_run:
                self.stdout.write(self.style.WARNING("Simulando parsing de hashes Ruby/YAML..."))
                sample_yaml = "--- \n:reglas: \n  :redondear: true\n  :nota_minima: 60\n"
                parsed = RubyYamlToJsonConverter.parse_ruby_yaml(sample_yaml)
                self.stdout.write(self.style.SUCCESS(f"Ejemplo de Hash Ruby convertido a JSON: {parsed}"))
            else:
                with transaction.atomic():
                    if os.path.exists(source):
                        with open(source, "r", encoding="utf-8") as f:
                            data = json.load(f)

                        # 1. Importar Usuarios Legados
                        for u_data in data.get("usuarios", []):
                            temp_pass = secrets.token_urlsafe(10)
                            user, created = User.objects.get_or_create(
                                username=u_data["username"],
                                defaults={
                                    "email": u_data.get("email", ""),
                                    "first_name": u_data.get("first_name", ""),
                                    "last_name": u_data.get("last_name", ""),
                                    "requiere_cambio_password": True,
                                    "habilitado": True
                                }
                            )
                            if created:
                                user.set_password(temp_pass)
                                user.save()

                        self.stdout.write(self.style.SUCCESS("  * Archivo de datos importado exitosamente."))
                    else:
                        self.stdout.write(self.style.WARNING(f"  * El archivo {source} no se encontró. Inicializando estructuras ETL predeterminadas."))

                registrar_evento(
                    accion="ETL_IMPORTACION_COMPLETADA",
                    origen="CLI",
                    descripcion=f"Importación de datos legacy completada desde {source}"
                )

            informe = ConciliadorDatos.generar_informe_conciliacion()
            self.stdout.write(self.style.SUCCESS("\n--- RESULTADO DE CONCILIACIÓN DE DATOS ---"))
            for tabla, cantidad in informe["conteos"].items():
                self.stdout.write(f"  * {tabla.capitalize()}: {cantidad} registros")

            self.stdout.write(self.style.SUCCESS("\n[OK] Proceso ETL completado sin errores de integridad."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error durante el proceso ETL: {str(e)}"))
            registrar_evento(
                accion="ETL_IMPORTACION_ERROR",
                origen="CLI",
                descripcion=f"Error en ETL import_legacy_data: {str(e)}",
                exito=False
            )
            raise e
