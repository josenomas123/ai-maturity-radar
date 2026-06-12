"""
AI Maturity Radar — Herramienta de evaluación de madurez en adopción de IA.
Evalúa 5 pilares con 4 preguntas cada uno (escala 1–5) y genera un gráfico
de radar interactivo + plan de acción automático o vía OpenAI.
"""

import json
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

# Intentamos importar OpenAI; si no está instalado, se usa el análisis básico.
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# ── Configuración de página ───────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Maturity Radar",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Datos: pilares y preguntas ────────────────────────────────────────────────

PILLARS = {
    "🧭 Estrategia y Liderazgo": {
        "short": "Estrategia",
        "color": "#FF6B6B",
        "description": "¿La IA está en la agenda de dirección o en el cajón?",
        "questions": [
            "La dirección tiene una visión IA documentada y ambiciosa a 12–24 meses.",
            "Existe un sponsor ejecutivo con mandato formal y presupuesto asignado a IA.",
            "Los KPIs de IA están conectados a objetivos de negocio y al P&L de la empresa.",
            "La IA se discute regularmente en los comités de dirección (al menos mensual).",
            "Existe un roadmap IA formal con hitos, fechas y responsables identificados.",
            "La inversión anual en IA supera el 2% de la facturación de la empresa.",
            "La estrategia IA se revisa y actualiza al menos una vez al año con métricas objetivas.",
        ],
    },
    "🗄️ Datos y Tecnología": {
        "short": "Datos y Tech",
        "color": "#4ECDC4",
        "description": "¿Tus datos son un activo o un problema oculto?",
        "questions": [
            "Los datos de cliente, venta y operaciones están centralizados y son accesibles.",
            "La arquitectura tecnológica (cloud, APIs) está preparada para integrar IA.",
            "Los sistemas clave (CRM, ERP, canales) están integrados entre sí.",
            "Existe una única fuente de verdad para los datos críticos del negocio.",
            "La calidad de los datos se mide y monitoriza de forma continua.",
            "Tenemos herramientas de analítica avanzada o BI en uso regular por el equipo.",
            "Podemos acceder a los datos de cliente y venta clave en menos de un día hábil.",
        ],
    },
    "🙌 Personas y Cultura": {
        "short": "Personas",
        "color": "#45B7D1",
        "description": "¿Tu equipo empuja la IA o la IA empuja a tu equipo?",
        "questions": [
            "Existe un programa continuo de formación en IA para el equipo (no puntual).",
            "Más del 30% del equipo utiliza IA en su trabajo diario de forma productiva.",
            "La cultura valora la experimentación y el aprendizaje rápido con nuevas herramientas.",
            "Hay embajadores IA o referentes internos en las áreas clave del negocio.",
            "Los casos de éxito con IA se comunican y celebran internamente.",
            "El equipo no tiene miedo a ser reemplazado por IA, lo ve como palanca personal.",
            "Los procesos de contratación incorporan ya skills de IA como competencia valorada.",
        ],
    },
    "⚙️ Procesos y Casos de Uso": {
        "short": "Procesos",
        "color": "#96CEB4",
        "description": "¿Eliges casos por moda o por valor cuantificable?",
        "questions": [
            "Tenemos un portfolio de casos de uso priorizados por impacto y esfuerzo.",
            "Al menos un caso de uso de IA está en producción con ROI medido y documentado.",
            "Cada caso de uso tiene KPIs claros, owner asignado y sistema de medición.",
            "Los pilotos que funcionan se escalan a producción con un proceso definido.",
            "Existen mecanismos para capturar feedback de los usuarios de las herramientas IA.",
            "Se comparten aprendizajes entre pilotos (lo que funcionó y lo que no).",
            "La IA ya está integrada en al menos uno de los procesos core del negocio.",
        ],
    },
    "⚖️ Gobernanza y Ética": {
        "short": "Gobernanza",
        "color": "#FFEAA7",
        "description": "¿Estás construyendo sobre terreno firme o sobre arena?",
        "questions": [
            "Tenemos una política de uso responsable de IA publicada internamente y firmada.",
            "Cumplimos con RGPD, AI Act y requisitos sectoriales aplicables a IA.",
            "Existen controles de acceso y trazabilidad a los datos que usan los modelos IA.",
            "Hay un responsable formal de IA y datos (puede coincidir con el DPO).",
            "Los empleados saben qué tipos de datos NO pueden subir a IAs públicas.",
            "Las licencias corporativas de IA tienen cláusulas de no-training con nuestros datos.",
            "Los modelos en producción están documentados en un registro accesible y auditable.",
        ],
    },
}

