from django.core.management.base import BaseCommand
from apps.integrations.etl import ConciliadorDatos
from apps.audit.services import registrar_evento


class Command(BaseCommand):
    help = "Genera el informe de conciliación de integridad y conteo de datos para el corte."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== INFORME DE CONCILIACIÓN DE DATOS E INTEGRIDAD ACADÉMICA ==="))
        
        informe = ConciliadorDatos.generar_informe_conciliacion()

        self.stdout.write("\n1. Conteos de Registros Persistidos:")
        for modelo, cantidad in informe["conteos"].items():
            self.stdout.write(f"   - {modelo.capitalize()}: {cantidad}")

        self.stdout.write("\n2. Auditoría de Registros Huérfanos:")
        for regla, cnt in informe["huerfanos"].items():
            color = self.style.SUCCESS if cnt == 0 else self.style.ERROR
            self.stdout.write(color(f"   - {regla}: {cnt}"))

        if informe["integridad_valida"]:
            self.stdout.write(self.style.SUCCESS("\n[OK] ESTADO DE INTEGRIDAD: VÁLIDA (Cero datos huérfanos)"))
            registrar_evento(
                accion="CONCILIACION_DATOS_EXITOSA",
                origen="CLI",
                descripcion="Informe de conciliación generado sin discrepancias de integridad."
            )
        else:
            self.stdout.write(self.style.ERROR("\n[ALERTA] ESTADO DE INTEGRIDAD: INCONSISTENCIAS DETECTADAS"))
            registrar_evento(
                accion="CONCILIACION_DATOS_INCONSISTENTE",
                origen="CLI",
                descripcion="Se detectaron registros huérfanos durante la conciliación.",
                exito=False
            )
