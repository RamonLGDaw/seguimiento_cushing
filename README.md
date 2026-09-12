# 🐾 Sistema de Seguimiento Clínico - Síndrome de Cushing

[![Documentación](https://img.shields.io/badge/📖_Documentación-Ver_en_mi_Portafolio-blue?style=for-the-badge)](https://lagidev.com/proyectos/cushing-streamlit-1/)

Aplicación web interactiva desarrollada con **Streamlit** y **Python** para el registro, visualización y seguimiento diario de los síntomas asociados al Síndrome de Cushing en pacientes veterinarios.

Permite a propietarios y veterinarios monitorizar la evolución sintomática en tiempo real mediante métricas clave, gráficos interactivos y exportación de informes clínicos vectoriales en PDF.

---

## Características Principales

- **Registro Diario de Síntomas:** Formulario intuitivo para calificar los cuatro indicadores clínicos principales en una escala de 0 a 3:
  - Poliuria / Polidipsia (PU/PD)
  - Apetito
  - Aspecto General
  - Actitud / Nivel de Actividad
- **Panel de Control Interactivo (Dashboard):**
  - Métricas acumuladas y promedios por síntoma.
  - Gráficos de evolución temporal apilados para evaluar la severidad diaria (sobre un máximo de 12 puntos).
  - Filtros flexibles por rangos de fecha (Últimos 7 días, 14 días, 30 días o Histórico completo).
- **Exportación de Informes Clínicos en PDF:** Generación dinámica de informes en formato PDF vectorial usando **ReportLab**, incluyendo:
  - Gráfico de barras apiladas nativo con leyenda de colores integrada.
  - Tabla detallada de registros históricos y comentarios del propietario.
  - Preparado para impresión o envío por correo electrónico al equipo veterinario.
- **Persistencia de Datos:** Almacenamiento estructurado de registros mediante **SQLite** / **Pandas**.

---

## Tecnologías Utilizadas

- **Lenguaje:** Python 3.12+
- **Framework Web:** [Streamlit](https://streamlit.io/)
- **Procesamiento de Datos:** [Pandas](https://pandas.pydata.org/)
- **Generación de Documentos:** [ReportLab](https://www.reportlab.com/) (Gráficos vectoriales nativos)
- **Base de Datos:** SQLite

---

## Estructura del Proyecto

```text
├── app.py                  # Punto de entrada de la aplicación Streamlit
├── database.py             # Gestión y conexión con la base de datos SQLite
├── pdf_generator.py        # Módulo de generación del informe PDF con ReportLab
├── views/                  # Vistas/Módulos de la interfaz de usuario
│   ├── dashboard.py        # Visualización de métricas, gráficos y descarga de PDF
│   └── formulario.py       # Interfaz para el ingreso diario de datos
├── requirements.txt        # Dependencias del proyecto
└── README.md               # Documentación del proyecto
```

---

## Instalación y Ejecución Local

Sigue estos pasos para ejecutar el proyecto en tu entorno local:

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/project_grafica_cushing_streamlit.git
cd project_grafica_cushing_streamlit
```

### 2. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 3. Iniciar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador web en [http://localhost:8501](http://localhost:8501).

---

## Licencia

Este proyecto se distribuye bajo la licencia [MIT](https://opensource.org/licenses/MIT). Puedes modificar esta sección según la licencia que corresponda a tu proyecto.



