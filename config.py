import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()


def get_db_connection():
  """Obtiene la conexión a PostgreSQL compatible con local y Streamlit Cloud."""
  db_url = os.getenv("DATABASE_URL")

  if not db_url:
    st.error(
        "No se encontró la variable DATABASE_URL en .env"
    )
    st.stop()

  return st.connection("postgres", type="sql", url=db_url)