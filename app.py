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
    "🏢 Impacto Negocio": {
        "short": "Impacto Negocio",
        "color": "#FF6B6B",
        "description": "Evaluación del valor de negocio generado por iniciativas de IA",
        "questions": [
            "¿Su organización ha identificado casos de uso de IA alineados con los objetivos estratégicos?",
            "¿Existe un mecanismo formal para medir el ROI de las iniciativas de IA?",
            "¿La dirección ejecutiva apoya activamente y patrocina los proyectos de IA?",
            "¿Ha implementado soluciones de IA que hayan generado valor de negocio tangible y medible?",
        ],
    },
    "⚙️ Tecnología": {
        "short": "Tecnología",
        "color": "#4ECDC4",
        "description": "Capacidad tecnológica para desarrollar y desplegar soluciones de IA",
        "questions": [
            "¿Su infraestructura tecnológica puede soportar el despliegue de modelos de IA a escala?",
            "¿Tiene capacidades de MLOps para gestionar el ciclo de vida completo de los modelos?",
            "¿Su organización utiliza herramientas de IA/ML modernas y actualizadas?",
            "¿Existe integración efectiva entre los sistemas de IA y las aplicaciones de negocio existentes?",
        ],
    },
    "🗄️ Data Management": {
        "short": "Data Management",
        "color": "#45B7D1",
        "description": "Gestión, calidad y accesibilidad de los datos para proyectos de IA",
        "questions": [
            "¿Sus datos están bien organizados, etiquetados y son accesibles para proyectos de IA?",
            "¿Cuenta con procesos establecidos de calidad y limpieza de datos?",
            "¿Tiene pipelines de datos automatizados para alimentar modelos de IA?",
            "¿Sus datos cumplen con los estándares de privacidad y seguridad requeridos?",
        ],
    },
    "⚖️ Gobierno": {
        "short": "Gobierno",
        "color": "#96CEB4",
        "description": "Marco de gobernanza, ética y cumplimiento regulatorio en IA",
        "questions": [
            "¿Tiene políticas claras de gobernanza para el uso responsable de la IA?",
            "¿Existe un marco de gestión de riesgos específico para proyectos de IA?",
            "¿Sus modelos de IA son auditables, transparentes y explicables?",
            "¿Cumple con las regulaciones de IA aplicables en su sector o industria?",
        ],
    },
    "🎓 Skills": {
        "short": "Skills",
        "color": "#FFEAA7",
        "description": "Capacidades humanas, talento y cultura de adopción de IA",
        "questions": [
            "¿Su equipo cuenta con habilidades técnicas (ML, data science, ingeniería de datos)?",
            "¿Existe un programa de capacitación continua en IA para su personal?",
            "¿Tiene acceso a talento especializado en IA cuando lo necesita (interno o externo)?",
            "¿La cultura organizacional fomenta activamente la experimentación y adopción de IA?",
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


def action_plan_openai(scores: list[float], api_key: str) -> str:
    """Plan de acción generado por GPT-4o-mini vía OpenAI API."""
    client = OpenAI(api_key=api_key)

    resumen = "\n".join(
        f"- {name}: {score:.2f}/5.0"
        for score, name in zip(scores, SHORT_NAMES)
    )
    global_score = sum(scores) / len(scores)

    prompt = f"""Eres un consultor experto en transformación digital e inteligencia artificial.

Una organización ha completado una evaluación de madurez en IA con estos resultados:

{resumen}
Puntaje global: {global_score:.2f}/5.0

Genera un Plan de Acción ejecutivo en español con las siguientes secciones:
1. **Diagnóstico Ejecutivo** (2–3 oraciones sobre el estado actual)
2. **Fortalezas a Capitalizar** (basadas en los puntajes más altos)
3. **Áreas Críticas de Mejora** (los 2 pilares más débiles con acciones específicas)
4. **Hoja de Ruta de 90 días** (5 acciones concretas y priorizadas)
5. **KPIs de Seguimiento** (4 métricas para medir el progreso)

Sé específico, accionable y usa lenguaje ejecutivo. Usa formato Markdown."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
        temperature=0.7,
    )
    return response.choices[0].message.content


def to_json(responses: dict, scores: list[float], company: str) -> str:
    """Serializa los resultados en formato JSON para descarga."""
    label, _ = get_maturity(sum(scores) / len(scores))
    data = {
        "metadata": {
            "empresa": company or "Sin especificar",
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

def main():
    # CSS mínimo para mejorar la apariencia
    st.markdown("""
    <style>
    .radar-header {
        text-align: center;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 14px;
        padding: 28px 20px;
        margin-bottom: 28px;
    }
    .pillar-desc {
        background: rgba(255,255,255,0.04);
        border-left: 4px solid #4ECDC4;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 18px;
        color: #aaa;
        font-size: 0.92rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Encabezado
    st.markdown("""
    <div class="radar-header">
        <h1 style="color:white; font-size:2.4rem; margin:0;">🤖 AI Maturity Radar</h1>
        <p style="color:#4ECDC4; font-size:1.05rem; margin:10px 0 0;">
            Evalúa el nivel de madurez de tu organización en adopción de Inteligencia Artificial
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Barra lateral ──────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("⚙️ Configuración")
        company = st.text_input("🏢 Nombre de la empresa", placeholder="Ej: MiEmpresa S.A.")

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

    # ── Instrucciones ──────────────────────────────────────────────────────────
    st.info(
        "📋 **Instrucciones**: Selecciona el nivel que mejor describe la realidad de tu organización. "
        "**1** = No existe · **2** = Inicial · **3** = En desarrollo · **4** = Avanzado · **5** = Optimizado"
    )

    # ── Formulario por pestañas ────────────────────────────────────────────────
    st.header("📝 Cuestionario de Evaluación")
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
        st.header("📊 Resultados del Análisis")

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
        st.header("🚀 Plan de Acción")

        with st.spinner("Generando recomendaciones…"):
            if api_key and OPENAI_AVAILABLE:
                try:
                    plan = action_plan_openai(scores, api_key)
                    st.success("✅ Plan generado con IA (OpenAI GPT-4o-mini)")
                except Exception as exc:
                    st.warning(f"⚠️ Error con OpenAI ({exc}). Usando análisis automático.")
                    plan = action_plan_basic(scores)
            else:
                plan = action_plan_basic(scores)

        st.markdown(plan)

        # Exportar
        st.divider()
        st.header("💾 Exportar Resultados")

        responses_plain = {k: v for k, v in zip(SHORT_NAMES, [saved[pk] for pk in PILLAR_KEYS])}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "📥 Descargar JSON",
                data=to_json(responses_plain, scores, company),
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