PILLAR_KEYS = list(PILLARS.keys())
SHORT_NAMES = [PILLARS[k]["short"] for k in PILLAR_KEYS]

# Rangos de madurez: (min_score, max_score_exclusive) → (etiqueta, descripción)
MATURITY_LEVELS = [
    (1.0, 1.8, "🔴 Inicial",      "La organización está en etapas muy tempranas de adopción de IA."),
    (1.8, 2.6, "🟠 Exploratorio", "Hay iniciativas aisladas de IA pero sin estrategia coherente."),
    (2.6, 3.4, "🟡 Definido",     "Existen procesos definidos y una estrategia de IA emergente."),
    (3.4, 4.2, "🟢 Gestionado",   "La IA está integrada en procesos clave con métricas de seguimiento."),
    (4.2, 5.1, "🏆 Optimizado",   "La IA es una capacidad core con mejora continua y liderazgo de mercado."),
]


# ── Funciones de utilidad ─────────────────────────────────────────────────────

def get_maturity(score: float) -> tuple[str, str]:
    """Devuelve (etiqueta, descripción) según el puntaje global."""
    for low, high, label, desc in MATURITY_LEVELS:
        if low <= score < high:
            return label, desc
    return "🏆 Optimizado", "Nivel máximo de madurez en IA."


def build_radar_chart(scores: list[float], labels: list[str]) -> go.Figure:
    """Construye el gráfico de radar (pentágono) con Plotly."""
    # Cerramos el polígono repitiendo el primer valor
    values = scores + [scores[0]]
    cats   = labels  + [labels[0]]

    fig = go.Figure()

    # Área de puntaje actual
    fig.add_trace(go.Scatterpolar(
        r=values, theta=cats,
        fill="toself",
        fillcolor="rgba(78, 205, 196, 0.25)",
        line=dict(color="#4ECDC4", width=2.5),
        name="Puntaje Actual",
        hovertemplate="<b>%{theta}</b><br>Puntaje: %{r:.2f} / 5.0<extra></extra>",
    ))

    # Contorno de referencia (puntaje máximo = 5)
    fig.add_trace(go.Scatterpolar(
        r=[5] * len(cats), theta=cats,
        fill="toself",
        fillcolor="rgba(200,200,200,0.07)",
        line=dict(color="rgba(200,200,200,0.4)", width=1, dash="dot"),
        name="Máximo (5.0)",
        hoverinfo="skip",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True, range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                ticktext=["1 Inicial", "2 Exploratorio", "3 Definido", "4 Gestionado", "5 Optimizado"],
                tickfont=dict(size=9),
                gridcolor="rgba(255,255,255,0.15)",
            ),
            angularaxis=dict(tickfont=dict(size=13, color="white")),
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=520,
        margin=dict(t=40, b=90, l=90, r=90),
    )
    return fig


def action_plan_basic(scores: list[float]) -> str:
    """Plan de acción basado en reglas (sin API de OpenAI)."""
    pairs = sorted(zip(scores, SHORT_NAMES))  # del más bajo al más alto
    lines = []

    for score, name in pairs[:2]:            # los 2 pilares más débiles
        if score < 2:
            prioridad = "🔴 CRÍTICO"
            accion    = f"Establecer fundamentos básicos en **{name}**."
        elif score < 3:
            prioridad = "🟠 ALTO"
            accion    = f"Desarrollar capacidades estructuradas en **{name}**."
        elif score < 4:
            prioridad = "🟡 MEDIO"
            accion    = f"Optimizar y escalar las prácticas existentes en **{name}**."
        else:
            prioridad = "🟢 BAJO"
            accion    = f"Mantener e innovar en **{name}**."

        lines.append(
            f"- **{prioridad} — {name}** *(Puntaje: {score:.1f}/5.0)*  \n  → {accion}"
        )

    return f"""## 📋 Plan de Acción Recomendado

> ⚙️ *Análisis automático — añade tu API Key de OpenAI en la barra lateral para un análisis con IA personalizado.*

### Áreas de Mayor Oportunidad

{chr(10).join(lines)}

### Hoja de Ruta Sugerida

| Plazo | Acción |
|---|---|
| Semana 1–2 | Diagnóstico detallado en las áreas críticas identificadas |
| Mes 1 | Definir quick-wins y proyectos piloto de alto impacto |
| Trimestre 1 | Implementar mejoras fundamentales en los pilares más débiles |
| Trimestre 2–3 | Escalar iniciativas exitosas y medir resultados |
| Anual | Revisar y actualizar la estrategia de madurez en IA |
"""


