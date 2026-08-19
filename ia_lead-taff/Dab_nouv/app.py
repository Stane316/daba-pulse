"""
================================================================================
DABA · REVENUE-AT-RISK DECISION ENGINE — COCKPIT
================================================================================
Interface Streamlit "command center" : l'IA se déclenche automatiquement dès
que des données sont chargées et affiche un briefing exécutif directement sur
le tableau de bord, sans action manuelle requise (façon Stripe Radar / Linear
Insights).

Le chat reste disponible pour aller plus loin. Un nouvel onglet "Challenge
la décision" transforme l'IA d'une interface d'EXPLICATION passive en une
interface de MISE À L'ÉPREUVE de la décision :

    Décision -> Question -> Simulation -> Comparaison -> Contre-argument

Il consomme le endpoint /challenge du backend, qui :
    - reconnaît l'intention de la question (pas de simple mot-clé),
    - délègue tout nouveau calcul au Simulation Engine déterministe
      (l'IA ne simule JAMAIS elle-même),
    - restitue une réponse en 4 blocs distincts : Faits / Hypothèses /
      Interprétation / Incertitude — jamais fusionnés, pour que le
      dirigeant voie "voici les résultats, voici pourquoi j'en déduis
      cela" plutôt qu'un texte d'autorité.

Version: 5.0 — Decision Challenge Edition
Date: 18 août 2026
================================================================================
"""

import os
import json
import time
import hashlib
import requests
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from typing import Dict, Any, List, Optional

# ============================================================================
# 1. CONFIGURATION DE LA PAGE
# ============================================================================

