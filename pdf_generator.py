import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line


def _obtener_color_heatmap(valor: float) -> colors.HexColor:
    """Asigna el color basado en el valor entero redondeado (0 a 3)."""
    val_entero = round(valor)
    if val_entero == 0:
        return colors.HexColor("#A3E4D7")  # Verde menta (Normal)
    elif val_entero == 1:
        return colors.HexColor("#F9E79F")  # Amarillo (Leve)
    elif val_entero == 2:
        return colors.HexColor("#EDBB99")  # Naranja (Moderado)
    else:
        return colors.HexColor("#F1948A")  # Rojo/Coral (Severo)


def generar_pdf_informe(df: pd.DataFrame) -> bytes:
    """Genera un informe clínico completo con KPIs, guía detallada, mapa de calor, barras con tendencia y tabla."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    story = []
    styles = getSampleStyleSheet()

    # --- Estilos de Texto ---
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#2C3E50"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=colors.HexColor("#7F8C8D"),
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#2C3E50"),
        spaceBefore=10,
        spaceAfter=6,
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#2C3E50"),
    )
    cell_style_bold = ParagraphStyle(
        "TableCellBold", parent=cell_style, fontName="Helvetica-Bold"
    )
    kpi_val_style = ParagraphStyle(
        "KpiVal",
        parent=styles["Normal"],
        fontSize=14,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#2C3E50"),
        alignment=1,
    )
    kpi_lbl_style = ParagraphStyle(
        "KpiLbl",
        parent=styles["Normal"],
        fontSize=7.5,
        textColor=colors.HexColor("#7F8C8D"),
        alignment=1,
    )

    # --- Encabezado ---
    story.append(Paragraph("📋 Informe Clínico de Seguimiento - Síndrome de Cushing", title_style))
    fecha_gen = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(f"Fecha de generación: {fecha_gen}", subtitle_style))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.2,
            color=colors.HexColor("#3498DB"),
            spaceAfter=8,
        )
    )

    if df.empty:
        story.append(
            Paragraph("No hay registros disponibles para el período seleccionado.", cell_style)
        )
    else:
        df_ord = df.sort_values("Fecha").copy()

        cols_sintomas = [
            "Poliuria / Polidipsia (0-3)",
            "Apetito (0-3)",
            "Aspecto General (0-3)",
            "Actitud (0-3)",
        ]
        
        df_ord["Total_Dia"] = df_ord[cols_sintomas].sum(axis=1)
        ultima_val = int(df_ord["Total_Dia"].iloc[-1])
        promedio_val = round(df_ord["Total_Dia"].mean(), 1)

        # ==============================================================================
        # 1. TARJETAS DE KPIs
        # ==============================================================================
        kpi_data = [
            [
                Paragraph("Última Valoración Global", kpi_lbl_style),
                Paragraph("Promedio en el Período", kpi_lbl_style)
            ],
            [
                Paragraph(f"{ultima_val} / 12", kpi_val_style),
                Paragraph(f"{promedio_val} / 12", kpi_val_style)
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[260, 260])
        kpi_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F9F9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ECF0F1")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(kpi_table)
        story.append(Spacer(1, 8))

        # ==============================================================================
        # 2. GUÍA DE PUNTUACIÓN CLÍNICA DETALLADA (Estilo Web)
        # ==============================================================================
        story.append(Paragraph("📖 Guía de Puntuación de Síntomas (Escala 0 a 3)", section_style))
        guia_headers = ["Indicador Clínico", "0 (Normal)", "1 (Leve)", "2 (Moderado)", "3 (Severo)"]
        guia_rows = [
            [Paragraph(h, cell_style_bold) for h in guia_headers],
            [Paragraph("<b>Poliuria / Polidipsia</b>", cell_style), Paragraph("Normal", cell_style), Paragraph("Aumento leve", cell_style), Paragraph("Aumento moderado", cell_style), Paragraph("Exceso severo", cell_style)],
            [Paragraph("<b>Apetito</b>", cell_style), Paragraph("Normal", cell_style), Paragraph("Ligeramente alto", cell_style), Paragraph("Muy hambriento", cell_style), Paragraph("Voraz / Ansiedad", cell_style)],
            [Paragraph("<b>Aspecto General</b>", cell_style), Paragraph("Pelo y piel sanos", cell_style), Paragraph("Pérdida leve pelo", cell_style), Paragraph("Alopecia / Abdomen", cell_style), Paragraph("Alopecia avanzada", cell_style)],
            [Paragraph("<b>Actitud</b>", cell_style), Paragraph("Activo y alegre", cell_style), Paragraph("Menos activo", cell_style), Paragraph("Apatía moderada", cell_style), Paragraph("Letargo severo", cell_style)],
        ]
        guia_table = Table(guia_rows, colWidths=[110, 102, 102, 103, 103])
        guia_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ECF0F1")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ])
        )
        story.append(guia_table)
        story.append(Spacer(1, 10))

        df_diario = (
            df_ord.groupby("Fecha", as_index=False)[cols_sintomas + ["Total_Dia"]]
            .mean()
            .sort_values("Fecha")
        )

        dias_sincronizados = 14
        df_sync = df_diario.tail(dias_sincronizados).copy()

        # ==============================================================================
        # 3. MAPA DE CALOR + LEYENDA INTEGREADA
        # ==============================================================================
        story.append(Paragraph("🔥 Mapa de Calor de Síntomas", section_style))
        
        leyenda_hm_data = [[
            Paragraph("<b>Leyenda Heatmap:</b>", cell_style_bold),
            Paragraph("0 - Normal", cell_style),
            Paragraph("1 - Leve", cell_style),
            Paragraph("2 - Moderado", cell_style),
            Paragraph("3 - Severo", cell_style),
        ]]
        leyenda_hm_table = Table(leyenda_hm_data, colWidths=[90, 105, 105, 110, 110])
        leyenda_hm_table.setStyle(
            TableStyle([
                ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#A3E4D7")),
                ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#F9E79F")),
                ("BACKGROUND", (3, 0), (3, 0), colors.HexColor("#EDBB99")),
                ("BACKGROUND", (4, 0), (4, 0), colors.HexColor("#F1948A")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ])
        )
        story.append(leyenda_hm_table)
        story.append(Spacer(1, 4))

        hm_headers = ["Síntoma"] + [
            d.strftime("%d/%m") if isinstance(d, pd.Timestamp) else str(d)[:5] 
            for d in df_sync["Fecha"]
        ]
        
        nombres_cortos = ["Poliuria/PD", "Apetito", "Aspecto Gen.", "Actitud"]
        hm_rows = [ [Paragraph(h, cell_style_bold) for h in hm_headers] ]
        
        tstyle_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ECF0F1")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]

        for s_idx, col_name in enumerate(cols_sintomas):
            row_cells = [Paragraph(nombres_cortos[s_idx], cell_style_bold)]
            for d_idx, (_, row) in enumerate(df_sync.iterrows()):
                val = float(row[col_name])
                row_cells.append(Paragraph(str(round(val, 1)), cell_style))
                bg_color = _obtener_color_heatmap(val)
                tstyle_cmds.append(("BACKGROUND", (d_idx + 1, s_idx + 1), (d_idx + 1, s_idx + 1), bg_color))
            hm_rows.append(row_cells)

        col_w = [90] + [31] * len(df_sync)
        hm_table = Table(hm_rows, colWidths=col_w)
        hm_table.setStyle(TableStyle(tstyle_cmds))
        story.append(hm_table)
        story.append(Spacer(1, 10))

        # ==============================================================================
        # 4. GRÁFICO DE BARRAS APILADAS + LEYENDA (CON TENDENCIA DESTACADA)
        # ==============================================================================
        story.append(Paragraph("📊 Composición Diaria y Tendencia de Severidad", section_style))

        d_width = 530
        d_height = 150
        drawing = Drawing(d_width, d_height)

        sintomas_info = [
            ("Poliuria / Polidipsia", colors.HexColor("#66C2A5")),
            ("Apetito", colors.HexColor("#FC8D62")),
            ("Aspecto General", colors.HexColor("#8DA0CB")),
            ("Actitud", colors.HexColor("#E78AC3")),
        ]

        # Leyenda de síntomas y de la línea de tendencia optimizada (5 elementos en total)
        leg_positions = [
            (30, 135),   # Poliuria
            (155, 135),  # Apetito
            (280, 135),  # Aspecto
            (395, 135),  # Actitud
            (30, 120)    # Línea de tendencia (color vistoso: Rojo/Coral fuerte)
        ]
        
        color_tendencia = colors.HexColor("#E74C3C") # Rojo vibrante

        for idx, (nombre, color_sintoma) in enumerate(sintomas_info):
            lx, ly = leg_positions[idx]
            drawing.add(Rect(lx, ly, 8, 8, fillColor=color_sintoma, strokeColor=colors.white, strokeWidth=0.5))
            drawing.add(String(lx + 12, ly + 1, nombre, fontSize=7.5, fillColor=colors.HexColor("#2C3E50")))

        # Añadir la leyenda de la línea de tendencia explícitamente
        lx_t, ly_t = leg_positions[4]
        drawing.add(Line(lx_t, ly_t + 4, lx_t + 12, ly_t + 4, strokeColor=color_tendencia, strokeWidth=2))
        drawing.add(String(lx_t + 16, ly_t + 1, "Tendencia Global", fontSize=7.5, fillColor=colors.HexColor("#2C3E50")))

        chart_x_start = 35
        chart_x_end = 510
        chart_y_base = 25
        chart_height = 80  # Ligeramente ajustado para dar respiro a la leyenda superior
        max_val = 12

        drawing.add(Line(chart_x_start, chart_y_base, chart_x_end, chart_y_base, strokeColor=colors.HexColor("#BDC3C7"), strokeWidth=1))
        drawing.add(Line(chart_x_start, chart_y_base, chart_x_start, chart_y_base + chart_height, strokeColor=colors.HexColor("#BDC3C7"), strokeWidth=1))

        for v in [0, 3, 6, 9, 12]:
            y_pos = chart_y_base + (v / max_val) * chart_height
            if v > 0:
                drawing.add(Line(chart_x_start, y_pos, chart_x_end, y_pos, strokeColor=colors.HexColor("#ECF0F1"), strokeWidth=0.5))
            drawing.add(String(18, y_pos - 3, str(v), fontSize=7, fillColor=colors.HexColor("#7F8C8D")))

        num_puntos = len(df_sync)
        trend_points = []

        if num_puntos > 0:
            available_w = chart_x_end - chart_x_start - 15
            bar_width = max(6, min(18, (available_w / num_puntos) - 4))
            spacing = (available_w - (num_puntos * bar_width)) / max(1, num_puntos - 1) if num_puntos > 1 else 0

            start_x = chart_x_start + 10
            
            y_totals = df_sync["Total_Dia"].values
            if num_puntos > 1:
                x_idx = list(range(num_puntos))
                sum_x = sum(x_idx)
                sum_y = sum(y_totals)
                sum_xy = sum(x * y for x, y in zip(x_idx, y_totals))
                sum_xx = sum(x * x for x in x_idx)
                den = num_puntos * sum_xx - sum_x**2
                m = (num_puntos * sum_xy - sum_x * sum_y) / den if den != 0 else 0
                c = (sum_y - m * sum_x) / num_puntos
            else:
                m = 0
                c = y_totals[0] if num_puntos > 0 else 0

            for i, row in enumerate(df_sync.itertuples()):
                x = start_x + i * (bar_width + spacing)
                valores = [row._2, row._3, row._4, row._5]
                current_y = chart_y_base
                
                for idx_v, val in enumerate(valores):
                    if val > 0:
                        h_val = (val / max_val) * chart_height
                        col = sintomas_info[idx_v][1]
                        drawing.add(Rect(x, current_y, bar_width, h_val, fillColor=col, strokeColor=colors.white, strokeWidth=0.5))
                        current_y += h_val

                x_center = x + (bar_width / 2)
                y_trend_val = m * i + c
                y_trend_val = max(0, min(max_val, y_trend_val))
                y_pixel = chart_y_base + (y_trend_val / max_val) * chart_height
                trend_points.append((x_center, y_pixel))

                fecha_val = row.Fecha
                fecha_str = fecha_val.strftime("%d/%m") if isinstance(fecha_val, pd.Timestamp) else str(fecha_val)[:5]
                drawing.add(String(x_center - 6, 12, fecha_str, fontSize=5.5, fillColor=colors.HexColor("#2C3E50")))

            for idx_p in range(len(trend_points) - 1):
                p1 = trend_points[idx_p]
                p2 = trend_points[idx_p + 1]
                drawing.add(Line(p1[0], p1[1], p2[0], p2[1], strokeColor=color_tendencia, strokeWidth=2))

        story.append(drawing)
        story.append(Spacer(1, 10))

        # ==============================================================================
        # 5. TABLA DETALLADA DE REGISTROS
        # ==============================================================================
        story.append(Paragraph("📝 Tabla Detallada de Registros", section_style))

        headers = [
            "Fecha",
            "Poliuria (0-3)",
            "Apetito (0-3)",
            "Aspecto (0-3)",
            "Actitud (0-3)",
            "Total",
            "Comentarios",
        ]
        table_data = [[Paragraph(h, cell_style_bold) for h in headers]]

        for _, row in df.iterrows():
            fecha_str = (
                row["Fecha"].strftime("%d/%m/%Y")
                if isinstance(row["Fecha"], pd.Timestamp)
                else str(row["Fecha"])
            )
            p = int(row["Poliuria / Polidipsia (0-3)"])
            ap = int(row["Apetito (0-3)"])
            as_ = int(row["Aspecto General (0-3)"])
            ac = int(row["Actitud (0-3)"])
            total = p + ap + as_ + ac
            obs = str(row["Comentarios"]) if pd.notnull(row["Comentarios"]) else ""

            table_data.append(
                [
                    Paragraph(fecha_str, cell_style),
                    Paragraph(str(p), cell_style),
                    Paragraph(str(ap), cell_style),
                    Paragraph(str(as_), cell_style),
                    Paragraph(str(ac), cell_style),
                    Paragraph(f"<b>{total}</b> / 12", cell_style),
                    Paragraph(obs, cell_style),
                ]
            )

        table = Table(table_data, colWidths=[60, 60, 60, 60, 60, 50, 180], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ECF0F1")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ]
            )
        )
        story.append(table)

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data