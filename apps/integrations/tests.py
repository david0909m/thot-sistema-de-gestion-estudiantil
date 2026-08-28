from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from apps.integrations.solvencia_externa import SolvenciaExternaAdapter, ESTADO_SOLVENTE, ESTADO_DESCONOCIDO
from apps.integrations.etl import RubyYamlToJsonConverter, ConciliadorDatos
from apps.audit.models import AuditEvent


class IntegrationsAndEtlTests(TestCase):
    def test_solvencia_externa_adapter_with_mock_data(self):
        adapter = SolvenciaExternaAdapter(
            mock_responses={
                "EST-001": ESTADO_SOLVENTE,
                "EST-002": "INSOLVENTE"
            }
        )
        self.assertEqual(adapter.consultar_solvencia("EST-001"), ESTADO_SOLVENTE)
        self.assertEqual(adapter.consultar_solvencia("EST-002"), "INSOLVENTE")

    def test_solvencia_externa_adapter_fallback_desconocido_and_audit(self):
        adapter = SolvenciaExternaAdapter(connection_string=None)
        resultado = adapter.consultar_solvencia("EST-999")
        
        self.assertEqual(resultado, ESTADO_DESCONOCIDO)
        self.assertTrue(
            AuditEvent.objects.filter(accion="SOLVENCIA_EXTERNA_CONEXION_FALLIDA").exists()
        )

    def test_ruby_yaml_to_json_converter(self):
        ruby_hash_str = "--- \n:reglas: \n  :redondear_consolidados: true\n  :porcentaje_minimo: 99.9\n"
        converted = RubyYamlToJsonConverter.parse_ruby_yaml(ruby_hash_str)
        
        self.assertIsInstance(converted, dict)
        self.assertIn("reglas", converted)
        self.assertTrue(converted["reglas"]["redondear_consolidados"])

    def test_conciliador_datos(self):
        informe = ConciliadorDatos.generar_informe_conciliacion()
        self.assertIn("conteos", informe)
        self.assertIn("huerfanos", informe)

    def test_import_legacy_data_command_dry_run(self):
        out = StringIO()
        call_command("import_legacy_data", "--dry-run", stdout=out)
        self.assertIn("INICIANDO PROCESO ETL", out.getvalue())

    def test_conciliar_datos_command(self):
        out = StringIO()
        call_command("conciliar_datos", stdout=out)
        self.assertIn("INFORME DE CONCILIACIÓN DE DATOS", out.getvalue())