st.set_page_config(
    page_title="DABA · Revenue-at-Risk Cockpit",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ============================================================================
# 2. TOKENS DE DESIGN
# ============================================================================

BG_PRIMARY    = "#0A0E14"
BG_SURFACE    = "#12161F"
BG_SURFACE_2  = "#1A1F2B"
BG_SURFACE_3  = "#20263A"
BORDER        = "#232838"
BORDER_SOFT   = "#1C2130"
TEXT_PRIMARY  = "#EDEFF3"
TEXT_SECONDARY= "#8B93A7"
TEXT_MUTED    = "#5A6178"

ACCENT_PRIMARY = "#5B8CFF"   # IA / actions / marque
ACCENT_RISK    = "#FF5C5C"   # danger
ACCENT_WARNING = "#F5A623"   # attention (ochre/mangue — pas de terracotta cliché)
ACCENT_SAFE    = "#34D399"   # succès / OK
ACCENT_GROQ    = "#B583FF"   # violet pour Groq
ACCENT_CHALLENGE = "#F5A623" # couleur distincte pour la couche "challenge"

PROVIDER_META = {
    "gemini":   {"label": "Gemini",     "color": ACCENT_PRIMARY, "dot": "●"},
    "groq":     {"label": "Groq",       "color": ACCENT_GROQ,    "dot": "●"},
    "fallback": {"label": "Analytique", "color": TEXT_SECONDARY, "dot": "●"},
    "error":    {"label": "Erreur",     "color": ACCENT_RISK,    "dot": "●"},
}

INTENT_META = {
    "EXPLAIN":     {"label": "Explication",  "icon": "💡"},
    "CHALLENGE":   {"label": "Contre-argument", "icon": "🧪"},
    "COMPARE":     {"label": "Comparaison",  "icon": "🔄"},
    "ALTERNATIVE": {"label": "Alternative",  "icon": "🧭"},
    "JUSTIFY":     {"label": "Justification","icon": "⚖️"},
    "RESUME":      {"label": "Résumé",       "icon": "📝"},
    "LIMITS":      {"label": "Limites",      "icon": "⚠️"},
}

# Situations simulables exposées par le backend (GET /situations).
# Fallback statique si l'API est injoignable au moment du rendu de la sidebar.
DEFAULT_SITUATIONS = {
    "cotonou_distribution": "Distribution — Boutique Cotonou",
    "reputation_globale": "Réputation — Visibilité globale",
}

# ============================================================================
# 3. CSS
# ============================================================================

def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background: {BG_PRIMARY};
        color: {TEXT_PRIMARY};
    }}

    section[data-testid="stSidebar"] {{
        background: {BG_SURFACE};
        border-right: 1px solid {BORDER};
    }}
    section[data-testid="stSidebar"] * {{
        color: {TEXT_PRIMARY};
    }}

    h1, h2, h3, h4 {{
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.01em;
    }}

    p, span, label, div {{
        color: {TEXT_PRIMARY};
    }}

    /* ---- Header ---- */
    .cockpit-header {{
        display: flex; align-items: baseline; justify-content: space-between;
        border-bottom: 1px solid {BORDER}; padding-bottom: 18px; margin-bottom: 4px;
    }}
    .cockpit-title {{
        font-family: 'Space Grotesk', sans-serif; font-weight: 700;
        font-size: 28px; color: {TEXT_PRIMARY}; margin: 0;
    }}
    .cockpit-subtitle {{
        font-size: 13px; color: {TEXT_SECONDARY}; margin-top: 2px;
    }}
    .cockpit-date {{
        font-family: 'JetBrains Mono', monospace; font-size: 12px;
        color: {TEXT_MUTED};
    }}

    /* ---- Status pulse ---- */
    .status-row {{ display:flex; align-items:center; gap:8px; font-size:13px; }}
    .pulse-dot {{
        width:8px; height:8px; border-radius:50%; display:inline-block;
        position: relative;
    }}
    .pulse-dot.online {{ background:{ACCENT_SAFE}; box-shadow:0 0 0 rgba(52,211,153,0.5); animation: pulse 2s infinite; }}
    .pulse-dot.offline {{ background:{ACCENT_RISK}; }}
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(52,211,153,0.45); }}
        70% {{ box-shadow: 0 0 0 6px rgba(52,211,153,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(52,211,153,0); }}
    }}
    .provider-chip {{
        display:inline-flex; align-items:center; gap:6px;
        font-size:11.5px; font-family:'JetBrains Mono',monospace;
        padding:3px 8px; border-radius:20px; border:1px solid {BORDER};
        background:{BG_SURFACE_2}; color:{TEXT_SECONDARY};
    }}

    /* ---- KPI cards ---- */
    .kpi-card {{
        background: {BG_SURFACE}; border: 1px solid {BORDER}; border-radius: 12px;
        padding: 18px 20px; height: 100%;
    }}
    .kpi-label {{
        font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.06em;
        color: {TEXT_SECONDARY}; margin-bottom: 10px; font-weight: 500;
    }}
    .kpi-value {{
        font-family: 'JetBrains Mono', monospace; font-size: 24px; font-weight: 600;
        color: {TEXT_PRIMARY}; line-height:1.1;
    }}
    .kpi-sub {{ font-size: 12px; margin-top: 8px; }}
    .kpi-sub.risk {{ color: {ACCENT_RISK}; }}
    .kpi-sub.safe {{ color: {ACCENT_SAFE}; }}
    .kpi-sub.warn {{ color: {ACCENT_WARNING}; }}
    .kpi-sub.neutral {{ color: {TEXT_SECONDARY}; }}

    /* ---- AI Briefing (signature element) ---- */
    .briefing-card {{
        background: linear-gradient(160deg, {BG_SURFACE_2} 0%, {BG_SURFACE} 100%);
        border: 1px solid {BORDER}; border-left: 3px solid {ACCENT_PRIMARY};
        border-radius: 14px; padding: 22px 24px; margin: 6px 0 20px 0;
        animation: briefing-in 480ms cubic-bezier(0.16, 1, 0.3, 1);
    }}
    @keyframes briefing-in {{
        from {{ opacity: 0; transform: translateY(6px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .briefing-eyebrow {{
        display:flex; align-items:center; justify-content:space-between; margin-bottom:14px;
    }}
    .briefing-label {{
        font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.08em;
        color: {ACCENT_PRIMARY}; font-weight: 600;
    }}
    .briefing-meta {{
        font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {TEXT_MUTED};
    }}
    .briefing-body {{ font-size: 14.5px; line-height: 1.65; color: {TEXT_PRIMARY}; }}
    .briefing-body strong {{ color: {TEXT_PRIMARY}; font-family:'Space Grotesk',sans-serif; }}
    .briefing-body ul {{ margin: 6px 0 6px 18px; padding: 0; }}
    .briefing-body li {{ margin-bottom: 4px; color: {TEXT_PRIMARY}; }}

    /* ---- Risk / recommendation list items ---- */
    .item-card {{
        display:flex; gap:10px; align-items:flex-start;
        background:{BG_SURFACE}; border:1px solid {BORDER}; border-radius:10px;
        padding: 12px 14px; margin-bottom: 8px; font-size: 13.5px; line-height:1.45;
    }}
    .item-card .marker {{ font-size: 14px; margin-top:1px; flex-shrink:0; }}
    .item-card.risk {{ border-left: 3px solid {ACCENT_RISK}; }}
    .item-card.reco {{ border-left: 3px solid {ACCENT_SAFE}; }}

    /* ---- Section titles ---- */
    .section-title {{
        font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 15px;
        color: {TEXT_PRIMARY}; margin: 22px 0 12px 0; display:flex; align-items:center; gap:8px;
    }}

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {BORDER}; }}
    .stTabs [data-baseweb="tab"] {{
        background: transparent; border-radius: 8px 8px 0 0; color: {TEXT_SECONDARY};
        font-family: 'Space Grotesk', sans-serif; font-size: 14px; padding: 8px 4px;
    }}
    .stTabs [aria-selected="true"] {{
        color: {TEXT_PRIMARY} !important; border-bottom: 2px solid {ACCENT_PRIMARY};
    }}

    /* ---- Buttons ---- */
    .stButton>button {{
        background: {BG_SURFACE_2}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER};
        border-radius: 8px; font-family:'Inter',sans-serif; font-weight:500; font-size:13px;
        transition: all 0.15s ease;
    }}
    .stButton>button:hover {{
        border-color: {ACCENT_PRIMARY}; color: {ACCENT_PRIMARY};
        background: {BG_SURFACE_3};
    }}
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {{
        background: {BG_SURFACE}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER};
        border-radius: 8px;
    }}

    /* ---- Chat bubbles ---- */
    .chat-bubble {{
        border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; font-size: 13.8px;
        line-height: 1.55; max-width: 92%;
    }}
    .chat-bubble.user {{
        background: {BG_SURFACE_3}; border: 1px solid {BORDER}; margin-left: auto;
    }}
    .chat-bubble.assistant {{
        background: {BG_SURFACE}; border: 1px solid {BORDER}; border-left: 3px solid {ACCENT_PRIMARY};
    }}
    .chat-role {{ font-size: 10.5px; text-transform:uppercase; letter-spacing:0.05em;
        color:{TEXT_MUTED}; margin-bottom:5px; font-family:'JetBrains Mono',monospace; }}

    /* ---- Decision Challenge — blocs Faits / Hypothèses / Incertitude ---- */
    .challenge-card {{
        background: linear-gradient(160deg, {BG_SURFACE_2} 0%, {BG_SURFACE} 100%);
        border: 1px solid {BORDER}; border-left: 3px solid {ACCENT_CHALLENGE};
        border-radius: 14px; padding: 20px 22px; margin: 10px 0 18px 0;
    }}
    .challenge-eyebrow {{
        display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;
    }}
    .challenge-intent-badge {{
        font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:600;
        padding:3px 10px; border-radius:20px; background:{BG_SURFACE_3};
        color:{ACCENT_CHALLENGE}; border:1px solid {ACCENT_CHALLENGE}55;
    }}
    .challenge-sim-badge {{
        font-family:'JetBrains Mono',monospace; font-size:10.5px;
        padding:2px 8px; border-radius:20px; margin-left:6px;
    }}
    .challenge-sim-badge.on {{ background:{ACCENT_SAFE}22; color:{ACCENT_SAFE}; border:1px solid {ACCENT_SAFE}55; }}
    .challenge-sim-badge.off {{ background:{BG_SURFACE_3}; color:{TEXT_MUTED}; border:1px solid {BORDER}; }}

    .challenge-block-title {{
        font-size: 11px; text-transform: uppercase; letter-spacing: 0.07em;
        font-weight: 600; margin: 14px 0 8px 0; display:flex; align-items:center; gap:6px;
    }}
    .challenge-block-title.faits {{ color: {ACCENT_SAFE}; }}
    .challenge-block-title.hypotheses {{ color: {ACCENT_WARNING}; }}
    .challenge-block-title.interpretation {{ color: {ACCENT_PRIMARY}; }}
    .challenge-block-title.incertitude {{ color: {ACCENT_RISK}; }}

    .challenge-list {{ margin: 0 0 4px 0; padding: 0; list-style:none; }}
    .challenge-list li {{
        font-size: 13px; line-height: 1.5; color: {TEXT_PRIMARY};
        padding: 5px 0 5px 16px; position: relative; border-bottom: 1px solid {BORDER_SOFT};
    }}
    .challenge-list li:last-child {{ border-bottom: none; }}
    .challenge-list li:before {{
        content: "—"; position: absolute; left: 0; color: {TEXT_MUTED};
    }}
    .challenge-interpretation-body {{
        font-size: 14px; line-height: 1.6; color: {TEXT_PRIMARY};
        background: {BG_SURFACE_3}; border-radius: 10px; padding: 12px 14px;
    }}

    .stMetric {{ background: transparent; }}
    hr {{ border-color: {BORDER}; }}
    #MainMenu, footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)


def plotly_dark_layout(fig, height=380):
    fig.update_layout(
        height=height,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT_SECONDARY, size=12),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=40, l=10, r=10, b=10),
    )
    return fig

