from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from apps.integrations.etl import RubyYamlToJsonConverter, ConciliadorDatos


class Fase4ETLTests(TestCase):
    def test_ruby_yaml_converter_parses_symbols(self):
        ruby_yaml = "--- \n:reglas: \n  :redondear: true\n  :nota_minima: 60\n"
        converted = RubyYamlToJsonConverter.parse_ruby_yaml(ruby_yaml)
        
        self.assertIsInstance(converted, dict)
        self.assertIn("reglas", converted)
        self.assertTrue(converted["reglas"].get("redondear"))
        self.assertEqual(converted["reglas"].get("nota_minima"), 60)

    def test_import_legacy_data_command_dry_run(self):
        out = StringIO()
        call_command("import_legacy_data", "--dry-run", stdout=out)
        output = out.getvalue()
        
        self.assertIn("INICIANDO PROCESO ETL DE IMPORTACIÓN HASTA PARIDAD", output)
        self.assertIn("DRY-RUN", output)
        self.assertIn("RESULTADO DE CONCILIACIÓN DE DATOS", output)

    def test_conciliar_datos_command_executes(self):
        out = StringIO()
        call_command("conciliar_datos", stdout=out)
        output = out.getvalue()

        self.assertIn("INFORME DE CONCILIACIÓN DE DATOS", output)
        self.assertIn("ESTADO DE INTEGRIDAD: VÁLIDA", output)

    def test_conciliador_datos_reports_zero_orphans_on_clean_db(self):
        informe = ConciliadorDatos.generar_informe_conciliacion()
        self.assertTrue(informe["integridad_valida"])
        for huerfano_cnt in informe["huerfanos"].values():
            self.assertEqual(huerfano_cnt, 0)
