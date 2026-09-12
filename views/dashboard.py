import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from db import obtener_historial_seguimiento
from pdf_generator import generar_pdf_informe


def render_dashboard():
  df_raw = obtener_historial_seguimiento()
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

    # --- Métricas y Botón PDF ---
    col1, col2, col3 = st.columns([1, 1, 1])

    ultimo_total = (
        df_filtrado["Total Diario"].iloc[-1] if not df_filtrado.empty else 0
    )
    promedio_total = (
        df_filtrado["Total Diario"].mean() if not df_filtrado.empty else 0
    )

    col1.metric("Última valoración (Total)", f"{ultimo_total:.0f} / 12")
    col2.metric("Promedio en el período", f"{promedio_total:.1f} / 12")

    # Generación y descarga de PDF en memoria
    pdf_bytes = generar_pdf_informe(df_filtrado)
    col3.download_button(
        label="📄 Descargar Informe PDF",
        data=pdf_bytes,
        file_name=f"informe_cushing_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        width="stretch",
    )

    st.write("---")

    # --- Gráfico de Barras ---
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
    st.plotly_chart(fig_barras, width="stretch")

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
    st.plotly_chart(fig_heatmap, width="stretch")

    st.write("---")
    st.write("### Tabla de datos filtrada (Neon DB)")
    st.dataframe(df_filtrado.drop(columns=["Fecha_Corta"]))
  else:
    st.info(
        "No hay datos disponibles en la base de datos para mostrar el"
        " dashboard."
    )