def action_plan_openai(scores: list[float], api_key: str, profile: dict) -> str:
    """Plan de acción personalizado generado por GPT-4o-mini usando perfil + puntajes."""
    client = OpenAI(api_key=api_key)

    resumen = "\n".join(
        f"- {name}: {score:.2f}/5.0"
        for score, name in zip(scores, SHORT_NAMES)
    )
    global_score = sum(scores) / len(scores)
    g_label, _ = get_maturity(global_score)

    # Construye el contexto de empresa solo con los campos que el usuario rellenó
    ctx_lines = []
    if profile.get("empresa") and profile["empresa"] != "Sin especificar":
        ctx_lines.append(f"- Empresa: {profile['empresa']}")
    if profile.get("sector") and profile["sector"] != "—":
        ctx_lines.append(f"- Sector: {profile['sector']}")
    if profile.get("empleados") and profile["empleados"] != "—":
        ctx_lines.append(f"- Tamaño: {profile['empleados']} empleados")
    if profile.get("facturacion") and profile["facturacion"] != "—":
        ctx_lines.append(f"- Facturación anual: {profile['facturacion']}")
    if profile.get("pais") and profile["pais"] != "—":
        ctx_lines.append(f"- País: {profile['pais']}")
    if profile.get("cargo") and profile["cargo"] != "—":
        ctx_lines.append(f"- Evaluado por: {profile['cargo']}")

    company_context = "\n".join(ctx_lines) if ctx_lines else "No especificado"

    prompt = f"""Eres un consultor senior experto en transformación digital e inteligencia artificial para empresas.

## Contexto de la empresa evaluada
{company_context}

## Resultados de la evaluación de madurez en IA
{resumen}
Puntaje global: {global_score:.2f}/5.0 — Nivel: {g_label}

## Instrucciones
Genera un Plan de Acción ejecutivo en español, completamente personalizado para esta empresa concreta (su sector, tamaño y contexto). Incluye las siguientes secciones:

1. **Diagnóstico Ejecutivo** — 2–3 oraciones que describan la situación actual de esta empresa específica, mencionando su sector y tamaño si están disponibles.
2. **Fortalezas a Capitalizar** — 2–3 puntos basados en los pilares con mayor puntaje, con recomendaciones concretas para este tipo de empresa.
3. **Áreas Críticas de Mejora** — Los 2 pilares más débiles con acciones específicas y adaptadas al sector y tamaño de la organización.
4. **Hoja de Ruta de 90 días** — 5 acciones concretas, priorizadas y realistas para el tamaño y recursos de esta empresa.
5. **KPIs de Seguimiento** — 4 métricas medibles y relevantes para este sector.

Usa lenguaje ejecutivo directo. No uses frases genéricas — cada punto debe reflejar el contexto de esta empresa. Formato Markdown."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1400,
        temperature=0.7,
    )
    return response.choices[0].message.content


def to_json(responses: dict, scores: list[float], profile: dict) -> str:
    """Serializa los resultados en formato JSON para descarga."""
    label, _ = get_maturity(sum(scores) / len(scores))
    data = {
        "metadata": {
            **profile,
            "fecha_evaluacion": datetime.now().isoformat(),
            "herramienta": "AI Maturity Radar v1.0",
        },
        "puntajes_pilares": {name: round(score, 4) for name, score in zip(SHORT_NAMES, scores)},
        "puntaje_global": round(sum(scores) / len(scores), 4),
        "nivel_madurez": label,
        "respuestas_detalladas": responses,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def to_csv(scores: list[float]) -> str:
    """Genera un CSV sencillo con los puntajes por pilar."""
    global_score = sum(scores) / len(scores)
    rows = [["Pilar", "Puntaje", "Nivel de Madurez"]]
    for name, score in zip(SHORT_NAMES, scores):
        label, _ = get_maturity(score)
        rows.append([name, f"{score:.2f}", label])
    global_label, _ = get_maturity(global_score)
    rows.append(["GLOBAL", f"{global_score:.2f}", global_label])
    return "\n".join(",".join(r) for r in rows)


# ── Aplicación principal ──────────────────────────────────────────────────────

def build_css(dark: bool) -> str:
    if dark:
        bg          = "#080c14"
        sidebar_bg  = "linear-gradient(180deg,#0d1117 0%,#10151f 100%)"
        sidebar_txt = "#94a3b8"
        sidebar_hdr = "#e2e8f0"
        hero_bg     = "linear-gradient(135deg,#0d1117 0%,#131929 60%,#0d1117 100%)"
        hero_border = "rgba(78,205,196,0.18)"
        hero_glow   = "rgba(78,205,196,0.12)"
        hero_title  = "linear-gradient(135deg,#ffffff 30%,#4ECDC4 70%,#7C3AED 100%)"
        hero_sub    = "#64748b"
        card_bg     = "rgba(255,255,255,0.025)"
        card_border = "rgba(78,205,196,0.14)"
        desc_bg     = "linear-gradient(135deg,rgba(78,205,196,0.07),rgba(124,58,237,0.07))"
        desc_txt    = "#94a3b8"
        tab_bg      = "rgba(255,255,255,0.03)"
        tab_txt     = "#64748b"
        sec_txt     = "#f1f5f9"
        body_txt    = "#e2e8f0"
        input_bg    = "rgba(255,255,255,0.04)"
        input_txt   = "#e2e8f0"
        label_txt   = "#94a3b8"
        prog_track  = "rgba(255,255,255,0.06)"
        metric_bg   = "rgba(255,255,255,0.03)"
        metric_val  = "#e2e8f0"
        metric_lbl  = "#64748b"
        btn_sec_bg  = "rgba(255,255,255,0.05)"
        btn_sec_txt = "#94a3b8"
        btn_sec_bdr = "rgba(255,255,255,0.1)"
        hr_color    = "rgba(78,205,196,0.08)"
        markdown_txt= "#cbd5e1"
    else:
        bg          = "#f0f4f8"
        sidebar_bg  = "linear-gradient(180deg,#ffffff 0%,#f8fafc 100%)"
        sidebar_txt = "#475569"
        sidebar_hdr = "#0f172a"
        hero_bg     = "linear-gradient(135deg,#ffffff 0%,#f0f9ff 60%,#ffffff 100%)"
        hero_border = "rgba(14,165,233,0.25)"
        hero_glow   = "rgba(14,165,233,0.08)"
        hero_title  = "linear-gradient(135deg,#0f172a 20%,#0891b2 60%,#7C3AED 100%)"
        hero_sub    = "#64748b"
        card_bg     = "#ffffff"
        card_border = "rgba(14,165,233,0.18)"
        desc_bg     = "linear-gradient(135deg,rgba(14,165,233,0.07),rgba(124,58,237,0.07))"
        desc_txt    = "#475569"
        tab_bg      = "rgba(0,0,0,0.04)"
        tab_txt     = "#64748b"
        sec_txt     = "#0f172a"
        body_txt    = "#1e293b"
        input_bg    = "#f8fafc"
        input_txt   = "#0f172a"
        label_txt   = "#475569"
        prog_track  = "rgba(0,0,0,0.08)"
        metric_bg   = "#ffffff"
        metric_val  = "#0f172a"
        metric_lbl  = "#475569"
        btn_sec_bg  = "rgba(0,0,0,0.04)"
        btn_sec_txt = "#475569"
        btn_sec_bdr = "rgba(0,0,0,0.1)"
        hr_color    = "rgba(14,165,233,0.15)"
        markdown_txt= "#334155"

    accent = "#4ECDC4" if dark else "#0891b2"

    return f"""
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {{
        font-family: 'Inter', sans-serif !important;
        background: {bg} !important;
        color: {body_txt} !important;
    }}
    [data-testid="stAppViewContainer"] > .main {{ background: transparent; }}
    [data-testid="block-container"] {{ padding-top: 2rem; }}

    /* General text */
    p, span, div, li, td, th {{ color: {body_txt}; }}
    h1, h2, h3, h4, h5, h6 {{ color: {sec_txt} !important; }}
    .stMarkdown p, .stMarkdown li {{ color: {markdown_txt} !important; }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        border-right: 1px solid {hr_color} !important;
    }}
    [data-testid="stSidebar"] * {{ color: {sidebar_txt} !important; }}
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{ color: {sidebar_hdr} !important; }}

    /* Hero */
    .hero-header {{
        text-align: center;
        background: {hero_bg};
        border: 1px solid {hero_border};
        border-radius: 24px;
        padding: 52px 32px 44px;
        margin-bottom: 36px;
        position: relative;
        overflow: hidden;
        box-shadow: {'0 0 60px rgba(78,205,196,0.06)' if dark else '0 4px 32px rgba(0,0,0,0.06)'};
    }}
    .hero-header::before {{
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(ellipse 70% 60% at 50% -10%, {hero_glow} 0%, transparent 70%);
        pointer-events: none;
    }}
    .hero-title {{
        font-size: 2.8rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        background: {hero_title};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 12px;
    }}
    .hero-sub {{
        font-size: 1.05rem;
        color: {hero_sub};
        margin: 0;
        font-weight: 400;
        letter-spacing: 0.01em;
    }}
    .hero-badge {{
        display: inline-block;
        margin-top: 20px;
        background: linear-gradient(135deg,rgba(78,205,196,0.15),rgba(124,58,237,0.15));
        border: 1px solid rgba(78,205,196,0.3);
        border-radius: 50px;
        padding: 5px 18px;
        font-size: 0.78rem;
        color: {accent};
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-weight: 600;
    }}

    /* Cards */
    .glass-card {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 18px;
        padding: 28px 28px 20px;
        margin-bottom: 24px;
        {'backdrop-filter: blur(12px);' if dark else 'box-shadow: 0 2px 16px rgba(0,0,0,0.06);'}
    }}

    /* Pillar desc */
    .pillar-desc {{
        background: {desc_bg};
        border-left: 3px solid {accent};
        border-radius: 0 12px 12px 0;
        padding: 14px 20px;
        margin-bottom: 28px;
        color: {desc_txt};
        font-size: 0.97rem;
        font-style: italic;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 6px;
        background: {tab_bg};
        border-radius: 14px;
        padding: 5px;
        border: 1px solid {card_border};
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px !important;
        color: {tab_txt} !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        padding: 8px 14px !important;
        border: none !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg,rgba(78,205,196,0.2),rgba(124,58,237,0.2)) !important;
        color: {accent} !important;
        border: 1px solid rgba(78,205,196,0.3) !important;
    }}
    .stTabs [data-baseweb="tab-panel"] {{ padding-top: 20px; }}

    /* Buttons */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg,#4ECDC4 0%,#7C3AED 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 14px 28px !important;
        letter-spacing: 0.01em !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        opacity: 0.88 !important;
        box-shadow: 0 8px 30px rgba(78,205,196,0.35) !important;
    }}
    .stButton > button:not([kind="primary"]) {{
        background: {btn_sec_bg} !important;
        color: {btn_sec_txt} !important;
        border: 1px solid {btn_sec_bdr} !important;
        border-radius: 10px !important;
    }}

    /* Inputs */
    .stTextInput input, .stSelectbox > div > div {{
        background: {input_bg} !important;
        border: 1px solid {card_border} !important;
        border-radius: 10px !important;
        color: {input_txt} !important;
    }}
    .stTextInput input:focus {{
        border-color: {accent} !important;
        box-shadow: 0 0 0 3px rgba(78,205,196,0.12) !important;
    }}
    label[data-testid="stWidgetLabel"] p {{ color: {label_txt} !important; font-size: 0.85rem !important; }}

    /* Progress */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg,#4ECDC4,#7C3AED) !important;
        border-radius: 99px !important;
    }}
    .stProgress > div > div {{
        background: {prog_track} !important;
        border-radius: 99px !important;
        height: 6px !important;
    }}

    /* Metrics */
    [data-testid="stMetric"] {{
        background: {metric_bg} !important;
        border: 1px solid {card_border} !important;
        border-radius: 14px !important;
        padding: 16px 20px !important;
        {'box-shadow: 0 2px 8px rgba(0,0,0,0.06);' if not dark else ''}
    }}
    [data-testid="stMetricValue"] {{ color: {metric_val} !important; font-weight: 700 !important; }}
    [data-testid="stMetricDelta"] {{ color: {accent} !important; }}
    [data-testid="stMetricLabel"] p {{ color: {metric_lbl} !important; font-size: 0.82rem !important; }}

    /* Alerts */
    .stAlert {{
        border-radius: 12px !important;
        border: 1px solid {card_border} !important;
    }}

    /* Divider */
    hr {{ border-color: {hr_color} !important; margin: 28px 0 !important; }}

    /* Download buttons */
    [data-testid="stDownloadButton"] button {{
        background: {btn_sec_bg} !important;
        color: {btn_sec_txt} !important;
        border: 1px solid {card_border} !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
    }}

    /* ── Segmented control (botones de respuesta) ── */
    /* Contenedor */
    html body div[data-testid="stSegmentedControl"] {{
        gap: 4px !important;
    }}
    /* Todos los botones sin seleccionar — especificidad alta */
    html body div[data-testid="stSegmentedControl"] button,
    html body div[data-testid="stSegmentedControl"] button:not([aria-pressed="true"]) {{
        background: {'rgba(255,255,255,0.09)' if dark else '#e8edf2'} !important;
        color: {'#e2e8f0' if dark else '#1e293b'} !important;
        border: 1px solid {'rgba(78,205,196,0.25)' if dark else 'rgba(0,0,0,0.15)'} !important;
        border-radius: 8px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        padding: 7px 14px !important;
        transition: background 0.15s, color 0.15s !important;
    }}
    /* Texto dentro de los botones */
    html body div[data-testid="stSegmentedControl"] button p,
    html body div[data-testid="stSegmentedControl"] button span,
    html body div[data-testid="stSegmentedControl"] button div,
    html body div[data-testid="stSegmentedControl"] button label {{
        color: {'#e2e8f0' if dark else '#1e293b'} !important;
        background: transparent !important;
    }}
    /* Hover */
    html body div[data-testid="stSegmentedControl"] button:hover {{
        background: {'rgba(78,205,196,0.18)' if dark else 'rgba(8,145,178,0.12)'} !important;
        color: {accent} !important;
        border-color: {accent} !important;
    }}
    html body div[data-testid="stSegmentedControl"] button:hover p,
    html body div[data-testid="stSegmentedControl"] button:hover span {{
        color: {accent} !important;
    }}
    /* Seleccionado — múltiples selectores para cubrir todos los casos de Streamlit */
    html body div[data-testid="stSegmentedControl"] button[aria-pressed="true"],
    html body div[data-testid="stSegmentedControl"] button[data-selected="true"],
    html body div[data-testid="stSegmentedControl"] button[aria-checked="true"],
    html body div[data-testid="stSegmentedControl"] button[tabindex="0"]:focus,
    html body div[data-testid="stSegmentedControl"] button:active {{
        background: linear-gradient(135deg,#4ECDC4,#7C3AED) !important;
        color: #ffffff !important;
        border-color: transparent !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 14px rgba(78,205,196,0.4) !important;
    }}
    html body div[data-testid="stSegmentedControl"] button[aria-pressed="true"] p,
    html body div[data-testid="stSegmentedControl"] button[aria-pressed="true"] span,
    html body div[data-testid="stSegmentedControl"] button[aria-pressed="true"] div,
    html body div[data-testid="stSegmentedControl"] button[data-selected="true"] p,
    html body div[data-testid="stSegmentedControl"] button[data-selected="true"] span {{
        color: #ffffff !important;
        background: transparent !important;
    }}

    /* Hide Streamlit chrome */
    #MainMenu, footer {{ visibility: hidden; }}
    [data-testid="stToolbar"] {{ display: none; }}
    """


def section_title(icon: str, text: str, dark: bool = True):
    txt_color = "#f1f5f9" if dark else "#0f172a"
    line_color = "rgba(78,205,196,0.5)" if dark else "rgba(8,145,178,0.4)"
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin:36px 0 18px;">
        <span style="font-size:1.5rem;">{icon}</span>
        <span style="font-size:1.25rem;font-weight:700;color:{txt_color};letter-spacing:-0.01em;">{text}</span>
        <div style="flex:1;height:1px;background:linear-gradient(90deg,{line_color},transparent);margin-left:8px;"></div>
    </div>
    """, unsafe_allow_html=True)


