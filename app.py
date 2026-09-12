from auth import autenticar_usuario
import streamlit as st
from views.dashboard import render_dashboard
from views.formulario import render_formulario

st.set_page_config(page_title="Seguimiento Cushing", layout="wide")

# ==============================================================================
# GESTIÓN DE SESIÓN PERSISTENTE
# ==============================================================================
usuario_en_url = st.query_params.get("user", None)

if usuario_en_url:
  st.session_state.autenticado = True
  st.session_state.usuario_actual = usuario_en_url
elif "autenticado" not in st.session_state:
  st.session_state.autenticado = False
  st.session_state.usuario_actual = ""


# ==============================================================================
# PANTALLA DE LOGIN
# ==============================================================================
if not st.session_state.autenticado:
  st.title("🔒 Acceso a Seguimiento Cushing")

  col_login, _ = st.columns([1, 1])
  with col_login:
    with st.form("form_login"):
      usuario = st.text_input("Usuario")
      password = st.text_input("Contraseña", type="password")
      btn_login = st.form_submit_button(
          "Iniciar Sesión", width="stretch"
      )

      if btn_login:
        if autenticar_usuario(usuario, password):
          st.session_state.autenticado = True
          st.session_state.usuario_actual = usuario
          st.query_params["user"] = usuario
          st.success("Acceso concedido.")
          st.rerun()
        else:
          st.error("Usuario o contraseña incorrectos.")

  st.stop()


# ==============================================================================
# APLICACIÓN PRINCIPAL
# ==============================================================================
st.sidebar.write(f"👤 Usuario: **{st.session_state.usuario_actual}**")
if st.sidebar.button("🚪 Cerrar Sesión"):
  st.session_state.autenticado = False
  st.session_state.usuario_actual = ""
  st.query_params.clear()
  st.rerun()

st.title("Seguimiento Cushing")

tab_dashboard, tab_formulario = st.tabs(
    ["📊 Dashboard de Consulta", "📝 Nuevo Registro"]
)



with tab_dashboard:
  render_dashboard()

with tab_formulario:
  render_formulario()