# ============================================================================
# 4. API HELPERS
# ============================================================================

def check_api_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        return response.json()
    except Exception:
        return {"status": "unreachable", "providers": {}}

def get_demo_data():
    try:
        response = requests.get(f"{API_URL}/demo-data", timeout=5)
        return response.json()
    except Exception:
        return {}

def get_stats():
    try:
        response = requests.get(f"{API_URL}/stats", timeout=3)
        return response.json()
    except Exception:
        return {}

def get_situations() -> Dict[str, str]:
    """Récupère la liste des situations simulables depuis le backend
    (GET /situations). Repli sur la liste statique si l'API est injoignable,
    pour que l'onglet Challenge reste utilisable même hors connexion."""
    try:
        response = requests.get(f"{API_URL}/situations", timeout=3)
        data = response.json()
        if data:
            return {sid: DEFAULT_SITUATIONS.get(sid, sid) for sid in data}
    except Exception:
        pass
    return DEFAULT_SITUATIONS

def send_chat_message(messages, context_data=None, prompt_type="general_assistant"):
    try:
        payload = {
            "messages": messages,
            "context_data": context_data or {},
            "prompt_type": prompt_type,
            "max_tokens": 2048
        }
        response = requests.post(f"{API_URL}/chat", json=payload, timeout=45)
        return response.json()
    except Exception as e:
        return {"success": False, "content": f"❌ Erreur de connexion: {str(e)}", "provider_used": "error"}

