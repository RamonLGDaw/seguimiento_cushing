import datetime
import zoneinfo
import streamlit as st
from db import guardar_registro


def render_formulario():
  st.subheader("📝 Registrar nuevo estado diario")
  st.write(
      "Selecciona los valores observados para guardar la entrada en Neon.tech."
  )

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
        "💾 Guardar Registro en Neon", width="stretch"
    )

    if submitted:
      fecha_hora_combinada = datetime.datetime.combine(
          fecha_registro, hora_registro
      )
      usuario_actual = st.session_state.get("usuario_actual", "Desconocido")

      exito = guardar_registro(
          fecha_hora=fecha_hora_combinada,
          poliuria=num_poliuria_polidipsia,
          apetito=num_apetito,
          aspecto=num_aspecto_general,
          actitud=num_actitud,
          comentarios=comentarios,
          usuario=usuario_actual,
      )

      if exito:
        st.success(
            "✅ Registro guardado con éxito con fecha"
            f" {fecha_hora_combinada.strftime('%d/%m/%Y %H:%M')} por"
            f" **{usuario_actual}**."
        )
      else:
        st.error("❌ Error al guardar el registro en la base de datos.")