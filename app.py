import datetime
import hashlib
import os
import zoneinfo
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import text

# Cargar variables de entorno (.env)
load_dotenv()

st.set_page_config(page_title="Seguimiento Cushing Croqueta", layout="wide")

# --- Conexión a Neon PostgreSQL (Compatible local / Streamlit Cloud) ---
db_url = st.secrets.get("DATABASE_URL") or os.getenv("DATABASE_URL")

if not db_url:
  st.error(
      "No se encontró la variable DATABASE_URL en .env ni en los Secrets de"
      " Streamlit."
  )
  st.stop()

conn = st.connection("postgres", type="sql", url=db_url)


# --- Función para calcular hash SHA-256 de la contraseña ---
def hash_password(password: str) -> str:
  return hashlib.sha256(password.encode("utf-8")).hexdigest()


# --- Función de Autenticación contra Neon ---
def autenticar_usuario(username, password):
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
      row = result.fetchone()
      return row is not None
  except Exception as e:
    st.error(f"Error al autenticar con la base de datos: {e}")
    return False


# ==============================================================================
# GESTIÓN DE SESIÓN PERSISTENTE (Mediante URL)
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
          "Iniciar Sesión", use_container_width=True
      )

      if btn_login:
        if autenticar_usuario(usuario, password):
          st.session_state.autenticado = True
          st.session_state.usuario_actual = usuario

          # Persistir usuario en la URL para sobrevivir al refresco (F5)
          st.query_params["user"] = usuario

          st.success("Acceso concedido.")
          st.rerun()
        else:
          st.error("Usuario o contraseña incorrectos.")

  st.stop()


# ==============================================================================
# APLICACIÓN PRINCIPAL (Solo visible con sesión iniciada)
# ==============================================================================

# Barra lateral: Info de sesión y botón de cierre
st.sidebar.write(f"👤 Usuario: **{st.session_state.usuario_actual}**")
if st.sidebar.button("🚪 Cerrar Sesión"):
  st.session_state.autenticado = False
  st.session_state.usuario_actual = ""
  st.query_params.clear()
  st.rerun()

st.title("Seguimiento Cushing")

# Creación de Pestañas
tab_dashboard, tab_formulario = st.tabs(
    ["📊 Dashboard de Consulta", "📝 Nuevo Registro"]
)


