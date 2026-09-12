import hashlib
from config import get_db_connection
from sqlalchemy import text


def hash_password(password: str) -> str:
  """Calcula el hash SHA-256 de una contraseña."""
  return hashlib.sha256(password.encode("utf-8")).hexdigest()


def autenticar_usuario(username: str, password: str) -> bool:
  """Verifica las credenciales del usuario contra la base de datos."""
  conn = get_db_connection()
  password_hashed = hash_password(password)

  query = text("""
        SELECT id 
        FROM usuarios 
        WHERE LOWER(username) = LOWER(:username) 
          AND password_hash = :password_hash;
    """)

  try:
    with conn.session as session:
      result = session.execute(
          query,
          params={"username": username, "password_hash": password_hashed},
      )
      return result.fetchone() is not None
  except Exception as e:
    print(f"Error al autenticar: {e}")
    return False