def main():
    # ── Tema: debe leerse ANTES de renderizar cualquier widget ─────────────────
    dark = st.session_state.get("dark_mode", True)

    # Inyecta el CSS del tema actual
    st.markdown(f"<style>{build_css(dark)}</style>", unsafe_allow_html=True)

    # ── Hero Header ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero-header">
        <p class="hero-title">AI Maturity Radar</p>
        <p class="hero-sub">Evalúa el nivel de madurez de tu organización en adopción de Inteligencia Artificial</p>
        <span class="hero-badge">✦ Assessment Tool v1.0</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Barra lateral ──────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("⚙️ Configuración")

        # Toggle de tema
        st.toggle(
            "🌙 Modo oscuro" if dark else "☀️ Modo claro",
            value=dark,
            key="dark_mode",
            help="Cambia entre tema oscuro y claro",
        )

        st.divider()
        st.subheader("🔑 OpenAI API Key (opcional)")
        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder="sk-...",
            help="Añade tu clave para obtener un plan de acción generado con IA. Sin clave se usa análisis automático.",
        )
        if api_key:
            st.success("✅ API Key configurada")
        else:
            st.info("Sin API Key → análisis automático básico")

        st.divider()
        st.subheader("📊 Escala de Madurez")
        for _, _, label, _ in MATURITY_LEVELS:
            st.caption(label)

    # ── Estado de sesión ───────────────────────────────────────────────────────
    if "sliders" not in st.session_state:
        st.session_state.sliders = {}
    if "show_results" not in st.session_state:
        st.session_state.show_results = False

    # ── Perfil de la empresa ───────────────────────────────────────────────────
    section_title("🏢", "Perfil de la Empresa", dark)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    p_col1, p_col2, p_col3 = st.columns(3)
    with p_col1:
        company = st.text_input("Nombre de la empresa *", placeholder="Ej: MiEmpresa S.A.", key="p_company")
        evaluator = st.text_input("Nombre del evaluador", placeholder="Ej: Ana García", key="p_evaluator")
    with p_col2:
        role = st.text_input("Cargo / Rol", placeholder="Ej: Chief Digital Officer", key="p_role")
        email = st.text_input("Email de contacto", placeholder="ana@empresa.com", key="p_email")
    with p_col3:
        sector = st.selectbox("Sector / Industria", [
            "— Selecciona —", "Retail / Consumo", "Servicios Financieros / Banca",
            "Salud / Farmacéutico", "Manufactura / Industria", "Tecnología / Software",
            "Logística / Transporte", "Educación", "Energía / Utilities",
            "Telecomunicaciones", "Turismo / Hostelería", "Sector Público", "Otro",
        ], key="p_sector")
        country = st.selectbox("País", [
            "— Selecciona —", "España", "México", "Colombia", "Argentina", "Chile",
            "Perú", "Ecuador", "Estados Unidos", "Otro",
        ], key="p_country")

    p_col4, p_col5 = st.columns(2)
    with p_col4:
        employees = st.selectbox("Número de empleados", [
            "— Selecciona —", "1–10", "11–50", "51–200", "201–500",
            "501–1.000", "1.001–5.000", "Más de 5.000",
        ], key="p_employees")
    with p_col5:
        revenue = st.selectbox("Facturación anual aproximada", [
            "— Selecciona —", "Menos de 1M€", "1M€ – 10M€", "10M€ – 50M€",
            "50M€ – 200M€", "200M€ – 1.000M€", "Más de 1.000M€", "Prefiero no indicar",
        ], key="p_revenue")

    st.markdown('</div>', unsafe_allow_html=True)  # cierra glass-card

    # Recoge el perfil en un dict para usarlo en el export
    company_profile = {
        "empresa":      company or "Sin especificar",
        "evaluador":    evaluator or "—",
        "cargo":        role or "—",
        "email":        email or "—",
        "sector":       sector if sector != "— Selecciona —" else "—",
        "pais":         country if country != "— Selecciona —" else "—",
        "empleados":    employees if employees != "— Selecciona —" else "—",
        "facturacion":  revenue if revenue != "— Selecciona —" else "—",
    }

    # ── Instrucciones ──────────────────────────────────────────────────────────
    st.info(
        "📋 **Instrucciones**: Selecciona el nivel que mejor describe la realidad de tu organización. "
        "**1** = No existe · **2** = Inicial · **3** = En desarrollo · **4** = Avanzado · **5** = Optimizado"
    )

    # ── Formulario por pestañas ────────────────────────────────────────────────
    section_title("📝", "Cuestionario de Evaluación", dark)
    tabs = st.tabs(PILLAR_KEYS)

    raw_responses: dict[str, list[int]] = {}

    for tab, key in zip(tabs, PILLAR_KEYS):
        data = PILLARS[key]
        with tab:
            st.markdown(f'<div class="pillar-desc">{data["description"]}</div>', unsafe_allow_html=True)

            LABELS = {
                1: "1 · No existe",
                2: "2 · Inicial",
                3: "3 · En desarrollo",
                4: "4 · Avanzado",
                5: "5 · Optimizado",
            }

            pillar_vals: list[int] = []
            for q_idx, question in enumerate(data["questions"], start=1):
                sk = f"{key}_{q_idx}"
                st.markdown(f"**{q_idx}.** {question}")
                val = st.segmented_control(
                    label=f"nivel_{sk}",
                    options=[1, 2, 3, 4, 5],
                    default=st.session_state.sliders.get(sk, 3),
                    format_func=lambda x: LABELS[x],
                    key=sk,
                    label_visibility="collapsed",
                )
                if val is None:
                    val = st.session_state.sliders.get(sk, 3)
                st.session_state.sliders[sk] = val
                pillar_vals.append(val)
                st.write("")

            raw_responses[key] = pillar_vals

            # Vista previa del puntaje del pilar dentro de la pestaña
            avg_tab = sum(pillar_vals) / len(pillar_vals)
            label_tab, _ = get_maturity(avg_tab)
            st.divider()
            st.metric(f"Puntaje {data['short']}", f"{avg_tab:.2f} / 5.00", label_tab)

    # ── Botón de análisis ──────────────────────────────────────────────────────
    st.write("")
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        if st.button("🔍 Analizar Madurez en IA", type="primary", use_container_width=True):
            st.session_state.show_results = True
            st.session_state.raw_responses = raw_responses

    # ── Resultados ─────────────────────────────────────────────────────────────
    if st.session_state.show_results and "raw_responses" in st.session_state:
        saved = st.session_state.raw_responses
        scores = [
            sum(saved[k]) / len(saved[k])
            for k in PILLAR_KEYS
        ]
        global_score  = sum(scores) / len(scores)
        g_label, g_desc = get_maturity(global_score)
        weakest_idx   = scores.index(min(scores))

        st.divider()
        empresa_display = company_profile["empresa"]
        section_title("📊", f"Resultados — {empresa_display}", dark)

        # Métricas resumen
        c1, c2, c3 = st.columns(3)
        c1.metric("🎯 Puntaje Global",  f"{global_score:.2f} / 5.00")
        c2.metric("🏆 Nivel de Madurez", g_label)
        c3.metric("⚠️ Área Crítica",    SHORT_NAMES[weakest_idx])
        st.info(f"**Descripción del nivel**: {g_desc}")

        # Radar + barras de puntaje
        col_radar, col_bars = st.columns([3, 2])

        with col_radar:
            st.subheader("🕸️ Radar de Madurez")
            fig = build_radar_chart(scores, SHORT_NAMES)
            st.plotly_chart(fig, use_container_width=True)

        with col_bars:
            st.subheader("📈 Puntajes por Pilar")
            for name, score in zip(SHORT_NAMES, scores):
                label_p, _ = get_maturity(score)
                st.metric(name, f"{score:.2f} / 5.00", label_p)
                st.progress(score / 5.0)
                st.write("")

        # Plan de acción
        st.divider()
        section_title("🚀", "Plan de Acción", dark)

        with st.spinner("Generando recomendaciones…"):
            if api_key and OPENAI_AVAILABLE:
                try:
                    plan = action_plan_openai(scores, api_key, company_profile)
                    st.success("✅ Plan generado con IA (OpenAI GPT-4o-mini)")
                except Exception as exc:
                    st.warning(f"⚠️ Error con OpenAI ({exc}). Usando análisis automático.")
                    plan = action_plan_basic(scores)
            else:
                plan = action_plan_basic(scores)

        st.markdown(plan)

        # Exportar
        st.divider()
        section_title("💾", "Exportar Resultados", dark)

        responses_plain = {k: v for k, v in zip(SHORT_NAMES, [saved[pk] for pk in PILLAR_KEYS])}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "📥 Descargar JSON",
                data=to_json(responses_plain, scores, company_profile),
                file_name=f"ai_maturity_{timestamp}.json",
                mime="application/json",
                use_container_width=True,
            )
        with dl2:
            st.download_button(
                "📥 Descargar CSV",
                data=to_csv(scores),
                file_name=f"ai_maturity_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        # Botón de reset
        st.write("")
        if st.button("🔄 Nueva Evaluación"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


if __name__ == "__main__":
    main()
