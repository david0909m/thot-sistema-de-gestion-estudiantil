import logging
from datetime import date
from apps.audit.services import registrar_evento

logger = logging.getLogger(__name__)

# Estados del contrato único de solvencia financiera
ESTADO_SOLVENTE = "SOLVENTE"
ESTADO_INSOLVENTE = "INSOLVENTE"
ESTADO_DESCONOCIDO = "DESCONOCIDO"
ESTADO_EXENTO = "EXENTO"
ESTADO_CONVENIO_DE_PAGO = "CONVENIO_DE_PAGO"

ESTADOS_SOLVENCIA = [
    ESTADO_SOLVENTE,
    ESTADO_INSOLVENTE,
    ESTADO_DESCONOCIDO,
    ESTADO_EXENTO,
    ESTADO_CONVENIO_DE_PAGO,
]


class SolvenciaExternaAdapter:
    """
    Adaptador genérico de integración con bases de datos o servicios de solvencia externos (SQL Server / API).
    Proporciona el contrato de solvencia para el dominio académico de cualquier centro educativo.
    """
    def __init__(self, connection_string=None, mock_responses=None):
        self.connection_string = connection_string
        self.mock_responses = mock_responses or {}

    def consultar_solvencia(self, codigo_estudiante, fecha=None):
        """
        Consulta la solvencia financiera de un estudiante en una fecha dada.
        Retorna uno de los 5 estados contractuales.
        Si la conexión falla o se produce un error, RETORNA 'DESCONOCIDO' obligatoriamente.
        """
        if not fecha:
            fecha = date.today()

        # Si existen respuestas simuladas para pruebas/entornos sin SQL Server
        if codigo_estudiante in self.mock_responses:
            return self.mock_responses[codigo_estudiante]

        if not self.connection_string:
            logger.warning(
                "SolvenciaExternaAdapter: No se ha configurado la cadena de conexión externa. Retornando DESCONOCIDO."
            )
            registrar_evento(
                accion="SOLVENCIA_EXTERNA_CONEXION_FALLIDA",
                objeto_tipo="Estudiante",
                objeto_id=codigo_estudiante,
                descripcion="Sin cadena de conexión configurada para servicio de solvencia externa",
                exito=False
            )
            return ESTADO_DESCONOCIDO

        try:
            # Intento de conexión mediante pyodbc
            import pyodbc
            with pyodbc.connect(self.connection_string, timeout=5) as conn:
                cursor = conn.cursor()
                query = """
                    SELECT TOP 1 estado_solvencia 
                    FROM solvencias 
                    WHERE codigo_estudiante = ? AND fecha_corte <= ?
                    ORDER BY fecha_corte DESC
                """
                cursor.execute(query, (codigo_estudiante, fecha))
                row = cursor.fetchone()
                if row and row[0] in ESTADOS_SOLVENCIA:
                    return row[0]
                elif row:
                    return ESTADO_DESCONOCIDO
                else:
                    return ESTADO_INSOLVENTE

        except Exception as e:
            logger.error(f"Error consultando solvencia externa para {codigo_estudiante}: {str(e)}")
            registrar_evento(
                accion="SOLVENCIA_EXTERNA_ERROR",
                objeto_tipo="Estudiante",
                objeto_id=codigo_estudiante,
                descripcion=f"Error en consulta externa SQL Server / API: {str(e)}",
                exito=False
            )
            return ESTADO_DESCONOCIDO


# Alias genérico para retrocompatibilidad
LoyolaSolvenciaAdapter = SolvenciaExternaAdapter
