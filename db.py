import datetime
from config import get_db_connection
import pandas as pd
from sqlalchemy import text


def obtener_historial_seguimiento() -> pd.DataFrame:
  """Obtiene todos los registros de seguimiento desde Neon DB."""
  conn = get_db_connection()
  query = """
        SELECT 
            fecha AS "Fecha",
            num_poliuria_polidipsia AS "Poliuria / Polidipsia (0-3)",
            num_apetito AS "Apetito (0-3)",
            num_aspecto_general AS "Aspecto General (0-3)",
            num_actitud AS "Actitud (0-3)",
            comentarios AS "Comentarios",
            usuario AS "Registrado Por"
        FROM seguimiento_cushing
        ORDER BY fecha ASC;
    """
  return conn.query(query, ttl=0)


def guardar_registro(
    fecha_hora: datetime.datetime,
    poliuria: int,
    apetito: int,
    aspecto: int,
    actitud: int,
    comentarios: str,
    usuario: str,
) -> bool:
  """Inserta una nueva entrada diaria en la base de datos."""
  conn = get_db_connection()
  insert_sql = text("""
        INSERT INTO seguimiento_cushing (
            fecha, num_poliuria_polidipsia, num_apetito, 
            num_aspecto_general, num_actitud, comentarios, usuario
        ) VALUES (
            :fecha, :poliuria, :apetito, :aspecto, :actitud, :comentarios, :usuario
        );
    """)

  try:
    with conn.session as session:
      session.execute(
          insert_sql,
          params={
              "fecha": fecha_hora,
              "poliuria": poliuria,
              "apetito": apetito,
              "aspecto": aspecto,
              "actitud": actitud,
              "comentarios": comentarios,
              "usuario": usuario,
          },
      )
      session.commit()
    return True
  except Exception as e:
    print(f"Error al insertar registro: {e}")
    return False