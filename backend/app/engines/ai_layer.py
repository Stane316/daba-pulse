"""AI Explanation Layer — explique les résultats du moteur, sans inventer de chiffres.

Fonctionne en mode fallback déterministe si le LLM est indisponible.
"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import get_settings
from app.engines.data_loader import DataStore
from app.engines.decision_engine import get_decision
from app.engines.risk_engine import build_executive_summary, get_situation
from app.engines.simulator import simulate
from app.models.schemas import AIExplainResponse


def _build_context(store: DataStore, situation_id: str | None) -> dict[str, Any]:
    summary = build_executive_summary(store)
    ctx: dict[str, Any] = {
        "rar_total": summary.revenue_at_risk_total,
        "rar_distribution": summary.revenue_at_risk_distribution,
        "rar_reputation": summary.revenue_at_risk_reputation,
        "nb_critiques": summary.nb_situations_critiques,
        "disclaimer": summary.disclaimer,
        "donnees_synthetiques": True,
    }

    sid = situation_id
    if not sid and summary.situations:
        sid = summary.situations[0].id

    if sid:
        sit = get_situation(store, sid)
        dec = get_decision(store, sid)
        sim = simulate(store, sid)
        if sit:
            ctx["situation"] = sit.model_dump()
        if dec:
            ctx["decision"] = dec.model_dump(exclude={"alternative"})
            if dec.alternative:
                ctx["alternative"] = {
                    "libelle": dec.alternative.libelle,
                    "quantite": dec.alternative.quantite,
                    "revenu_potentiellement_protege": dec.alternative.revenu_potentiellement_protege,
                }
        if sim:
            ctx["simulation"] = {
                "rar_avant": sim.revenue_at_risk_avant,
                "rar_apres": sim.revenue_at_risk_apres,
                "protege": sim.revenu_potentiellement_protege,
                "quantite": sim.quantite_simulee,
                "metriques": [m.model_dump() for m in sim.metriques],
            }
    return ctx


def _fallback_explanation(
    ctx: dict[str, Any],
    question: str | None = None,
) -> AIExplainResponse:
    sit = ctx.get("situation") or {}
    dec = ctx.get("decision") or {}
    sim = ctx.get("simulation") or {}

    boutique = (sit.get("boutique") or {}).get("nom", "l'entreprise")
    produit = (sit.get("produit") or {}).get("nom", "le produit concerné")
    scope = sit.get("scope", "distribution")

    if scope == "reputation":
        situation_txt = (
            f"La réputation globale de DABA est sous tension : {sit.get('signal', '')}. "
            f"Revenue-at-Risk réputation estimé à "
            f"{sit.get('revenue_at_risk', 0):,.0f} FCFA."
        )
        facteurs = [
            f"{d.get('libelle')}: {d.get('impact')}"
            for d in sit.get("drivers", [])
        ] or ["Indicateurs de visibilité sous les seuils critiques"]
        decision_txt = dec.get("libelle", "Améliorer la visibilité et les avis")
        impact_txt = (
            f"En appliquant cette action, le RaR réputation passerait de "
            f"{sim.get('rar_avant', 0):,.0f} à {sim.get('rar_apres', 0):,.0f} FCFA "
            f"(~{sim.get('protege', 0):,.0f} FCFA potentiellement protégés). "
            "Une meilleure réputation peut aussi stimuler la demande (+20 % hypothèse)."
        )
    else:
        situation_txt = (
            f"Chez {boutique}, le produit « {produit} » présente un risque : "
            f"{sit.get('signal', 'désalignement demande/stock')}. "
            f"Stock disponible : {sit.get('stock_disponible', '?')} · "
            f"Demande attendue ({sit.get('horizon_jours', 7)} j) : "
            f"{sit.get('demande_attendue', '?')} · "
            f"Déficit : {sit.get('deficit_potentiel', '?')} · "
            f"Revenue-at-Risk : {sit.get('revenue_at_risk', 0):,.0f} FCFA."
        )
        facteurs = [
            f"{d.get('libelle')}: {d.get('impact')}"
            for d in sit.get("drivers", [])
        ] or [
            f"Déficit de {sit.get('deficit_potentiel', 0)} unités",
            f"Prix unitaire {sit.get('prix_unitaire', 0):,.0f} FCFA",
        ]
        decision_txt = dec.get("libelle", "Réallouer du stock")
        if dec.get("raisons"):
            decision_txt += " — " + "; ".join(dec["raisons"][:2])
        impact_txt = (
            f"Si l'on applique {dec.get('quantite', sim.get('quantite', '?'))} unités : "
            f"RaR de {sim.get('rar_avant', 0):,.0f} → {sim.get('rar_apres', 0):,.0f} FCFA. "
            f"Revenu potentiellement protégé : {sim.get('protege', 0):,.0f} FCFA. "
            f"Confiance : {sit.get('niveau_confiance', 'moyen')} "
            f"({sit.get('confiance', 0):.0%})."
        )

    reponse = (
        f"**Situation**\n{situation_txt}\n\n"
        f"**Facteurs**\n"
        + "\n".join(f"• {f}" for f in facteurs)
        + f"\n\n**Décision**\n{decision_txt}\n\n"
        f"**Impact**\n{impact_txt}\n\n"
        f"_Données synthétiques — estimation, non une prédiction certaine._"
    )

    # Q&A simple par mots-clés
    if question:
        q = question.lower()
        reponse = _answer_question(q, sit, dec, sim, ctx)

    sources = [
        "Risk Engine (calcul déterministe)",
        "Decision Engine (règles explicables)",
        "What-if Simulator",
        "Dataset synthétique local",
    ]

    return AIExplainResponse(
        situation=situation_txt,
        facteurs=facteurs,
        decision=decision_txt,
        impact=impact_txt,
        reponse=reponse,
        sources=sources,
        fallback=True,
        model=None,
    )


def _answer_question(
    q: str,
    sit: dict,
    dec: dict,
    sim: dict,
    ctx: dict,
) -> str:
    boutique = (sit.get("boutique") or {}).get("nom", "cette boutique")
    produit = (sit.get("produit") or {}).get("nom", "ce produit")

    if any(w in q for w in ["boutique", "pourquoi cette boutique", "point de vente"]):
        return (
            f"{boutique} est prioritaire car elle cumule le déficit le plus élevé "
            f"({sit.get('deficit_potentiel', '?')} unités) et un Revenue-at-Risk de "
            f"{sit.get('revenue_at_risk', 0):,.0f} FCFA sur "
            f"« {produit} ». "
            f"Signal : {sit.get('signal', 'n/a')}. "
            f"Niveau de confiance : {sit.get('confiance', 0):.0%}."
        )

    if any(w in q for w in ["quantit", "combien", "unités", "unite"]):
        return (
            f"La quantité recommandée est de {dec.get('quantite', sim.get('quantite', '?'))} unités. "
            f"Elle vise à couvrir le déficit de {sit.get('deficit_potentiel', '?')} unités "
            f"(demande {sit.get('demande_attendue', '?')} − stock {sit.get('stock_disponible', '?')}). "
            f"Source potentielle : "
            f"{(dec.get('boutique_source') or {}).get('nom', 'entrepôt / production')}."
        )

    if any(w in q for w in ["facteur", "pourquoi ce risque", "cause", "driver"]):
        drivers = sit.get("drivers") or []
        lines = [f"• {d.get('libelle')}: {d.get('impact')}" for d in drivers]
        return (
            "Les facteurs quantitatifs du risque sont :\n"
            + ("\n".join(lines) if lines else "• Déficit demande/stock")
            + f"\n\nRaR = {sit.get('deficit_potentiel', '?')} × "
            f"{sit.get('prix_unitaire', '?')} = {sit.get('revenue_at_risk', 0):,.0f} FCFA."
        )

    if any(w in q for w in ["si je", "que se passe", "simule", "impact", "après"]):
        return (
            f"Simulation : RaR passe de {sim.get('rar_avant', 0):,.0f} FCFA à "
            f"{sim.get('rar_apres', 0):,.0f} FCFA. "
            f"Revenu potentiellement protégé : {sim.get('protege', 0):,.0f} FCFA. "
            f"Quantité simulée : {sim.get('quantite', 'n/a')}."
        )

    if any(w in q for w in ["protégé", "protege", "économ", "gagne", "sauve"]):
        return (
            f"Le revenu potentiellement protégé est estimé à "
            f"{sim.get('protege', dec.get('revenu_potentiellement_protege', 0)):,.0f} FCFA. "
            "Ce n'est pas un gain garanti : c'est le RaR évité si la demande se matérialise "
            "et que l'action est exécutée à temps."
        )

    if any(w in q for w in ["total", "global", "ensemble", "entreprise"]):
        return (
            f"Revenue-at-Risk total : {ctx.get('rar_total', 0):,.0f} FCFA "
            f"(distribution {ctx.get('rar_distribution', 0):,.0f} + "
            f"réputation {ctx.get('rar_reputation', 0):,.0f}). "
            f"{ctx.get('nb_critiques', 0)} situation(s) critique(s)."
        )

    if any(w in q for w in ["alternative", "autre action", "autre option"]):
        alt = ctx.get("alternative") or {}
        if alt:
            return (
                f"Alternative : {alt.get('libelle', 'n/a')}. "
                f"Quantité : {alt.get('quantite', 'n/a')}. "
                f"Revenu protégé estimé : "
                f"{alt.get('revenu_potentiellement_protege', 0):,.0f} FCFA."
            )
        return "Aucune alternative quantitative n'est associée à cette situation."

    # défaut structuré
    return (
        f"**Situation** — {sit.get('signal', 'n/a')} chez {boutique} / {produit}. "
        f"RaR {sit.get('revenue_at_risk', 0):,.0f} FCFA.\n\n"
        f"**Décision** — {dec.get('libelle', 'n/a')}\n\n"
        f"**Impact** — RaR {sim.get('rar_avant', 0):,.0f} → {sim.get('rar_apres', 0):,.0f} FCFA "
        f"(protégé : {sim.get('protege', 0):,.0f} FCFA)."
    )


async def explain(
    store: DataStore,
    situation_id: str | None = None,
    question: str | None = None,
    mode: str = "resume",
) -> AIExplainResponse:
    ctx = _build_context(store, situation_id)
    settings = get_settings()

    # Toujours capable de répondre sans LLM
    fallback = _fallback_explanation(ctx, question if mode == "qa" else None)

    if not settings.ai_enabled or not settings.openai_api_key:
        return fallback

    try:
        llm = await _call_llm(settings, ctx, question, mode)
        if llm:
            return llm
    except Exception:
        pass

    return fallback


async def _call_llm(
    settings,
    ctx: dict[str, Any],
    question: str | None,
    mode: str,
) -> AIExplainResponse | None:
    """Appel LLM optionnel — strictement borné au contexte fourni."""

    system = (
        "Tu es l'assistant décisionnel de DabaPulse pour DABA SAS (aviculture). "
        "Tu expliques UNIQUEMENT les résultats fournis dans le contexte JSON. "
        "Tu ne inventes JAMAIS de chiffres absents du contexte. "
        "Tu réponds en français, de façon claire et professionnelle, "
        "structurée en SITUATION → FACTEURS → DÉCISION → IMPACT. "
        "Tu rappelles que les données sont synthétiques et les chiffres des estimations. "
        "Si on te demande un chiffre absent, dis-le explicitement."
    )

    user_payload = {
        "mode": mode,
        "question": question,
        "contexte": ctx,
    }

    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    "Voici le contexte calculé par le moteur (JSON). "
                    "Produis une explication structurée.\n\n"
                    + json.dumps(user_payload, ensure_ascii=False, default=str)[:12000]
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 900,
    }

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(
            f"{settings.openai_base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        r.raise_for_status()
        data = r.json()

    text = data["choices"][0]["message"]["content"]

    # Extraire sections si possible
    situation = _extract_section(text, "SITUATION") or text[:280]
    facteurs_raw = _extract_section(text, "FACTEURS") or ""
    facteurs = [
        re.sub(r"^[\-•*\d.)\s]+", "", ln).strip()
        for ln in facteurs_raw.splitlines()
        if ln.strip()
    ] or fallback_facteurs(ctx)
    decision = _extract_section(text, "DÉCISION") or _extract_section(text, "DECISION") or ""
    impact = _extract_section(text, "IMPACT") or ""

    return AIExplainResponse(
        situation=situation.strip(),
        facteurs=facteurs[:8],
        decision=decision.strip() or (ctx.get("decision") or {}).get("libelle", ""),
        impact=impact.strip(),
        reponse=text,
        sources=[
            "Risk Engine",
            "Decision Engine",
            "What-if Simulator",
            f"LLM:{settings.openai_model}",
        ],
        fallback=False,
        model=settings.openai_model,
    )


def fallback_facteurs(ctx: dict) -> list[str]:
    sit = ctx.get("situation") or {}
    return [
        f"{d.get('libelle')}: {d.get('impact')}" for d in sit.get("drivers", [])
    ]


def _extract_section(text: str, title: str) -> str | None:
    pattern = rf"(?:^|\n)\s*[*#]*\s*{title}\s*[*#:]*\s*\n(.*?)(?=\n\s*[*#]*\s*(?:SITUATION|FACTEURS|D[ÉE]CISION|IMPACT)\b|$)"
    m = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else None
