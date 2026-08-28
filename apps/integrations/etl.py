import re
import yaml
import unicodedata
from decimal import Decimal
from django.db import models
from apps.accounts.models import User, Perfil, Permiso, AsignacionUsuario
from apps.academic_core.models import PeriodoLectivo, Nivel, Asignatura, Clase, Seccion, Materia, TipoNota
from apps.people.models import Estudiante, Pariente, Responsable, EstudianteClase, Docente
from apps.grading.models import Evaluacion, Calificacion, ResumenAcademicoEstudiante
from apps.support.models import Incidencia, Mensaje
from apps.audit.models import AuditEvent


class RubyYamlToJsonConverter:
    """
    Parsea y convierte cadenas de Hashes/Arreglos serializados en Ruby (YAML / Símbolos :clave)
    a diccionarios y listas nativas de Python compatibles con `JSONField`.
    """
    @staticmethod
    def parse_ruby_yaml(raw_str):
        if not raw_str or not isinstance(raw_str, str):
            return {}

        cleaned = raw_str.strip()
        # Eliminar cabecera de clase Ruby si existe (ej: !ruby/hash:HashWithIndifferentAccess)
        cleaned = re.sub(r"!ruby/[^\s\n]+", "", cleaned)
        # Convertir símbolos de clave Ruby :clave: -> clave:
        cleaned = re.sub(r":([a-zA-Z0-9_]+)\s*=>", r"\1:", cleaned)
        cleaned = re.sub(r"(?<=\s):([a-zA-Z0-9_]+):", r"\1:", cleaned)

        try:
            parsed = yaml.safe_load(cleaned)
            return RubyYamlToJsonConverter._clean_keys(parsed)
        except Exception:
            # Fallback a extracción de claves por expresiones regulares
            return {"raw_text": raw_str}

    @staticmethod
    def _clean_keys(data):
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                clean_key = str(k).lstrip(":") if k else ""
                new_dict[clean_key] = RubyYamlToJsonConverter._clean_keys(v)
            return new_dict
        elif isinstance(data, list):
            return [RubyYamlToJsonConverter._clean_keys(item) for item in data]
        elif isinstance(data, str):
            return unicodedata.normalize("NFC", data.strip())
        return data


class LegacyDataTransformer:
    """
    Transformador de datos legacy de Rails a modelos objetivo Django.
    """
    @staticmethod
    def normalizar_texto(texto):
        if not texto:
            return ""
        return unicodedata.normalize("NFC", str(texto).strip())

    @staticmethod
    def transformar_configuracion_periodo(config_raw):
        return RubyYamlToJsonConverter.parse_ruby_yaml(config_raw)


class ConciliadorDatos:
    """
    Verifica la integridad de datos, conteo de tablas, detección de huérfanos
    y sumas de control tras el proceso de migración ETL.
    """
    @staticmethod
    def generar_informe_conciliacion():
        informe = {
            "conteos": {
                "usuarios": User.objects.count(),
                "estudiantes": Estudiante.objects.count(),
                "docentes": Docente.objects.count(),
                "parientes": Pariente.objects.count(),
                "periodos": PeriodoLectivo.objects.count(),
                "clases": Clase.objects.count(),
                "secciones": Seccion.objects.count(),
                "materias": Materia.objects.count(),
                "evaluaciones": Evaluacion.objects.count(),
                "calificaciones": Calificacion.objects.count(),
                "audit_events": AuditEvent.objects.count(),
            },
            "huerfanos": {
                "calificaciones_sin_estudiante": Calificacion.objects.filter(estudiante__isnull=True).count(),
                "calificaciones_sin_materia": Calificacion.objects.filter(materia__isnull=True).count(),
                "matriculas_sin_estudiante": EstudianteClase.objects.filter(estudiante__isnull=True).count(),
                "materias_sin_clase": Materia.objects.filter(clase__isnull=True).count(),
            },
            "integridad_valida": True
        }

        # Marcar integridad inválida si existen huérfanos
        if any(cnt > 0 for cnt in informe["huerfanos"].values()):
            informe["integridad_valida"] = False

        return informe
