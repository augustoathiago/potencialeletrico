import math
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# =========================================================
# Configuração da página
# =========================================================
st.set_page_config(
    page_title="Simulador Potencial Elétrico",
    page_icon="⚡",
    layout="wide"
)

# =========================================================
# Estilos
# =========================================================
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }

    .small-note {
        color: #111111;
        font-size: 0.95rem;
    }

    .section-header-card {
        background: #ffffff;
        border: 1px solid #d0d0d0;
        border-radius: 12px;
        padding: 14px 16px;
        margin-top: 14px;
        margin-bottom: 8px;
        color: #111111 !important;
    }

    .section-header-title {
        color: #111111 !important;
        font-size: 1.45rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
        line-height: 1.2;
    }

    .section-header-desc {
        color: #111111 !important;
        font-size: 1rem;
        line-height: 1.45;
        margin: 0;
    }

    .calc-box {
        background: #f7f7f7;
        border: 1px solid #d0d0d0;
        border-radius: 12px;
        padding: 14px 16px;
        margin-top: 8px;
        margin-bottom: 10px;
        color: #111111 !important;
    }

    .calc-box * {
        color: #111111 !important;
    }

    .result-line {
        font-size: 1.03rem;
        margin-bottom: 0.35rem;
        color: #111111 !important;
    }

    /* Em telas estreitas, permite arrastar horizontalmente a área do gráfico */
    [data-testid="stPlotlyChart"] {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch;
    }

    [data-testid="stPlotlyChart"] > div {
        min-width: 1040px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# Constantes
# =========================================================
K = 9.9e9  # N·m²/C²

# =========================================================
# Funções auxiliares
# =========================================================
SUPERSCRIPT_MAP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")

def int_to_superscript(n: int) -> str:
    return str(n).translate(SUPERSCRIPT_MAP)

def format_decimal_pt(value: float, digits: int = 3) -> str:
    if math.isinf(value):
        return "∞" if value > 0 else "−∞"
    if math.isnan(value):
        return "indefinido"
    s = f"{value:.{digits}f}"
    return s.replace(".", ",")

def format_scientific_pt(value: float, digits: int = 3) -> str:
    """
    Formata número em notação científica:
    3,14 × 10²
    em vez de 3.14e2
    """
    if math.isinf(value):
        return "∞" if value > 0 else "−∞"
    if math.isnan(value):
        return "indefinido"
    if value == 0:
        return "0"

    sign = "−" if value < 0 else ""
    x = abs(value)
    exponent = int(math.floor(math.log10(x)))
    mantissa = x / (10 ** exponent)

    if 1e-2 <= x < 1e4:
        s = f"{value:.{digits}f}".replace(".", ",")
        s = s.rstrip("0").rstrip(",") if "," in s else s
        return s

    mantissa_str = f"{mantissa:.{digits}f}".replace(".", ",")
    mantissa_str = mantissa_str.rstrip("0").rstrip(",")
    return f"{sign}{mantissa_str} × 10{int_to_superscript(exponent)}"

def format_charge_coulomb_from_micro(q_micro: float, digits: int = 3) -> str:
    q_c = q_micro * 1e-6
    return f"{format_scientific_pt(q_c, digits)} C"

def distance_to_origin(x: float, y: float) -> float:
    return math.hypot(x, y)

def potential_point_charge(q_micro: float, r: float) -> float:
    """
    Potencial gerado por uma carga puntiforme no ponto P.
    q em μC; r em m; resultado em V.
    """
    q_c = q_micro * 1e-6

    if r == 0:
        if q_c > 0:
            return math.inf
        elif q_c < 0:
            return -math.inf
        return 0.0

    return K * q_c / r

def html_formula_line(text: str) -> str:
    return f'<div class="result-line">{text}</div>'

def finite_sum(a: float, b: float) -> float:
    if math.isinf(a) and math.isinf(b):
        if a > 0 and b > 0:
            return math.inf
        if a < 0 and b < 0:
            return -math.inf
        return math.nan
    return a + b

def charge_color(q_micro: float) -> str:
    if q_micro > 0:
        return "red"
    elif q_micro < 0:
        return "blue"
    return "black"

def section_header(title: str, description: str):
    st.markdown(
        f"""
        <div class="section-header-card">
            <div class="section-header-title">{title}</div>
            <div class="section-header-desc">{description}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def build_calc_section(
    titulo: str,
    indice: str,
    x: float,
    y: float,
    q_micro: float,
    r: float,
    v: float
):
    section_header(
        titulo,
        f"Potencial elétrico gerado pela carga puntiforme {indice} no ponto P."
    )

    conteudo = (
        html_formula_line(
            f"<b>V<sub>{indice}</sub> = K · q<sub>{indice}</sub> / r<sub>{indice}</sub></b>"
        )
        + html_formula_line(
            f"sendo <b>K</b> a constante de Coulomb = {format_scientific_pt(K, 3)} N·m²/C²"
        )
        + html_formula_line(
            f"<b>q<sub>{indice}</sub></b> a carga da partícula {indice} = {format_charge_coulomb_from_micro(q_micro, 3)} C"
        )
        + html_formula_line(
            f"<b>r<sub>{indice}</sub></b> a distância entre a partícula {indice} e o ponto P = "
            f"√(x<sub>{indice}</sub>² + y<sub>{indice}</sub>²) = "
            f"√(({format_decimal_pt(x, 2)})² + ({format_decimal_pt(y, 2)})²) = {format_decimal_pt(r, 3)} m"
        )
        + "<br>"
    )

    if r != 0:
        conteudo += html_formula_line(
            f"<b>V<sub>{indice}</sub> = "
            f"{format_scientific_pt(K, 3)} · ({format_scientific_pt(q_micro * 1e-6, 3)}) / {format_decimal_pt(r, 3)}</b>"
        )
        conteudo += html_formula_line(
            f"<b>V<sub>{indice}</sub> = {format_scientific_pt(v, 3)} V</b>"
        )
    else:
        conteudo += html_formula_line(
            f"<b>Como r<sub>{indice}</sub> = 0, o potencial torna-se "
            f"{'∞' if v > 0 else ('−∞' if v < 0 else '0')}.</b>"
        )

    st.markdown(
        f'<div class="calc-box">{conteudo}</div>',
        unsafe_allow_html=True
    )

def build_potential_grid(x1, y1, q1_micro, x2, y2, q2_micro):
    """
    Gera malha de potencial para equipotenciais.
    """
    xs = np.linspace(-15, 15, 260)
    ys = np.linspace(-15, 15, 260)
    X, Y = np.meshgrid(xs, ys)

    eps = 0.20

    r1 = np.sqrt((X - x1) ** 2 + (Y - y1) ** 2)
    r2 = np.sqrt((X - x2) ** 2 + (Y - y2) ** 2)

    q1_c = q1_micro * 1e-6
    q2_c = q2_micro * 1e-6

    with np.errstate(divide='ignore', invalid='ignore'):
        V = K * q1_c / r1 + K * q2_c / r2

    mask = (r1 < eps) | (r2 < eps)
    V = np.where(mask, np.nan, V)

    return xs, ys, V

def build_figure(x1, y1, q1_micro, x2, y2, q2_micro, v_total):
    """
    Cria figura com:
    - gráfico cartesiano à esquerda
    - box de resumo à direita
    """
    xs, ys, V = build_potential_grid(x1, y1, q1_micro, x2, y2, q2_micro)

    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.80, 0.20],
        specs=[[{"type": "xy"}, {"type": "domain"}]],
        horizontal_spacing=0.03
    )

    finite_vals = V[np.isfinite(V)]
    if finite_vals.size > 0 and np.nanmax(np.abs(finite_vals)) > 0:
        vmax = float(np.nanpercentile(np.abs(finite_vals), 92))
        vmax = max(vmax, 1.0)
        n_levels = 12
        step = (2 * vmax) / n_levels

        contour_trace = go.Contour(
            x=xs,
            y=ys,
            z=V,
            contours=dict(
                start=-vmax,
                end=vmax,
                size=step,
                coloring="none",
                showlines=True
            ),
            line=dict(width=1),
            colorscale="RdBu",
            showscale=False,
            hovertemplate="x = %{x:.2f} m<br>y = %{y:.2f} m<br>V = %{z:.2f} V<extra></extra>"
        )
        fig.add_trace(contour_trace, row=1, col=1)

    # Eixos cartesianos
    fig.add_shape(
        type="line",
        x0=-15, x1=15, y0=0, y1=0,
        line=dict(color="#666666", width=1),
        row=1, col=1
    )
    fig.add_shape(
        type="line",
        x0=0, x1=0, y0=-15, y1=15,
        line=dict(color="#666666", width=1),
        row=1, col=1
    )

    # Ponto P
    fig.add_trace(
        go.Scatter(
            x=[0],
            y=[0],
            mode="markers+text",
            marker=dict(size=10, color="green", symbol="circle"),
            text=["P"],
            textposition="top center",
            textfont=dict(color="#111111", size=14),
            name="P",
            hovertemplate="Ponto P<br>x = 0 m<br>y = 0 m<extra></extra>"
        ),
        row=1, col=1
    )

    # Carga 1
    fig.add_trace(
        go.Scatter(
            x=[x1],
            y=[y1],
            mode="markers+text",
            marker=dict(size=16, color=charge_color(q1_micro), symbol="circle"),
            text=["q₁"],
            textposition="top center",
            textfont=dict(color="#111111", size=14),
            name="Carga 1",
            hovertemplate=(
                f"Carga 1<br>x₁ = {x1:.2f} m<br>y₁ = {y1:.2f} m<br>"
                f"q₁ = {q1_micro:.2f} μC<extra></extra>"
            )
        ),
        row=1, col=1
    )

    # Carga 2
    fig.add_trace(
        go.Scatter(
            x=[x2],
            y=[y2],
            mode="markers+text",
            marker=dict(size=16, color=charge_color(q2_micro), symbol="circle"),
            text=["q₂"],
            textposition="top center",
            textfont=dict(color="#111111", size=14),
            name="Carga 2",
            hovertemplate=(
                f"Carga 2<br>x₂ = {x2:.2f} m<br>y₂ = {y2:.2f} m<br>"
                f"q₂ = {q2_micro:.2f} μC<extra></extra>"
            )
        ),
        row=1, col=1
    )

    # Box lateral de resumo
    resumo_html = (
        f"<b>Resumo</b><br>"
        f"q₁ = {format_decimal_pt(q1_micro, 2)} μC<br>"
        f"q₂ = {format_decimal_pt(q2_micro, 2)} μC<br>"
        f"Vₚ = {format_scientific_pt(v_total, 3)} V"
    )

    fig.add_annotation(
        x=0.90,
        y=0.92,
        xref="paper",
        yref="paper",
        text=resumo_html,
        showarrow=False,
        align="left",
        bordercolor="#222222",
        borderwidth=1,
        borderpad=8,
        bgcolor="rgba(255,255,255,0.97)",
        font=dict(size=14, color="#111111")
    )

    # Abre inicialmente entre -15 e 15 m
    # dragmode="zoom" favorece interação de zoom
    fig.update_xaxes(
        title_text="x (m)",
        row=1, col=1,
        range=[-15, 15],
        dtick=5,
        zeroline=False,
        scaleanchor="y",
        scaleratio=1,
        tickfont=dict(color="#111111", size=12),
        title_font=dict(color="#111111", size=14),
        showline=True,
        linewidth=1,
        linecolor="#444444"
    )

    fig.update_yaxes(
        title_text="y (m)",
        row=1, col=1,
        range=[-15, 15],
        dtick=5,
        zeroline=False,
        tickfont=dict(color="#111111", size=12),
        title_font=dict(color="#111111", size=14),
        showline=True,
        linewidth=1,
        linecolor="#444444"
    )

    fig.update_layout(
        width=1080,
        height=650,
        margin=dict(l=55, r=25, t=30, b=45),
        showlegend=False,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#111111"),
        dragmode="zoom"   # <- importante para favorecer zoom
    )

    return fig

# =========================================================
# Cabeçalho
# =========================================================
col_logo, col_title = st.columns([1, 3], gap="large")

with col_logo:
    try:
        st.image("logo_maua.png", use_container_width=True)
    except Exception:
        st.info("Coloque o arquivo `logo_maua.png` na mesma pasta do app para exibir o logotipo.")

with col_title:
    st.title("Simulador Potencial Elétrico")
    st.write("Estude o potencial elétrico nos arredores de duas cargas puntiformes.")

# =========================================================
# Parâmetros
# =========================================================
st.markdown("## Parâmetros")

param_col1, param_col2 = st.columns(2, gap="large")

with param_col1:
    st.markdown("### Carga puntiforme 1")
    x1 = st.slider("Posição x₁ (m)", min_value=-10.0, max_value=10.0, value=-4.0, step=0.1)
    y1 = st.slider("Posição y₁ (m)", min_value=-10.0, max_value=10.0, value=3.0, step=0.1)
    q1_micro = st.slider("Carga q₁ (μC)", min_value=-10.0, max_value=10.0, value=5.0, step=0.1)

with param_col2:
    st.markdown("### Carga puntiforme 2")
    x2 = st.slider("Posição x₂ (m)", min_value=-10.0, max_value=10.0, value=5.0, step=0.1)
    y2 = st.slider("Posição y₂ (m)", min_value=-10.0, max_value=10.0, value=4.0, step=0.1)
    q2_micro = st.slider("Carga q₂ (μC)", min_value=-10.0, max_value=10.0, value=-4.0, step=0.1)

# =========================================================
# Cálculos
# =========================================================
r1 = distance_to_origin(x1, y1)
r2 = distance_to_origin(x2, y2)

V1 = potential_point_charge(q1_micro, r1)
V2 = potential_point_charge(q2_micro, r2)
Vp = finite_sum(V1, V2)

# =========================================================
# Imagem
# =========================================================
st.markdown("## Imagem")
st.markdown(
    '<div class="small-note">Em celulares, tente usar dois dedos (pinça) sobre a figura para dar zoom. Se a tela for estreita, também é possível deslizar horizontalmente a área do gráfico para visualizar tudo.</div>',
    unsafe_allow_html=True
)

fig = build_figure(x1, y1, q1_micro, x2, y2, q2_micro, Vp)

st.plotly_chart(
    fig,
    use_container_width=False,
    config={
        "displaylogo": False,
        "responsive": False,
        "scrollZoom": True,   # <- importante para zoom por gesto / pinça
        "doubleClick": "reset",
        "modeBarButtonsToRemove": [
            "lasso2d",
            "select2d",
            "autoScale2d"
        ]
    }
)

# =========================================================
# Potencial elétrico V1
# =========================================================
build_calc_section(
    titulo="Potencial elétrico V1",
    indice="1",
    x=x1,
    y=y1,
    q_micro=q1_micro,
    r=r1,
    v=V1
)

# =========================================================
# Potencial elétrico V2
# =========================================================
build_calc_section(
    titulo="Potencial elétrico V2",
    indice="2",
    x=x2,
    y=y2,
    q_micro=q2_micro,
    r=r2,
    v=V2
)

# =========================================================
# Potencial elétrico no ponto P
# =========================================================
section_header(
    "Potencial elétrico no ponto P",
    "Soma dos potenciais gerados pelas cargas puntiformes 1 e 2 no ponto P."
)

if math.isnan(Vp):
    linha_resultado = (
        "A soma resulta em valor indefinido, pois há contribuições infinitas de sinais opostos no ponto P."
    )
else:
    linha_resultado = f"<b>Vₚ = {format_scientific_pt(Vp, 3)} V</b>"

st.markdown(
    '<div class="calc-box">'
    + html_formula_line("<b>Vₚ = V₁ + V₂</b>")
    + html_formula_line(
        f"<b>Vₚ = {format_scientific_pt(V1, 3)} + {format_scientific_pt(V2, 3)}</b>"
    )
    + html_formula_line(linha_resultado)
    + '</div>',
    unsafe_allow_html=True
)
