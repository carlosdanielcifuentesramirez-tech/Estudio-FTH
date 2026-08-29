
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import Wedge, Circle
from matplotlib.lines import Line2D
from PIL import Image
import io
import base64
import math

# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Análisis de cargas del vehículo",
    page_icon="🚐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# ESTILO
# ============================================================

st.markdown("""
<style>
    .main .block-container {
        max-width: 1320px;
        padding-top: 20px;
        padding-left: 25px;
        padding-right: 25px;
    }

    h1, h2, h3 {
        color: #17365D !important;
    }

    .control-title {
        color: #17365D;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 8px;
    }

    .section-button {
        width: 100%;
    }

    div[data-testid="stNumberInput"] label,
    div[data-testid="stSlider"] label {
        font-weight: bold;
    }

    .result-box {
        border: 1px solid lightgray;
        padding: 10px;
        font-family: Arial, sans-serif;
        font-size: 14px;
        line-height: 1.45;
        white-space: pre-wrap;
    }

    .dimension-table {
        border: 1px solid lightgray;
        padding: 5px;
        width: 355px;
    }

    .small-note {
        color: #666;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONSTANTES
# ============================================================

ESCALA_IMAGEN_DIMENSIONES = 0.35

POS_X_LONGITUD_TOTAL = 430
POS_Y_LONGITUD_TOTAL = 280
POS_X_LONGITUD_CABINA = 320
POS_Y_LONGITUD_CABINA = 15
POS_X_ALTO_TOTAL = 210
POS_Y_ALTO_TOTAL = 110
POS_X_ANCHO_TOTAL = 80
POS_Y_ANCHO_TOTAL = 275
POS_X_DISTANCIA_EJES = 430
POS_Y_DISTANCIA_EJES = 260
POS_X_VOLADIZO_ANTERIOR = 260
POS_Y_VOLADIZO_ANTERIOR = 260
POS_X_VOLADIZO_POSTERIOR = 650
POS_Y_VOLADIZO_POSTERIOR = 260
POS_X_LONGITUD_BASTIDOR = 540
POS_Y_LONGITUD_BASTIDOR = 15
POS_X_ALTO_CARROCERIA = 725
POS_Y_ALTO_CARROCERIA = 100

COLOR_DIMENSIONES = "#17365D"
TAMANO_DIMENSIONES = 10

# Dimensiones iniciales
longitud_total_inicial = 5990
longitud_cabina_inicial = 2520
alto_total_inicial = 2645
ancho_total_inicial = 2098
distancia_entre_ejes_inicial = 3500
voladizo_anterior_inicial = 990
voladizo_posterior_inicial = 1430
longitud_sobre_bastidor_inicial = 3470
alto_carroceria_inicial = 1930

# Carrocería
peso_carroceria_eje_delantero_inicial = 1395
peso_carroceria_eje_trasero_inicial = 1155

# Pasajeros
numero_pasajeros_inicial = 2
peso_por_pasajero = 70
cg_pasajeros = 1000

# Carga
carga_inicial = 739

# Capacidades
capacidad_eje_delantero = 1750
capacidad_eje_trasero = 3000

# Coordenadas de los ejes en la imagen
x1, y1 = 186, 516
x2, y2 = 900, 525

# Coordenadas verticales
y_cg_vehiculo_imagen = 238
y_cg_carga_imagen = 250
y_cg_pasajeros_imagen = 330

# ============================================================
# FUNCIONES DE CÁLCULO
# ============================================================

def mm_a_pixel_x(posicion_mm, distancia_entre_ejes):
    if distancia_entre_ejes <= 0:
        return x1
    return x1 + (posicion_mm / distancia_entre_ejes) * (x2 - x1)


def color_gauge(valor):
    if valor < 80:
        return "#D9A900"
    elif valor < 100:
        return "green"
    return "red"


def calcular_resultados(
    numero_pasajeros,
    carga,
    peso_carroceria_eje_delantero,
    peso_carroceria_eje_trasero,
    longitud_cabina,
    voladizo_anterior,
    longitud_sobre_bastidor,
    distancia_entre_ejes,
):
    if distancia_entre_ejes <= 0:
        distancia_entre_ejes = 1

    cg_carga = (
        longitud_cabina
        - voladizo_anterior
        + longitud_sobre_bastidor / 2
    )

    peso_carroceria = (
        peso_carroceria_eje_delantero
        + peso_carroceria_eje_trasero
    )

    if peso_carroceria > 0:
        cg_vehiculo_carrozado = (
            distancia_entre_ejes * peso_carroceria_eje_trasero
        ) / peso_carroceria
    else:
        cg_vehiculo_carrozado = 0

    peso_pasajeros = numero_pasajeros * peso_por_pasajero

    peso_pasajeros_eje_trasero = (
        peso_pasajeros * cg_pasajeros / distancia_entre_ejes
    )

    peso_pasajeros_eje_delantero = (
        peso_pasajeros - peso_pasajeros_eje_trasero
    )

    peso_carga_eje_trasero = (
        carga * cg_carga / distancia_entre_ejes
    )

    peso_carga_eje_delantero = (
        carga - peso_carga_eje_trasero
    )

    peso_total_eje_delantero = (
        peso_carroceria_eje_delantero
        + peso_pasajeros_eje_delantero
        + peso_carga_eje_delantero
    )

    peso_total_eje_trasero = (
        peso_carroceria_eje_trasero
        + peso_pasajeros_eje_trasero
        + peso_carga_eje_trasero
    )

    peso_total = peso_carroceria + peso_pasajeros + carga

    utilizacion_delantera = (
        peso_total_eje_delantero / capacidad_eje_delantero
    ) * 100

    utilizacion_trasera = (
        peso_total_eje_trasero / capacidad_eje_trasero
    ) * 100

    return {
        "cg_carga": cg_carga,
        "peso_carroceria": peso_carroceria,
        "cg_vehiculo_carrozado": cg_vehiculo_carrozado,
        "peso_pasajeros": peso_pasajeros,
        "peso_pasajeros_eje_delantero": peso_pasajeros_eje_delantero,
        "peso_pasajeros_eje_trasero": peso_pasajeros_eje_trasero,
        "peso_carga_eje_delantero": peso_carga_eje_delantero,
        "peso_carga_eje_trasero": peso_carga_eje_trasero,
        "peso_total_eje_delantero": peso_total_eje_delantero,
        "peso_total_eje_trasero": peso_total_eje_trasero,
        "peso_total": peso_total,
        "utilizacion_delantera": utilizacion_delantera,
        "utilizacion_trasera": utilizacion_trasera,
    }


# ============================================================
# GAUGE
# ============================================================

def crear_gauge(ax_gauge, valor, titulo):
    ax_gauge.set_aspect("equal")
    ax_gauge.set_xlim(-1.20, 1.20)
    ax_gauge.set_ylim(-0.22, 1.18)
    ax_gauge.axis("off")

    ax_gauge.text(
        0, 1.05, titulo,
        ha="center", va="center",
        fontsize=8.5, fontweight="bold"
    )

    ax_gauge.add_patch(Wedge(
        (0, 0), 1.0, 60, 180,
        width=0.18, facecolor="#D9A900",
        edgecolor="white", linewidth=1.5
    ))

    ax_gauge.add_patch(Wedge(
        (0, 0), 1.0, 30, 60,
        width=0.18, facecolor="green",
        edgecolor="white", linewidth=1.5
    ))

    ax_gauge.add_patch(Wedge(
        (0, 0), 1.0, 0, 30,
        width=0.18, facecolor="red",
        edgecolor="white", linewidth=1.5
    ))

    valor_limitado = max(0, min(valor, 120))
    angulo = 180 - (valor_limitado / 120) * 180
    rad = math.radians(angulo)

    ax_gauge.add_line(Line2D(
        [0, 0.80 * math.cos(rad)],
        [0, 0.80 * math.sin(rad)],
        linewidth=2.8,
        color="black",
        solid_capstyle="round",
        zorder=8
    ))

    ax_gauge.add_patch(Circle(
        (0, 0), 0.065,
        facecolor="black",
        edgecolor="white",
        linewidth=1,
        zorder=10
    ))

    for angulo_marca, texto in [
        (180, "0%"),
        (60, "80%"),
        (30, "100%"),
        (0, "120%"),
    ]:
        rad_marca = math.radians(angulo_marca)
        ax_gauge.text(
            1.10 * math.cos(rad_marca),
            1.10 * math.sin(rad_marca),
            texto,
            ha="center", va="center",
            fontsize=5.5,
            color="dimgray",
            fontweight="bold"
        )

    ax_gauge.text(
        0, 0.26, f"{valor:.0f}%",
        ha="center", va="center",
        fontsize=13, fontweight="bold",
        color=color_gauge(valor)
    )

    ax_gauge.text(
        0, 0.06, "Utilización",
        ha="center", va="center",
        fontsize=5.5, color="dimgray"
    )

    if valor >= 100:
        estado, color_estado = "SOBRECARGA", "red"
    elif valor >= 80:
        estado, color_estado = "ÓPTIMO", "green"
    else:
        estado, color_estado = "DISPONIBLE", "#D9A900"

    ax_gauge.text(
        0, -0.13, estado,
        ha="center", va="center",
        fontsize=6.5, fontweight="bold",
        color=color_estado
    )


# ============================================================
# IMAGEN DE DIMENSIONES
# ============================================================

def crear_imagen_dimensiones_html(imagen_bytes, valores):
    imagen = Image.open(io.BytesIO(imagen_bytes))
    ancho = int(imagen.width * ESCALA_IMAGEN_DIMENSIONES)
    alto = int(imagen.height * ESCALA_IMAGEN_DIMENSIONES)

    b64 = base64.b64encode(imagen_bytes).decode()

    elementos = [
        (POS_X_LONGITUD_TOTAL, POS_Y_LONGITUD_TOTAL, valores["longitud_total"], False),
        (POS_X_LONGITUD_CABINA, POS_Y_LONGITUD_CABINA, valores["longitud_cabina"], False),
        (POS_X_ALTO_TOTAL, POS_Y_ALTO_TOTAL, valores["alto_total"], True),
        (POS_X_ANCHO_TOTAL, POS_Y_ANCHO_TOTAL, valores["ancho_total"], False),
        (POS_X_DISTANCIA_EJES, POS_Y_DISTANCIA_EJES, valores["distancia_entre_ejes"], False),
        (POS_X_VOLADIZO_ANTERIOR, POS_Y_VOLADIZO_ANTERIOR, valores["voladizo_anterior"], False),
        (POS_X_VOLADIZO_POSTERIOR, POS_Y_VOLADIZO_POSTERIOR, valores["voladizo_posterior"], False),
        (POS_X_LONGITUD_BASTIDOR, POS_Y_LONGITUD_BASTIDOR, valores["longitud_sobre_bastidor"], False),
        (POS_X_ALTO_CARROCERIA, POS_Y_ALTO_CARROCERIA, valores["alto_carroceria"], True),
    ]

    html = f"""
    <div style="
        position:relative;
        width:{ancho}px;
        height:{alto}px;
        margin:0;
        padding:0;
        line-height:0;
    ">
        <img src="data:image/png;base64,{b64}"
             style="
                position:absolute;
                left:0;
                top:0;
                width:{ancho}px;
                height:auto;
                display:block;
             ">
    """

    for x, y, valor, vertical in elementos:
        estilo_extra = ""
        if vertical:
            estilo_extra = """
                writing-mode:vertical-rl;
                transform:rotate(180deg);
            """

        html += f"""
        <div style="
            position:absolute;
            left:{x}px;
            top:{y}px;
            color:{COLOR_DIMENSIONES};
            font-size:{TAMANO_DIMENSIONES}px;
            font-weight:bold;
            font-family:Arial,sans-serif;
            white-space:nowrap;
            line-height:normal;
            z-index:10;
            {estilo_extra}
        ">
            {valor:.0f} mm
        </div>
        """

    html += "</div>"
    return html


# ============================================================
# GRÁFICA PRINCIPAL DE LA VAN
# ============================================================

def crear_grafica_van(imagen, resultados, distancia_entre_ejes, carga):
    cg_vehiculo = resultados["cg_vehiculo_carrozado"]
    cg_carga = resultados["cg_carga"]
    peso_pasajeros = resultados["peso_pasajeros"]

    x_cg_vehiculo = mm_a_pixel_x(cg_vehiculo, distancia_entre_ejes)
    x_cg_carga = mm_a_pixel_x(cg_carga, distancia_entre_ejes)
    x_cg_pasajeros = mm_a_pixel_x(cg_pasajeros, distancia_entre_ejes)

    peso_carroceria = resultados["peso_carroceria"]
    peso_total_eje_delantero = resultados["peso_total_eje_delantero"]
    peso_total_eje_trasero = resultados["peso_total_eje_trasero"]

    fig = plt.figure(figsize=(12.5, 6.8))

    ax = fig.add_axes([0.02, 0.39, 0.66, 0.55])
    ax.imshow(imagen, aspect="equal")

    # CG vehículo
    ax.plot(
        x_cg_vehiculo, y_cg_vehiculo_imagen,
        marker="o", markersize=10,
        markerfacecolor="red",
        markeredgecolor="white",
        markeredgewidth=2, zorder=10
    )

    ax.annotate(
        "",
        xy=(x_cg_vehiculo, y_cg_vehiculo_imagen + 90),
        xytext=(x_cg_vehiculo, y_cg_vehiculo_imagen),
        arrowprops=dict(
            arrowstyle="-|>", color="red",
            linewidth=3, mutation_scale=18
        )
    )

    ax.text(
        x_cg_vehiculo + 28,
        y_cg_vehiculo_imagen - 8,
        "CG vehículo",
        ha="left", va="center",
        fontsize=10, fontweight="bold", color="red",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.90,
                  boxstyle="round,pad=0.25")
    )

    ax.text(
        x_cg_vehiculo,
        y_cg_vehiculo_imagen + 95,
        f"{peso_carroceria:.0f} kg",
        ha="center", va="top",
        fontsize=9, fontweight="bold", color="red",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.85,
                  boxstyle="round,pad=0.2")
    )

    # CG pasajeros
    ax.plot(
        x_cg_pasajeros, y_cg_pasajeros_imagen,
        marker="o", markersize=9,
        markerfacecolor="blue",
        markeredgecolor="white",
        markeredgewidth=2, zorder=10
    )

    ax.annotate(
        "",
        xy=(x_cg_pasajeros, y_cg_pasajeros_imagen + 80),
        xytext=(x_cg_pasajeros, y_cg_pasajeros_imagen),
        arrowprops=dict(
            arrowstyle="-|>", color="blue",
            linewidth=3, mutation_scale=18
        )
    )

    ax.text(
        x_cg_pasajeros + 28,
        y_cg_pasajeros_imagen - 8,
        "CG pasajeros",
        ha="left", va="center",
        fontsize=10, fontweight="bold", color="blue",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.90,
                  boxstyle="round,pad=0.25")
    )

    ax.text(
        x_cg_pasajeros,
        y_cg_pasajeros_imagen + 85,
        f"{peso_pasajeros:.0f} kg",
        ha="center", va="top",
        fontsize=9, fontweight="bold", color="blue",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.85,
                  boxstyle="round,pad=0.2")
    )

    # CG carga
    ax.plot(
        x_cg_carga, y_cg_carga_imagen,
        marker="o", markersize=9,
        markerfacecolor="green",
        markeredgecolor="white",
        markeredgewidth=2, zorder=10
    )

    ax.annotate(
        "",
        xy=(x_cg_carga, y_cg_carga_imagen + 80),
        xytext=(x_cg_carga, y_cg_carga_imagen),
        arrowprops=dict(
            arrowstyle="-|>", color="green",
            linewidth=3, mutation_scale=18
        )
    )

    ax.text(
        x_cg_carga + 28,
        y_cg_carga_imagen - 8,
        "CG carga",
        ha="left", va="center",
        fontsize=10, fontweight="bold", color="green",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.90,
                  boxstyle="round,pad=0.25")
    )

    ax.text(
        x_cg_carga,
        y_cg_carga_imagen + 85,
        f"{carga:.0f} kg",
        ha="center", va="top",
        fontsize=9, fontweight="bold", color="green",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.85,
                  boxstyle="round,pad=0.2")
    )

    # Ejes
    for x, y, peso, nombre in [
        (x1, y1, peso_total_eje_delantero, "Eje delantero"),
        (x2, y2, peso_total_eje_trasero, "Eje trasero"),
    ]:
        ax.add_patch(Circle(
            (x, y), 10,
            facecolor="white", edgecolor="black",
            linewidth=2, zorder=12
        ))

        ax.plot(
            x, y, marker="o", markersize=6,
            markerfacecolor="black",
            markeredgecolor="black", zorder=13
        )

        ax.annotate(
            "",
            xy=(x, y + 80),
            xytext=(x, y),
            arrowprops=dict(
                arrowstyle="-|>", color="black",
                linewidth=3.5, mutation_scale=20
            )
        )

        ax.text(
            x, y + 125,
            f"{peso:.0f} kg",
            ha="center", va="center",
            fontsize=10, fontweight="bold",
            color="black",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.90,
                      boxstyle="round,pad=0.20")
        )

        ax.text(
            x + 30, y, nombre,
            ha="left", va="center",
            fontsize=9, fontweight="bold",
            color="black",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.90,
                      boxstyle="round,pad=0.25")
        )

    ax.set_axis_off()

    # Tabla
    ax_tabla = fig.add_axes([0.03, 0.06, 0.63, 0.27])
    ax_tabla.axis("off")

    datos_tabla = [
        [
            "Vehículo",
            f"{resultados['peso_carroceria_eje_delantero']:.0f} kg",
            f"{resultados['peso_carroceria_eje_trasero']:.0f} kg",
            f"{peso_carroceria:.0f} kg",
        ],
        [
            "Carga",
            f"{resultados['peso_carga_eje_delantero']:.0f} kg",
            f"{resultados['peso_carga_eje_trasero']:.0f} kg",
            f"{carga:.0f} kg",
        ],
        [
            "Pasajeros",
            f"{resultados['peso_pasajeros_eje_delantero']:.0f} kg",
            f"{resultados['peso_pasajeros_eje_trasero']:.0f} kg",
            f"{peso_pasajeros:.0f} kg",
        ],
        [
            "Total",
            f"{peso_total_eje_delantero:.0f} kg",
            f"{peso_total_eje_trasero:.0f} kg",
            f"{resultados['peso_total']:.0f} kg",
        ],
    ]

    tabla = ax_tabla.table(
        cellText=datos_tabla,
        colLabels=["Peso", "Eje Delantero", "Eje Trasero", "Total"],
        cellLoc="center",
        colLoc="center",
        loc="center",
        colWidths=[0.20, 0.28, 0.28, 0.24],
    )

    tabla.auto_set_font_size(False)
    tabla.set_fontsize(10)
    tabla.scale(1, 1.55)

    for _, celda in tabla.get_celld().items():
        celda.set_edgecolor("lightgray")
        celda.set_linewidth(0.8)

    for columna in range(4):
        tabla[0, columna].set_facecolor("#D9E2F3")
        tabla[0, columna].set_text_props(fontweight="bold")

    for fila in range(1, 5):
        tabla[fila, 0].set_facecolor("#F2F2F2")
        tabla[fila, 0].set_text_props(fontweight="bold")

    for columna in range(4):
        tabla[4, columna].set_text_props(fontweight="bold")

    # Gauges
    ax_gauge_delantero = fig.add_axes([0.72, 0.75, 0.21, 0.24])
    crear_gauge(
        ax_gauge_delantero,
        resultados["utilizacion_delantera"],
        "EJE DELANTERO"
    )

    ax_gauge_trasero = fig.add_axes([0.72, 0.40, 0.21, 0.24])
    crear_gauge(
        ax_gauge_trasero,
        resultados["utilizacion_trasera"],
        "EJE TRASERO"
    )

    return fig


# ============================================================
# CARGA DE ARCHIVOS
# ============================================================

with st.sidebar:
    st.header("Archivos")
    archivo_van = st.file_uploader(
        "Van Imagen.png",
        type=["png", "jpg", "jpeg"]
    )
    archivo_dim = st.file_uploader(
        "Dimensiones Van.png",
        type=["png", "jpg", "jpeg"]
    )

# Intentar usar archivos existentes en Colab
if archivo_van is not None:
    img = mpimg.imread(archivo_van)
else:
    try:
        img = mpimg.imread("Van Imagen.png")
    except Exception:
        img = None

if archivo_dim is not None:
    imagen_dimensiones_bytes = archivo_dim.getvalue()
else:
    try:
        with open("Dimensiones Van.png", "rb") as f:
            imagen_dimensiones_bytes = f.read()
    except Exception:
        imagen_dimensiones_bytes = None

# ============================================================
# TÍTULO
# ============================================================

st.markdown(
    '<div style="color:#17365D;font-size:24px;font-weight:bold;margin-bottom:12px;">'
    'ANÁLISIS DE CARGAS DEL VEHÍCULO'
    '</div>',
    unsafe_allow_html=True
)

# ============================================================
# CONTROLES
# ============================================================

# Streamlit vuelve a ejecutar el script al cambiar un control.
# session_state conserva qué sección está abierta.

if "seccion_abierta" not in st.session_state:
    st.session_state.seccion_abierta = None


def boton_seccion(nombre, texto):
    if st.button(
        ("▼  " if st.session_state.seccion_abierta == nombre else "▶  ") + texto,
        key=f"btn_{nombre}",
        use_container_width=True,
    ):
        if st.session_state.seccion_abierta == nombre:
            st.session_state.seccion_abierta = None
        else:
            st.session_state.seccion_abierta = nombre
        st.rerun()


# ============================================================
# LAYOUT ORIGINAL: IMÁGENES A LA IZQUIERDA / CONTROLES A LA DERECHA
# ============================================================

col_visual, col_control = st.columns([1.75, 1.0], gap="small")

# ------------------------------------------------------------
# VISUAL
# ------------------------------------------------------------

with col_visual:

    # --------------------------------------------------------
    # IMAGEN DIMENSIONES
    # --------------------------------------------------------

    if imagen_dimensiones_bytes is not None:

        valores_dim = {
            "longitud_total": longitud_total_inicial,
            "longitud_cabina": longitud_cabina_inicial,
            "alto_total": alto_total_inicial,
            "ancho_total": ancho_total_inicial,
            "distancia_entre_ejes": distancia_entre_ejes_inicial,
            "voladizo_anterior": voladizo_anterior_inicial,
            "voladizo_posterior": voladizo_posterior_inicial,
            "longitud_sobre_bastidor": longitud_sobre_bastidor_inicial,
            "alto_carroceria": alto_carroceria_inicial,
        }

        # Los valores reales se actualizan después de leer los controles.
        # Este bloque se reemplaza más abajo con la misma función usando
        # los valores seleccionados.
    else:
        st.warning(
            "Sube 'Dimensiones Van.png' desde la barra lateral "
            "para visualizar las dimensiones."
        )

# ------------------------------------------------------------
# CONTROL
# ------------------------------------------------------------

with col_control:

    st.markdown(
        '<div class="control-title">PARÁMETROS DEL VEHÍCULO</div>',
        unsafe_allow_html=True
    )

    boton_seccion("dimensiones", "Dimensiones del vehículo")

    # Valores de dimensiones
    if st.session_state.seccion_abierta == "dimensiones":
        st.markdown(
            '<div class="dimension-table">',
            unsafe_allow_html=True
        )

        c1, c2 = st.columns([1.35, 1])

        with c1:
            st.markdown("**PARÁMETRO**")
        with c2:
            st.markdown("**VALOR (mm)**")

        d1, d2 = st.columns([1.35, 1])
        with d1:
            st.markdown("Longitud total")
        with d2:
            longitud_total = st.number_input(
                "Longitud total",
                min_value=0.0,
                value=float(longitud_total_inicial),
                step=1.0,
                label_visibility="collapsed",
                key="longitud_total",
            )

        d1, d2 = st.columns([1.35, 1])
        with d1:
            st.markdown("Longitud de la cabina")
        with d2:
            longitud_cabina = st.number_input(
                "Longitud cabina",
                min_value=0.0,
                value=float(longitud_cabina_inicial),
                step=1.0,
                label_visibility="collapsed",
                key="longitud_cabina",
            )

        d1, d2 = st.columns([1.35, 1])
        with d1:
            st.markdown("Alto total")
        with d2:
            alto_total = st.number_input(
                "Alto total",
                min_value=0.0,
                value=float(alto_total_inicial),
                step=1.0,
                label_visibility="collapsed",
                key="alto_total",
            )

        d1, d2 = st.columns([1.35, 1])
        with d1:
            st.markdown("Ancho total")
        with d2:
            ancho_total = st.number_input(
                "Ancho total",
                min_value=0.0,
                value=float(ancho_total_inicial),
                step=1.0,
                label_visibility="collapsed",
                key="ancho_total",
            )

        d1, d2 = st.columns([1.35, 1])
        with d1:
            st.markdown("Distancia entre ejes")
        with d2:
            distancia_entre_ejes = st.number_input(
                "Distancia ejes",
                min_value=1.0,
                value=float(distancia_entre_ejes_inicial),
                step=1.0,
                label_visibility="collapsed",
                key="distancia_entre_ejes",
            )

        d1, d2 = st.columns([1.35, 1])
        with d1:
            st.markdown("Voladizo anterior")
        with d2:
            voladizo_anterior = st.number_input(
                "Voladizo anterior",
                min_value=0.0,
                value=float(voladizo_anterior_inicial),
                step=1.0,
                label_visibility="collapsed",
                key="voladizo_anterior",
            )

        d1, d2 = st.columns([1.35, 1])
        with d1:
            st.markdown("Voladizo posterior")
        with d2:
            voladizo_posterior = st.number_input(
                "Voladizo posterior",
                min_value=0.0,
                value=float(voladizo_posterior_inicial),
                step=1.0,
                label_visibility="collapsed",
                key="voladizo_posterior",
            )

        d1, d2 = st.columns([1.35, 1])
        with d1:
            st.markdown("Longitud sobre bastidor")
        with d2:
            longitud_sobre_bastidor = st.number_input(
                "Longitud bastidor",
                min_value=0.0,
                value=float(longitud_sobre_bastidor_inicial),
                step=1.0,
                label_visibility="collapsed",
                key="longitud_sobre_bastidor",
            )

        d1, d2 = st.columns([1.35, 1])
        with d1:
            st.markdown("Alto carrocería")
        with d2:
            alto_carroceria = st.number_input(
                "Alto carrocería",
                min_value=0.0,
                value=float(alto_carroceria_inicial),
                step=1.0,
                label_visibility="collapsed",
                key="alto_carroceria",
            )

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        longitud_total = st.session_state.get("longitud_total", float(longitud_total_inicial))
        longitud_cabina = st.session_state.get("longitud_cabina", float(longitud_cabina_inicial))
        alto_total = st.session_state.get("alto_total", float(alto_total_inicial))
        ancho_total = st.session_state.get("ancho_total", float(ancho_total_inicial))
        distancia_entre_ejes = st.session_state.get("distancia_entre_ejes", float(distancia_entre_ejes_inicial))
        voladizo_anterior = st.session_state.get("voladizo_anterior", float(voladizo_anterior_inicial))
        voladizo_posterior = st.session_state.get("voladizo_posterior", float(voladizo_posterior_inicial))
        longitud_sobre_bastidor = st.session_state.get("longitud_sobre_bastidor", float(longitud_sobre_bastidor_inicial))
        alto_carroceria = st.session_state.get("alto_carroceria", float(alto_carroceria_inicial))

    boton_seccion("pasajeros", "Pasajeros")

    if st.session_state.seccion_abierta == "pasajeros":
        numero_pasajeros = st.number_input(
            "Número de pasajeros:",
            min_value=0,
            max_value=20,
            value=int(st.session_state.get("numero_pasajeros", numero_pasajeros_inicial)),
            step=1,
            key="numero_pasajeros",
        )
        st.write(
            f"Pasajeros: **{numero_pasajeros}**  |  "
            f"Peso pasajeros: **{numero_pasajeros * peso_por_pasajero:.0f} kg**"
        )
    else:
        numero_pasajeros = int(
            st.session_state.get("numero_pasajeros", numero_pasajeros_inicial)
        )

    boton_seccion("carga", "Carga")

    if st.session_state.seccion_abierta == "carga":
        carga = st.slider(
            "Carga:",
            min_value=0,
            max_value=5000,
            value=int(st.session_state.get("carga", carga_inicial)),
            step=10,
            key="carga",
        )

        cg_carga_temp = (
            longitud_cabina
            - voladizo_anterior
            + longitud_sobre_bastidor / 2
        )

        st.write(
            f"Carga: **{carga:.0f} kg**  |  "
            f"CG carga: **{cg_carga_temp:.1f} mm**"
        )
    else:
        carga = int(st.session_state.get("carga", carga_inicial))

    boton_seccion("carroceria", "Pesos de la carrocería")

    if st.session_state.seccion_abierta == "carroceria":
        peso_carroceria_eje_delantero = st.slider(
            "Peso carrocería eje delantero:",
            min_value=0,
            max_value=3000,
            value=int(
                st.session_state.get(
                    "peso_carroceria_eje_delantero",
                    peso_carroceria_eje_delantero_inicial,
                )
            ),
            step=5,
            key="peso_carroceria_eje_delantero",
        )

        st.write(
            f"Peso carrocería eje delantero: "
            f"**{peso_carroceria_eje_delantero:.0f} kg**"
        )

        peso_carroceria_eje_trasero = st.slider(
            "Peso carrocería eje trasero:",
            min_value=0,
            max_value=3000,
            value=int(
                st.session_state.get(
                    "peso_carroceria_eje_trasero",
                    peso_carroceria_eje_trasero_inicial,
                )
            ),
            step=5,
            key="peso_carroceria_eje_trasero",
        )

        st.write(
            f"Peso carrocería eje trasero: "
            f"**{peso_carroceria_eje_trasero:.0f} kg**"
        )
    else:
        peso_carroceria_eje_delantero = int(
            st.session_state.get(
                "peso_carroceria_eje_delantero",
                peso_carroceria_eje_delantero_inicial,
            )
        )
        peso_carroceria_eje_trasero = int(
            st.session_state.get(
                "peso_carroceria_eje_trasero",
                peso_carroceria_eje_trasero_inicial,
            )
        )

# ============================================================
# RESULTADOS ACTUALIZADOS
# ============================================================

resultados = calcular_resultados(
    numero_pasajeros,
    carga,
    peso_carroceria_eje_delantero,
    peso_carroceria_eje_trasero,
    longitud_cabina,
    voladizo_anterior,
    longitud_sobre_bastidor,
    distancia_entre_ejes,
)

resultados["peso_carroceria_eje_delantero"] = peso_carroceria_eje_delantero
resultados["peso_carroceria_eje_trasero"] = peso_carroceria_eje_trasero

# ============================================================
# MOSTRAR VISUALES
# ============================================================

with col_visual:

    if imagen_dimensiones_bytes is not None:
        valores_dim = {
            "longitud_total": longitud_total,
            "longitud_cabina": longitud_cabina,
            "alto_total": alto_total,
            "ancho_total": ancho_total,
            "distancia_entre_ejes": distancia_entre_ejes,
            "voladizo_anterior": voladizo_anterior,
            "voladizo_posterior": voladizo_posterior,
            "longitud_sobre_bastidor": longitud_sobre_bastidor,
            "alto_carroceria": alto_carroceria,
        }

        st.markdown(
            crear_imagen_dimensiones_html(
                imagen_dimensiones_bytes,
                valores_dim,
            ),
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)

    if img is not None:
        fig = crear_grafica_van(
            img,
            resultados,
            distancia_entre_ejes,
            carga,
        )
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)
    else:
        st.warning(
            "Sube 'Van Imagen.png' desde la barra lateral "
            "para visualizar la distribución de pesos."
        )

# ============================================================
# RESULTADOS EN EL PANEL DERECHO
# ============================================================

with col_control:

    st.markdown(
        '<hr style="margin:8px 0;">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="control-title">DATOS Y RESULTADOS</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        **DATOS DEL VEHÍCULO**

        Longitud total: **{longitud_total:.0f} mm**

        Longitud de la cabina: **{longitud_cabina:.0f} mm**

        Alto total: **{alto_total:.0f} mm**

        Ancho total: **{ancho_total:.0f} mm**

        Distancia entre ejes: **{distancia_entre_ejes:.0f} mm**

        Voladizo anterior: **{voladizo_anterior:.0f} mm**

        Voladizo posterior: **{voladizo_posterior:.0f} mm**

        Longitud sobre bastidor: **{longitud_sobre_bastidor:.0f} mm**

        Alto carrocería: **{alto_carroceria:.0f} mm**

        ---

        **VEHÍCULO CARROZADO**

        Peso carrocería: **{resultados['peso_carroceria']:.1f} kg**

        Peso eje delantero: **{peso_carroceria_eje_delantero:.1f} kg**

        Peso eje trasero: **{peso_carroceria_eje_trasero:.1f} kg**

        CG vehículo carrozado: **{resultados['cg_vehiculo_carrozado']:.1f} mm**

        ---

        **PASAJEROS**

        Número de pasajeros: **{numero_pasajeros}**

        Peso pasajeros: **{resultados['peso_pasajeros']:.1f} kg**

        CG pasajeros: **{cg_pasajeros:.1f} mm**

        Peso pasajeros eje delantero: **{resultados['peso_pasajeros_eje_delantero']:.1f} kg**

        Peso pasajeros eje trasero: **{resultados['peso_pasajeros_eje_trasero']:.1f} kg**

        ---

        **CARGA**

        Carga: **{carga:.1f} kg**

        CG carga: **{resultados['cg_carga']:.1f} mm**

        Peso carga eje delantero: **{resultados['peso_carga_eje_delantero']:.1f} kg**

        Peso carga eje trasero: **{resultados['peso_carga_eje_trasero']:.1f} kg**

        ---

        **EJES**

        Peso total eje delantero: **{resultados['peso_total_eje_delantero']:.1f} kg**

        Capacidad eje delantero: **{capacidad_eje_delantero:.1f} kg**

        Utilización eje delantero: **{resultados['utilizacion_delantera']:.1f}%**

        Peso total eje trasero: **{resultados['peso_total_eje_trasero']:.1f} kg**

        Capacidad eje trasero: **{capacidad_eje_trasero:.1f} kg**

        Utilización eje trasero: **{resultados['utilizacion_trasera']:.1f}%**
        """
    )