# ==============================================================================
# PESTAÑA 1: DASHBOARD
# ==============================================================================
with tab_dashboard:
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
  df_raw = conn.query(query, ttl=0)

  df_filtrado = df_raw.copy()
  if not df_filtrado.empty:
    df_filtrado["Fecha"] = pd.to_datetime(df_filtrado["Fecha"])

  # --- Filtros de Fecha en Barra Lateral ---
  st.sidebar.header("🔍 Filtros de Consulta")
  opciones_periodo = [
      "Todo el historial",
      "Últimos 14 días",
      "Últimos 30 días",
      "Rango personalizado",
  ]
  seleccion = st.sidebar.selectbox("Seleccionar período:", opciones_periodo)

  if not df_filtrado.empty:
    fecha_max = df_filtrado["Fecha"].max()

    if seleccion == "Últimos 14 días":
      fecha_min = fecha_max - pd.Timedelta(days=14)
      df_filtrado = df_filtrado[df_filtrado["Fecha"] >= fecha_min]
    elif seleccion == "Últimos 30 días":
      fecha_min = fecha_max - pd.Timedelta(days=30)
      df_filtrado = df_filtrado[df_filtrado["Fecha"] >= fecha_min]
    elif seleccion == "Rango personalizado":
      rango = st.sidebar.date_input(
          "Rango de fechas",
          value=(df_filtrado["Fecha"].min().date(), fecha_max.date()),
          min_value=df_filtrado["Fecha"].min().date(),
          max_value=fecha_max.date(),
      )
      if isinstance(rango, tuple) and len(rango) == 2:
        df_filtrado = df_filtrado[
            (df_filtrado["Fecha"].dt.date >= rango[0])
            & (df_filtrado["Fecha"].dt.date <= rango[1])
        ]

    # Agrupación diaria
    df_filtrado["Fecha_Corta"] = df_filtrado["Fecha"].dt.date

    df_diario = df_filtrado.groupby("Fecha_Corta", as_index=False)[[
        "Poliuria / Polidipsia (0-3)",
        "Apetito (0-3)",
        "Aspecto General (0-3)",
        "Actitud (0-3)",
    ]].mean()

    df_diario["Fecha_Texto"] = pd.to_datetime(
        df_diario["Fecha_Corta"]
    ).dt.strftime("%d %b")

    df_diario["Total Diario"] = df_diario.iloc[:, 1:5].sum(axis=1)
    df_filtrado["Total Diario"] = df_filtrado.iloc[:, 1:5].sum(axis=1)

    # --- Métricas principales ---
    col1, col2 = st.columns(2)
    ultimo_total = (
        df_filtrado["Total Diario"].iloc[-1] if not df_filtrado.empty else 0
    )
    promedio_total = (
        df_filtrado["Total Diario"].mean() if not df_filtrado.empty else 0
    )

    col1.metric("Última valoración (Total)", f"{ultimo_total:.0f} / 12")
    col2.metric("Promedio en el período", f"{promedio_total:.1f} / 12")

    st.write("---")

    # --- Guía Clínica ---
    with st.expander("ℹ️ Ver guía de puntuaciones y significado clínico"):
      col_a, col_b = st.columns(2)
      with col_a:
        st.markdown("""
                **Poliuria / Polidipsia (Sed y Orina)**
                * **0:** Bebe y orina una cantidad normal
                * **1:** Es posible que bebe y orine más
                * **2:** Bebe y orine más
                * **3:** Bebe y orine de forma constante

                **Apetito**
                * **0:** Come una cantidad normal
                * **1:** Se termina la comida rápido
                * **2:** Se termina la comida rápido y pide más
                * **3:** Obsesionado con la comida más que nunca
                """)
      with col_b:
        st.markdown("""
                **Aspecto General**
                * **0:** Aspecto normal
                * **1:** Algo menos de pelo y mala calidad de piel
                * **2:** Poco pelo +/- algo de panza
                * **3:** Muy poco pelo +/- panza

                **Actitud**
                * **0:** Actitud y actividad normales
                * **1:** No termina de ser el mismo
                * **2:** No es el mismo +/- jadeo en reposo
                * **3:** No es el mismo, débil +/- jadeo constante
                """)

    st.write("---")

    # --- Gráfico de Barras Apiladas con Tendencia ---
    df_melted = df_diario.melt(
        id_vars=["Fecha_Texto", "Fecha_Corta"],
        value_vars=[
            "Poliuria / Polidipsia (0-3)",
            "Apetito (0-3)",
            "Aspecto General (0-3)",
            "Actitud (0-3)",
        ],
        var_name="Sintoma",
        value_name="Valor",
    )

    st.subheader("Composición Diaria de Síntomas")

    fig_barras = px.bar(
        df_melted,
        x="Fecha_Texto",
        y="Valor",
        color="Sintoma",
        title="Puntuación Acumulada por Día con Recta de Tendencia",
        labels={
            "Valor": "Puntuación por síntoma",
            "Fecha_Texto": "Fecha",
            "Sintoma": "Síntoma",
        },
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    if len(df_diario) > 1:
      x_indices = np.arange(len(df_diario))
      y_valores = df_diario["Total Diario"].values
      m, b = np.polyfit(x_indices, y_valores, 1)
      linea_tendencia = m * x_indices + b

      fig_barras.add_trace(
          go.Scatter(
              x=df_diario["Fecha_Texto"],
              y=linea_tendencia,
              mode="lines",
              name="Tendencia Global",
              line=dict(color="red", width=3, dash="dash"),
          )
      )

    fig_barras.update_xaxes(
        categoryorder="array", categoryarray=df_diario["Fecha_Texto"]
    )
    fig_barras.update_yaxes(range=[0, 12])
    st.plotly_chart(fig_barras, use_container_width=True)

    st.write("---")

    # --- Mapa de Calor (Heatmap) ---
    st.subheader("Matriz de Intensidad por Síntoma (Heatmap)")
    columnas_sintomas = [
        "Poliuria / Polidipsia (0-3)",
        "Apetito (0-3)",
        "Aspecto General (0-3)",
        "Actitud (0-3)",
    ]

    matriz_heatmap = df_diario.set_index("Fecha_Texto")[columnas_sintomas].T

    fig_heatmap = px.imshow(
        matriz_heatmap,
        labels=dict(x="Fecha", y="Síntoma", color="Grado (0-3)"),
        x=matriz_heatmap.columns,
        y=matriz_heatmap.index,
        color_continuous_scale=["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"],
        range_color=[0, 3],
        text_auto=True,
    )

    fig_heatmap.update_xaxes(
        categoryorder="array", categoryarray=df_diario["Fecha_Texto"]
    )
    fig_heatmap.update_layout(height=350)
    st.plotly_chart(fig_heatmap, use_container_width=True)

    st.write("---")
    st.write("### Tabla de datos filtrada (Neon DB)")
    st.dataframe(df_filtrado.drop(columns=["Fecha_Corta"]))
  else:
    st.info(
        "No hay datos disponibles en la base de datos para mostrar el"
        " dashboard."
    )


# ==============================================================================
# PESTAÑA 2: FORMULARIO DE NUEVO REGISTRO
# ==============================================================================
with tab_formulario:
  st.subheader("📝 Registrar nuevo estado diario")
  st.write(
      "Selecciona los valores observados para guardar la entrada en la base de datos. "
  )

  # Fecha y hora actual ajustadas a la zona horaria de España (Europe/Madrid)
  zona_horaria = zoneinfo.ZoneInfo("Europe/Madrid")
  ahora = datetime.datetime.now(zona_horaria)

  with st.form("form_cushing", clear_on_submit=True):
    col_f1, col_f2 = st.columns(2)

    with col_f1:
      fecha_registro = st.date_input("Fecha del registro", value=ahora.date())
      hora_registro = st.time_input("Hora del registro", value=ahora.time())

      num_poliuria_polidipsia = st.selectbox(
          "Poliuria / Polidipsia (Sed y Orina)",
          options=[0, 1, 2, 3],
          format_func=lambda x: {
              0: "0: Bebe y orina una cantidad normal",
              1: "1: Es posible que bebe y orine más",
              2: "2: Bebe y orine más",
              3: "3: Bebe y orine de forma constante",
          }[x],
      )

      num_apetito = st.selectbox(
          "Apetito",
          options=[0, 1, 2, 3],
          format_func=lambda x: {
              0: "0: Come una cantidad normal",
              1: "1: Se termina la comida rápido",
              2: "2: Se termina la comida rápido y pide más",
              3: "3: Obsesionado con la comida más que nunca",
          }[x],
      )

    with col_f2:
      num_aspecto_general = st.selectbox(
          "Aspecto General",
          options=[0, 1, 2, 3],
          format_func=lambda x: {
              0: "0: Aspecto normal",
              1: "1: Algo menos de pelo y mala calidad de piel",
              2: "2: Poco pelo +/- algo de panza",
              3: "3: Muy poco pelo +/- panza",
          }[x],
      )

      num_actitud = st.selectbox(
          "Actitud",
          options=[0, 1, 2, 3],
          format_func=lambda x: {
              0: "0: Actitud y actividad normales",
              1: "1: No termina de ser el mismo",
              2: "2: No es el mismo +/- jadeo en reposo",
              3: "3: No es el mismo, débil +/- jadeo constante",
          }[x],
      )

      comentarios = st.text_area(
          "Comentarios u observaciones adicionales",
          placeholder="Ej: Cambio de dosis, apetito algo menor por la mañana...",
      )

    submitted = st.form_submit_button(
        "💾 Guardar Registro en Neon", use_container_width=True
    )

    if submitted:
      fecha_hora_combinada = datetime.datetime.combine(
          fecha_registro, hora_registro
      )

      insert_sql = text("""
                INSERT INTO seguimiento_cushing (
                    fecha, 
                    num_poliuria_polidipsia, 
                    num_apetito, 
                    num_aspecto_general, 
                    num_actitud, 
                    comentarios,
                    usuario
                ) VALUES (
                    :fecha, 
                    :poliuria, 
                    :apetito, 
                    :aspecto, 
                    :actitud, 
                    :comentarios,
                    :usuario
                );
            """)

      try:
        with conn.session as session:
          session.execute(
              insert_sql,
              params={
                  "fecha": fecha_hora_combinada,
                  "poliuria": num_poliuria_polidipsia,
                  "apetito": num_apetito,
                  "aspecto": num_aspecto_general,
                  "actitud": num_actitud,
                  "comentarios": comentarios,
                  "usuario": st.session_state.usuario_actual,
              },
          )
          session.commit()

        st.success(
            "✅ Registro guardado con éxito con fecha"
            f" {fecha_hora_combinada.strftime('%d/%m/%Y %H:%M')} por"
            f" **{st.session_state.usuario_actual}**."
        )

      except Exception as e:
        st.error(f"❌ Error al guardar el registro: {e}")