def compare_scenarios(before, after, context=None):
    try:
        payload = {"before": before, "after": after, "context_data": context or {}}
        response = requests.post(f"{API_URL}/compare-scenarios", json=payload, timeout=45)
        return response.json()
    except Exception as e:
        return {"success": False, "content": f"❌ Erreur: {str(e)}", "provider_used": "error"}

def send_challenge_request(question: str, context_data: Dict[str, Any],
                            situation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Appelle POST /challenge — la boucle complète Décision -> Question ->
    Simulation -> Comparaison -> Contre-argument. Ne fait AUCUN calcul
    côté frontend : tout est délégué au backend (Simulation Engine +
    reconnaissance d'intention + LLM d'interprétation).
    """
    try:
        payload = {
            "question": question,
            "context_data": context_data or {},
            "situation_id": situation_id,
        }
        response = requests.post(f"{API_URL}/challenge", json=payload, timeout=45)
        response.raise_for_status()
        return {"success": True, **response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _data_hash(data: Dict[str, Any]) -> str:
    return hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()

def get_briefing(data: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
    """Déclenche automatiquement le briefing exécutif de l'IA pour ces données.
    Mis en cache par empreinte des données : ne rappelle le modèle que si les
    données changent (ou si force=True), pas à chaque re-render Streamlit."""
    h = _data_hash(data)
    cached = st.session_state.get("briefing_cache", {})
    if not force and cached.get("hash") == h:
        return cached["result"]

    messages = [{"role": "user", "content": "Génère le briefing exécutif du jour."}]
    result = send_chat_message(messages, context_data=data, prompt_type="executive_briefing")
    st.session_state["briefing_cache"] = {"hash": h, "result": result, "ts": datetime.now()}
    return result

def get_scenario_briefing(before, after, context, force: bool = False) -> Dict[str, Any]:
    h = _data_hash({"before": before, "after": after})
    cached = st.session_state.get("scenario_cache", {})
    if not force and cached.get("hash") == h:
        return cached["result"]
    result = compare_scenarios(before, after, context)
    st.session_state["scenario_cache"] = {"hash": h, "result": result, "ts": datetime.now()}
    return result

# ============================================================================
# 5. DONNÉES DE DÉMONSTRATION LOCALES (fallback si API indisponible)
# ============================================================================

LOCAL_DEMO_DATA = {
    "revenue_at_risk": {"total": 550800, "distribution": 486000, "reputation": 64800},
    "risks": [
        "Rupture de stock imminente à la boutique Cotonou (déficit: 27 unités)",
        "Note Google moyenne < 3,5 (actuelle: 2,5/5)",
        "Engagement sur réseaux sociaux < 1% (actuel: 0.8%)",
        "Absence d'avis Google (3 avis seulement)",
        "Faible visibilité sur Google (15 recherches/jour)",
    ],
    "recommendations": [
        "Réapprovisionner la boutique Cotonou avec 30 unités",
        "Lancer une campagne de collecte d'avis (SMS/email)",
        "Optimiser la stratégie de contenu sur les réseaux sociaux",
        "Mettre à jour la fiche Google My Business",
    ],
    "simulation": {
        "before": {
            "rar": 550800, "stock_health": 45, "reputation_score": 2.5,
            "stores": [
                {"name": "Cotonou", "stock": 8, "demand": 35, "deficit": 27},
                {"name": "Parakou", "stock": 15, "demand": 20, "deficit": 5},
                {"name": "Lomé", "stock": 25, "demand": 15, "surplus": 10},
            ]
        },
        "after": {
            "rar": 0, "stock_health": 95, "reputation_score": 4.5,
            "stores": [
                {"name": "Cotonou", "stock": 38, "demand": 35, "status": "OK"},
                {"name": "Parakou", "stock": 20, "demand": 20, "status": "OK"},
                {"name": "Lomé", "stock": 15, "demand": 15, "status": "OK"},
            ]
        },
        "reduction": 550800, "improvement": 50, "additional_demand": 20
    }
}

# ============================================================================
# 6. SIDEBAR
# ============================================================================

def render_sidebar():
    with st.sidebar:
        st.markdown("""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:2px;">
                <div style="font-size:22px;">🛰️</div>
                <div>
                    <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:16px;">DABA</div>
                    <div style="font-size:11px;color:#8B93A7;">Revenue-at-Risk Cockpit</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<hr style='margin:14px 0;'>", unsafe_allow_html=True)

        health = check_api_health()
        online = health.get("status") in ("healthy", "degraded")
        st.markdown(f"""
            <div class="status-row">
                <span class="pulse-dot {'online' if online else 'offline'}"></span>
                <span style="color:{'#EDEFF3' if online else '#FF5C5C'};font-weight:500;">
                    {'API connectée' if online else 'API déconnectée'}
                </span>
            </div>
        """, unsafe_allow_html=True)

        if online:
            chips = ""
            for name, available in health.get("providers", {}).items():
                meta = PROVIDER_META.get(name, {"label": name.capitalize(), "color": TEXT_SECONDARY})
                color = meta["color"] if available else TEXT_MUTED
                chips += f'<span class="provider-chip" style="color:{color};border-color:{color}44;">● {meta["label"]}</span> '
            st.markdown(f"<div style='margin-top:10px;'>{chips}</div>", unsafe_allow_html=True)
            if health.get("status") == "degraded":
                st.caption("⚠ Aucun LLM actif — le système répond en mode analytique (fallback).")
        else:
            st.caption("Lancez le backend : `python main.py`")

        st.markdown("<hr style='margin:16px 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:12px;color:#8B93A7;font-weight:500;margin-bottom:8px;'>ACTIVITÉ IA</div>", unsafe_allow_html=True)
        stats = get_stats()
        if stats and stats.get("total_requests", 0) > 0:
            c1, c2 = st.columns(2)
            c1.metric("Requêtes", stats.get("total_requests", 0))
            c2.metric("Succès", f"{stats.get('success_rate', 0)*100:.0f}%")
            st.caption(
                f"Gemini {stats.get('gemini_share',0)*100:.0f}% · "
                f"Groq {stats.get('groq_share',0)*100:.0f}% · "
                f"Fallback {stats.get('fallback_share',0)*100:.0f}%"
            )
        else:
            st.caption("En attente de la première requête…")

        st.markdown("<hr style='margin:16px 0;'>", unsafe_allow_html=True)
        if st.button("↻  Réinitialiser la session", use_container_width=True):
            for k in ["messages", "briefing_cache", "scenario_cache", "challenge_history"]:
                st.session_state.pop(k, None)
            st.rerun()
        if st.button("⟳  Recharger les données", use_container_width=True):
            data = get_demo_data() or LOCAL_DEMO_DATA
            st.session_state.context_data = data
            for k in ["briefing_cache", "scenario_cache"]:
                st.session_state.pop(k, None)
            st.rerun()

        st.markdown("<hr style='margin:16px 0;'>", unsafe_allow_html=True)
        st.caption("DABA © 2026 · Mission 2: Branding & Growth")

# ============================================================================
# 7. BRIEFING IA (auto-déclenché)
# ============================================================================

def render_briefing(data: Dict[str, Any]):
    """Le cœur du cockpit : ce briefing se génère tout seul dès que les
    données sont disponibles — aucune action de l'utilisateur requise."""
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(f"""
            <div class="briefing-card">
                <div class="briefing-eyebrow">
                    <span class="briefing-label">◆ Briefing IA — généré automatiquement</span>
                    <span class="briefing-meta">analyse en cours…</span>
                </div>
                <div class="briefing-body" style="color:{TEXT_MUTED};">
                    Lecture des indicateurs, croisement des risques et calcul de la
                    recommandation prioritaire…
                </div>
            </div>
        """, unsafe_allow_html=True)

    result = get_briefing(data)
    provider = result.get("provider_used", "fallback")
    meta = PROVIDER_META.get(provider, PROVIDER_META["fallback"])
    ts = st.session_state.get("briefing_cache", {}).get("ts", datetime.now())
    content = result.get("content") if result.get("success") else (
        "Impossible de générer le briefing pour le moment. "
        f"({result.get('content', 'erreur inconnue')})"
    )

    with placeholder.container():
        st.markdown(f"""
            <div class="briefing-card">
                <div class="briefing-eyebrow">
                    <span class="briefing-label">◆ Briefing IA — généré automatiquement</span>
                    <span class="briefing-meta">
                        <span style="color:{meta['color']};">{meta['dot']}</span> {meta['label']} · {ts.strftime('%H:%M:%S')}
                    </span>
                </div>
                <div class="briefing-body">{content}</div>
            </div>
        """, unsafe_allow_html=True)

    cols = st.columns([1, 1, 6])
    with cols[0]:
        if st.button("↻ Régénérer", key="regen_briefing"):
            get_briefing(data, force=True)
            st.rerun()

# ============================================================================
# 8. DASHBOARD
# ============================================================================

def kpi_card(label, value, sub, tone="neutral"):
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub {tone}">{sub}</div>
        </div>
    """, unsafe_allow_html=True)

def render_dashboard(data):
    if not data:
        st.warning("⚠️ Aucune donnée disponible.")
        return

    rar = data.get("revenue_at_risk", {})
    sim = data.get("simulation", {})

    # Briefing auto-déclenché — le point d'entrée du cockpit
    render_briefing(data)

    st.markdown('<div class="section-title">📈 Indicateurs clés</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Revenue-at-Risk total", f"{rar.get('total', 0):,.0f} FCFA".replace(",", " "),
                  "⚠ Risque à couvrir", "risk")
    with c2:
        kpi_card("Risque distribution", f"{rar.get('distribution', 0):,.0f} FCFA".replace(",", " "),
                  "Ruptures de stock", "warn")
    with c3:
        kpi_card("Risque réputation", f"{rar.get('reputation', 0):,.0f} FCFA".replace(",", " "),
                  "Visibilité & avis", "warn")
    with c4:
        reduction = sim.get("reduction", 0)
        kpi_card("Impact simulation", f"{reduction:,.0f} FCFA".replace(",", " "),
                  f"↑ +{sim.get('improvement', 0)}% si actions appliquées", "safe")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">⚠ Risques détectés</div>', unsafe_allow_html=True)
        risks = data.get("risks", [])
        if risks:
            for r in risks:
                st.markdown(f'<div class="item-card risk"><span class="marker">▲</span><span>{r}</span></div>', unsafe_allow_html=True)
        else:
            st.caption("Aucun risque majeur détecté.")
    with col2:
        st.markdown('<div class="section-title">✓ Recommandations</div>', unsafe_allow_html=True)
        recos = data.get("recommendations", [])
        if recos:
            for r in recos:
                st.markdown(f'<div class="item-card reco"><span class="marker">→</span><span>{r}</span></div>', unsafe_allow_html=True)
        else:
            st.caption("Aucune recommandation pour le moment.")

    st.markdown('<div class="section-title">📊 Visualisation</div>', unsafe_allow_html=True)
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Répartition du Revenue-at-Risk", "Comparaison avant / après"),
        specs=[[{"type": "pie"}, {"type": "bar"}]]
    )
    fig.add_trace(go.Pie(
        labels=["Distribution", "Réputation"],
        values=[rar.get("distribution", 0), rar.get("reputation", 0)],
        marker=dict(colors=[ACCENT_WARNING, ACCENT_RISK]),
        textinfo="label+percent", hole=0.55,
        textfont=dict(color=TEXT_PRIMARY),
    ), row=1, col=1)

    before, after = sim.get("before", {}), sim.get("after", {})
    if before and after:
        metrics = ["RAR (×10k)", "Santé stock", "Réputation"]
        before_v = [before.get("rar", 0)/10000, before.get("stock_health", 0), before.get("reputation_score", 0)]
        after_v  = [after.get("rar", 0)/10000, after.get("stock_health", 0), after.get("reputation_score", 0)]
        fig.add_trace(go.Bar(name="Avant", x=metrics, y=before_v, marker_color=ACCENT_RISK), row=1, col=2)
        fig.add_trace(go.Bar(name="Après", x=metrics, y=after_v, marker_color=ACCENT_SAFE), row=1, col=2)

    st.plotly_chart(plotly_dark_layout(fig), use_container_width=True, config={"displayModeBar": False})

# ============================================================================
# 9. CHAT
# ============================================================================

def render_chat_interface():
    st.markdown('<div class="section-title">💬 Aller plus loin avec l\'assistant</div>', unsafe_allow_html=True)
    st.caption("Le briefing du tableau de bord est déjà généré automatiquement — utilisez ce chat pour creuser un point précis. "
               "Pour tester ou contredire une décision, préférez l'onglet **🧪 Challenger la décision**.")

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Le briefing du jour est visible sur le Dashboard. Vous pouvez me demander un détail : "
                        "un risque en particulier, une action alternative, ou une simulation.",
            "provider": None
        }]
    if "context_data" not in st.session_state:
        st.session_state.context_data = LOCAL_DEMO_DATA

    for msg in st.session_state.messages:
        role = msg["role"]
        if role == "user":
            st.markdown(f'<div class="chat-bubble user"><div class="chat-role">Vous</div>{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            meta = PROVIDER_META.get(msg.get("provider"), {"label": "", "color": TEXT_MUTED})
            tag = f'<span style="color:{meta["color"]};">· {meta["label"]}</span>' if msg.get("provider") else ""
            st.markdown(f'<div class="chat-bubble assistant"><div class="chat-role">Assistant {tag}</div>{msg["content"]}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
    cols = st.columns(4)
    quick_questions = [
        ("📊 Risques", "Quels sont mes principaux risques ?"),
        ("💡 Action", "Que devrais-je faire en priorité ?"),
        ("🔄 Simulation", "Compare les scénarios pour moi"),
        ("📈 Réputation", "Comment améliorer ma réputation ?")
    ]
    triggered = None
    for idx, (label, question) in enumerate(quick_questions):
        with cols[idx]:
            if st.button(label, key=f"quick_{idx}", use_container_width=True):
                triggered = question

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([6, 1])
    with col1:
        user_input = st.text_input("Message", placeholder="Ex: Explique-moi le risque de distribution…",
                                    key="chat_input", label_visibility="collapsed")
    with col2:
        send = st.button("Envoyer →", key="send_btn", use_container_width=True)

    final_input = triggered or (user_input if send and user_input else None)
    if final_input:
        st.session_state.messages.append({"role": "user", "content": final_input, "provider": None})
        with st.spinner("Analyse en cours…"):
            messages_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-6:]]
            response = send_chat_message(messages_for_api, st.session_state.context_data, "general_assistant")
        if response.get("success"):
            st.session_state.messages.append({
                "role": "assistant", "content": response.get("content", "Aucune réponse"),
                "provider": response.get("provider_used", "unknown")
            })
        else:
            st.session_state.messages.append({
                "role": "assistant", "content": f"❌ {response.get('content', 'Erreur inconnue')}", "provider": "error"
            })
        st.rerun()

# ============================================================================
# 10. SIMULATION (comparaison avant/après générique du dashboard)
# ============================================================================

def render_simulation(data):
    st.markdown('<div class="section-title">🔄 Simulation de scénarios</div>', unsafe_allow_html=True)

    sim = data.get("simulation", {})
    before, after = sim.get("before", {}), sim.get("after", {})
    if not before or not after:
        st.warning("Aucune simulation disponible.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📉 Scénario actuel**")
        st.metric("Revenue-at-Risk", f"{before.get('rar', 0):,.0f} FCFA".replace(",", " "))
        st.metric("Santé des stocks", f"{before.get('stock_health', 0)}%")
        st.metric("Score réputation", f"{before.get('reputation_score', 0)}/5")
        for s in before.get("stores", []):
            status = "🔴 Rupture" if s.get("deficit", 0) > 0 else "🟢 OK"
            st.caption(f"{s.get('name')} — stock {s.get('stock',0)} / demande {s.get('demand',0)} {status}")
    with col2:
        st.markdown("**📈 Scénario recommandé**")
        st.metric("Revenue-at-Risk", f"{after.get('rar', 0):,.0f} FCFA".replace(",", " "),
                   delta=f"-{sim.get('reduction', 0):,.0f} FCFA")
        st.metric("Santé des stocks", f"{after.get('stock_health', 0)}%", delta=f"+{sim.get('improvement', 0)}%")
        st.metric("Score réputation", f"{after.get('reputation_score', 0)}/5",
                   delta=f"+{after.get('reputation_score', 0) - before.get('reputation_score', 0):.1f}")
        for s in after.get("stores", []):
            st.caption(f"{s.get('name')} — stock {s.get('stock',0)} / demande {s.get('demand',0)} 🟢 OK")

    st.markdown('<div class="section-title">📝 Analyse IA — générée automatiquement</div>', unsafe_allow_html=True)
    result = get_scenario_briefing(before, after, data)
    provider = result.get("provider_used", "fallback")
    meta = PROVIDER_META.get(provider, PROVIDER_META["fallback"])
    content = result.get("content") if result.get("success") else "Analyse indisponible pour le moment."
    st.markdown(f"""
        <div class="briefing-card">
            <div class="briefing-eyebrow">
                <span class="briefing-label">◆ Comparaison avant / après</span>
                <span class="briefing-meta"><span style="color:{meta['color']};">{meta['dot']}</span> {meta['label']}</span>
            </div>
            <div class="briefing-body">{content}</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("↻ Régénérer l'analyse", key="regen_scenario"):
        get_scenario_briefing(before, after, data, force=True)
        st.rerun()

# ============================================================================
# 11. DECISION CHALLENGE — "Challenger la décision"
# ============================================================================
# Corrige la limite identifiée : "l'IA explique, mais ne challenge pas
# encore". Cet onglet consomme POST /challenge et affiche les 4 blocs
# distincts renvoyés par le backend (jamais de fusion en un seul texte).
# ============================================================================

def render_challenge_result(result: Dict[str, Any]):
    """Affiche une réponse de /challenge en 4 blocs visuellement distincts :
    Faits (preuves) / Hypothèses (config) / Interprétation (LLM, bornée) /
    Incertitude (limites, jamais dissimulées)."""
    intent = result.get("intent", "EXPLAIN")
    intent_meta = INTENT_META.get(intent, {"label": intent, "icon": "•"})
    provider = result.get("provider_used", "fallback")
    provider_meta = PROVIDER_META.get(provider, PROVIDER_META["fallback"])
    sim_on = result.get("simulation_declenchee", False)

    sim_badge = (
        f'<span class="challenge-sim-badge {"on" if sim_on else "off"}">'
        f'{"🧮 Simulation exécutée" if sim_on else "Aucune simulation nécessaire"}</span>'
    )

    st.markdown(f"""
        <div class="challenge-card">
            <div class="challenge-eyebrow">
                <span class="challenge-intent-badge">{intent_meta["icon"]} {intent_meta["label"]}</span>
                <span class="briefing-meta">
                    <span style="color:{provider_meta['color']};">{provider_meta['dot']}</span> {provider_meta['label']}
                    {sim_badge}
                </span>
            </div>
    """, unsafe_allow_html=True)

    # --- Faits (preuves calculées — "voici les résultats") ---
    faits = result.get("faits", [])
    if faits:
        st.markdown('<div class="challenge-block-title faits">✓ Faits (calculés par les moteurs)</div>', unsafe_allow_html=True)
        st.markdown(
            '<ul class="challenge-list">' + "".join(f"<li>{f}</li>" for f in faits) + "</ul>",
            unsafe_allow_html=True,
        )

    # --- Interprétation (LLM, bornée aux Faits/Hypothèses) ---
    interpretation = result.get("interpretation", "")
    st.markdown('<div class="challenge-block-title interpretation">◆ Interprétation</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="challenge-interpretation-body">{interpretation}</div>', unsafe_allow_html=True)

    # --- Hypothèses (configuration versionnée) ---
    hypotheses = result.get("hypotheses", [])
    if hypotheses:
        st.markdown('<div class="challenge-block-title hypotheses">⚙ Hypothèses (configuration versionnée)</div>', unsafe_allow_html=True)
        st.markdown(
            '<ul class="challenge-list">' + "".join(f"<li>{h}</li>" for h in hypotheses) + "</ul>",
            unsafe_allow_html=True,
        )

    # --- Incertitude (limites connues, jamais dissimulées) ---
    incertitude = result.get("incertitude", [])
    if incertitude:
        st.markdown('<div class="challenge-block-title incertitude">⚠ Incertitude</div>', unsafe_allow_html=True)
        st.markdown(
            '<ul class="challenge-list">' + "".join(f"<li>{i}</li>" for i in incertitude) + "</ul>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_decision_challenge(data: Dict[str, Any]):
    st.markdown('<div class="section-title">🧪 Challenger la décision</div>', unsafe_allow_html=True)
    st.caption(
        "Mettez la recommandation à l'épreuve. L'IA n'invente jamais un chiffre : toute "
        "nouvelle simulation est déléguée au Simulation Engine (déterministe) avant "
        "d'être interprétée."
    )

    situations = get_situations()
    situation_labels = list(situations.values())
    situation_ids = list(situations.keys())

    col_sit, col_spacer = st.columns([2, 3])
    with col_sit:
        selected_label = st.selectbox("Situation à mettre à l'épreuve", situation_labels, key="challenge_situation")
    selected_situation_id = situation_ids[situation_labels.index(selected_label)]

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    quick_challenges = [
        ("🧪 Contredire", "Pourquoi cette recommandation pourrait-elle être une mauvaise idée ?"),
        ("⚠️ Limites", "Quelles sont les limites de cette recommandation ?"),
        ("🔄 +30 unités", "Que se passe-t-il si j'envoie 30 unités supplémentaires ?"),
        ("🧭 Alternative", "Quelle autre option ai-je si je ne fais rien ?"),
    ]
    cols = st.columns(4)
    triggered = None
    for idx, (label, question) in enumerate(quick_challenges):
        with cols[idx]:
            if st.button(label, key=f"challenge_quick_{idx}", use_container_width=True):
                triggered = question

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([6, 1])
    with col1:
        user_question = st.text_input(
            "Question de challenge",
            placeholder="Ex: Et si la demande réelle était inférieure aux prévisions ?",
            key="challenge_input", label_visibility="collapsed",
        )
    with col2:
        send = st.button("Challenger →", key="challenge_send_btn", use_container_width=True)

    final_question = triggered or (user_question if send and user_question else None)

    if "challenge_history" not in st.session_state:
        st.session_state.challenge_history = []

    if final_question:
        with st.spinner("Reconnaissance de l'intention, simulation si nécessaire, puis interprétation…"):
            result = send_challenge_request(final_question, data, selected_situation_id)
        if result.get("success"):
            st.session_state.challenge_history.insert(0, {"question": final_question, **result})
        else:
            st.error(f"❌ Erreur lors du challenge : {result.get('error', 'inconnue')}")

    if st.session_state.challenge_history:
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        for entry in st.session_state.challenge_history[:5]:
            st.markdown(f"**« {entry['question']} »**")
            render_challenge_result(entry)
    else:
        st.caption("Posez une question ou utilisez un des boutons ci-dessus pour commencer.")

# ============================================================================
# 12. PAGE PRINCIPALE
# ============================================================================

def main():
    inject_css()

    # Chargement automatique des données dès l'ouverture — aucune action requise
    if "context_data" not in st.session_state:
        with st.spinner("Chargement des données…"):
            st.session_state.context_data = get_demo_data() or LOCAL_DEMO_DATA

    render_sidebar()

    st.markdown(f"""
        <div class="cockpit-header">
            <div>
                <p class="cockpit-title">🛰️ Revenue-at-Risk Cockpit</p>
                <p class="cockpit-subtitle">DABA · Smart Distribution · Visibility & Reputation Intelligence</p>
            </div>
            <div class="cockpit-date">{datetime.now().strftime('%d %B %Y — %H:%M')}</div>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard", "💬 Assistant IA", "🔄 Simulation", "🧪 Challenger la décision"
    ])

    data = st.session_state.context_data
    with tab1:
        render_dashboard(data)
    with tab2:
        render_chat_interface()
    with tab3:
        render_simulation(data)
    with tab4:
        render_decision_challenge(data)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption("Revenue-at-Risk Decision Engine · DABA · Mission 2: Branding & Growth")

if __name__ == "__main__":
    main()
