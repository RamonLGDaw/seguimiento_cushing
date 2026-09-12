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


def generar_pdf_informe(df: pd.DataFrame) -> bytes:
    """Genera un informe PDF estilizado que incluye tabla de datos y gráfico vectorial de barras apiladas con leyenda."""
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
        fontSize=18,
        textColor=colors.HexColor("#2C3E50"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#7F8C8D"),
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#2C3E50"),
        spaceBefore=10,
        spaceAfter=8,
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#2C3E50"),
    )
    cell_style_bold = ParagraphStyle(
        "TableCellBold", parent=cell_style, fontName="Helvetica-Bold"
    )

    # --- Encabezado ---
    story.append(Paragraph("📋 Informe Clínico de Seguimiento - Cushing", title_style))
    fecha_gen = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(f"Fecha de generación: {fecha_gen}", subtitle_style))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#3498DB"),
            spaceAfter=10,
        )
    )

    if df.empty:
        story.append(
            Paragraph("No hay registros disponibles para el período seleccionado.", cell_style)
        )
    else:
        # Agrupar por fecha
        df_diario = (
            df.groupby("Fecha", as_index=False)[
                [
                    "Poliuria / Polidipsia (0-3)",
                    "Apetito (0-3)",
                    "Aspecto General (0-3)",
                    "Actitud (0-3)",
                ]
            ]
            .mean()
            .sort_values("Fecha")
        )

        story.append(Paragraph("📊 Composición Diaria de Síntomas", section_style))

        # ==============================================================================
        # GRÁFICO VECTORIAL DE BARRAS APILADAS + LEYENDA EN CABECERA (ReportLab Nativo)
        # ==============================================================================
        d_width = 530
        d_height = 170
        drawing = Drawing(d_width, d_height)

        # Configuración de Sintomas / Leyenda
        sintomas_info = [
            ("Poliuria / Polidipsia (0-3)", colors.HexColor("#66C2A5")),
            ("Apetito (0-3)", colors.HexColor("#FC8D62")),
            ("Aspecto General (0-3)", colors.HexColor("#8DA0CB")),
            ("Actitud (0-3)", colors.HexColor("#E78AC3")),
        ]

        # --- DIBUJAR LEYENDA HORIZONTAL EN LA PARTE SUPERIOR (y = 152) ---
        # 2 elementos por fila en 2 columnas para no apretar el texto demasiado
        leg_positions = [(35, 155), (260, 155), (35, 140), (260, 140)]
        for idx, (nombre, color_sintoma) in enumerate(sintomas_info):
            lx, ly = leg_positions[idx]
            drawing.add(Rect(lx, ly, 10, 10, fillColor=color_sintoma, strokeColor=colors.white, strokeWidth=0.5))
            drawing.add(String(lx + 15, ly + 2, nombre, fontSize=8, fillColor=colors.HexColor("#2C3E50")))

        # Límites del área del gráfico de barras
        chart_x_start = 35
        chart_x_end = 510
        chart_y_base = 25
        chart_height = 95
        max_val = 12

        # Ejes base
        drawing.add(Line(chart_x_start, chart_y_base, chart_x_end, chart_y_base, strokeColor=colors.HexColor("#BDC3C7"), strokeWidth=1))
        drawing.add(Line(chart_x_start, chart_y_base, chart_x_start, chart_y_base + chart_height, strokeColor=colors.HexColor("#BDC3C7"), strokeWidth=1))

        # Líneas de referencia y marcas en el Eje Y (0 a 12)
        for v in [0, 3, 6, 9, 12]:
            y_pos = chart_y_base + (v / max_val) * chart_height
            if v > 0:
                drawing.add(Line(chart_x_start, y_pos, chart_x_end, y_pos, strokeColor=colors.HexColor("#ECF0F1"), strokeWidth=0.5))
            drawing.add(String(18, y_pos - 3, str(v), fontSize=7, fillColor=colors.HexColor("#7F8C8D")))

        # Límite de días visibles en la gráfica (ajustable)
        max_dias_grafica = 14
        if len(df_diario) > max_dias_grafica:
            df_diario = df_diario.tail(max_dias_grafica)

        num_puntos = len(df_diario)
        if num_puntos > 0:
            available_w = chart_x_end - chart_x_start - 15
            bar_width = max(10, min(24, (available_w / num_puntos) - 6))
            spacing = (available_w - (num_puntos * bar_width)) / max(1, num_puntos - 1) if num_puntos > 1 else 0

            start_x = chart_x_start + 10
            for i, row in enumerate(df_diario.itertuples()):
                x = start_x + i * (bar_width + spacing)
                
                valores = [row._2, row._3, row._4, row._5]
                current_y = chart_y_base
                
                for idx_v, val in enumerate(valores):
                    if val > 0:
                        h_val = (val / max_val) * chart_height
                        col = sintomas_info[idx_v][1]
                        drawing.add(Rect(
                            x, current_y, bar_width, h_val, 
                            fillColor=col, 
                            strokeColor=colors.white, 
                            strokeWidth=0.5
                        ))
                        current_y += h_val

                # Fecha en el Eje X
                fecha_val = row.Fecha
                fecha_str = fecha_val.strftime("%d/%m") if isinstance(fecha_val, pd.Timestamp) else str(fecha_val)[:5]
                drawing.add(String(x + (bar_width / 2) - 8, 12, fecha_str, fontSize=6.5, fillColor=colors.HexColor("#2C3E50")))

        story.append(drawing)
        story.append(Spacer(1, 15))

        # ==============================================================================
        # TABLA DETALLADA DE REGISTROS
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
        data = [[Paragraph(h, cell_style_bold) for h in headers]]

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

            data.append(
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

        table = Table(data, colWidths=[65, 60, 60, 60, 60, 55, 170], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ECF0F1")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ]
            )
        )
        story.append(table)

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data