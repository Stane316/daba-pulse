"""AI Explanation Layer — explique les résultats du moteur, sans inventer de chiffres.

Fonctionne en mode fallback déterministe si le LLM est indisponible.

INC-20 — IA challengeable :
- classification d'intention (7 intentions) au lieu de mots-clés bruts ;
- réponse structurée en 4 blocs séparés : Faits / Hypothèses / Interprétation /
  Incertitude, pour distinguer ce qui est CALCULÉ de ce qui est SUPPOSÉ ;
- les champs historiques (situation / facteurs / decision / impact) restent
  peuplés pour la rétro-compatibilité (chemin LLM et consommateurs existants).
"""

from __future__ import annotations

import json
import re
from enum import Enum
from typing import Any

import httpx

from app.core.config import HYPOTHESES, get_settings
from app.engines.data_loader import DataStore
from app.engines.decision_engine import get_decision
from app.engines.risk_engine import build_executive_summary, get_situation
from app.engines.simulator import simulate
from app.models.schemas import AIExplainResponse

# ============================================================================
# 1. Intentions — INC-20
# ============================================================================


class IntentType(str, Enum):
    """Intentions reconnues derrière la question du responsable."""

    EXPLAIN = "EXPLAIN"  # « Pourquoi cette boutique ? »
    CHALLENGE = "CHALLENGE"  # « Et si on n'agit pas ? », « pourquoi pas ? »
    COMPARE = "COMPARE"  # « Et si 20 unités ? », « que se passe-t-il si je réduis ? »
    ALTERNATIVE = "ALTERNATIVE"  # « Y a-t-il une autre option ? »
    JUSTIFY = "JUSTIFY"  # « Pourquoi cette quantité / cette décision ? »
    RESUME = "RESUME"  # « Résume en 3 phrases »
    LIMITS = "LIMITS"  # « Quelle hypothèse est fragile ? », « limites ? »


# Ordre de priorité : le premier match gagne (du plus spécifique au plus général).
_INTENT_RULES: list[tuple[IntentType, tuple[str, ...]]] = [
    (
        IntentType.LIMITS,
        (
            "fragile",
            "hypothèse",
            "hypothese",
            "incertitude",
            "incertain",
            "limite",
            "faille",
            "changerait ta recommandation",
            "changerait votre recommandation",
            "changerait la recommandation",
        ),
    ),
    (
        IntentType.ALTERNATIVE,
        (
            "alternative",
            "autre option",
            "autre action",
            "autre stratégie",
            "autre strategie",
            "plan b",
            "compare cette décision",
        ),
    ),
    (
        IntentType.COMPARE,
        (
            "compar",
            "que se passe-t-il si",
            "que se passerait-il",
            "que se passe t il",
            "rédui",
            "redui",
            "augment",
            "au lieu de",
            "plutôt que",
            "à la place",
            "a la place",
            "versus",
        ),
    ),
    (
        IntentType.CHALLENGE,
        (
            "et si",
            "mauvaise idée",
            "mauvaise idee",
            "risqué",
            "contredi",
            "pourquoi pas",
            "je doute",
            "challeng",
            "met en doute",
        ),
    ),
    (
        IntentType.JUSTIFY,
        (
            "justifi",
            "prouve",
            "preuve",
            "pourquoi cette quantité",
            "pourquoi cette quantite",
            "pourquoi cette décision",
            "pourquoi cette decision",
            "pourquoi proposes",
        ),
    ),
    (
        IntentType.RESUME,
        (
            "résume",
            "resume",
            "synthèse",
            "synthese",
            "3 phrases",
            "pour mon équipe",
            "pour mon equipe",
            "en bref",
        ),
    ),
    (
        IntentType.EXPLAIN,
        (
            "pourquoi",
            "explique",
            "facteur",
            "cause",
            "driver",
            "comment",
            "qu'est-ce",
            "qu'est ce",
            "boutique",
            "signal",
            "quel",
            "quelle",
        ),
    ),
]


def classify_intent(question: str) -> tuple[IntentType, dict[str, Any]]:
    """Classifie l'intention d'une question — déterministe, sans LLM.

    La quantité n'est extraite que pour les intentions de scénario
    (COMPARE / CHALLENGE) : « 3 » dans « Résume en 3 phrases » n'est pas
    une quantité de réallocation. « Et si X unités ? » est promu en COMPARE
    dès qu'une quantité est détectée ; « et si on n'agit pas » reste CHALLENGE.
    """
    q = question.lower().strip()
    intent: IntentType = IntentType.EXPLAIN
    for rule_intent, keywords in _INTENT_RULES:
        if any(k in q for k in keywords):
            intent = rule_intent
            break
    quantite: int | None = None
    if intent in (IntentType.CHALLENGE, IntentType.COMPARE):
        m = re.search(r"\b(\d{1,5})\b", q)
        quantite = int(m.group(1)) if m else None
    if intent is IntentType.CHALLENGE and quantite is not None:
        intent = IntentType.COMPARE
    return intent, {"quantite": quantite}


# ============================================================================
# 2. Contexte calculé par le moteur (source de vérité pour l'explication)
# ============================================================================


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


# ============================================================================
# 3. Helpers calcul (déterministes — l'IA ne calcule JAMAIS à la place du moteur)
# ============================================================================


def _num(v: Any, default: float = 0.0) -> float:
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _labels(sit: dict) -> tuple[str, str]:
    boutique = (sit.get("boutique") or {}).get("nom", "l'entreprise")
    produit = (sit.get("produit") or {}).get("nom", "le produit concerné")
    return boutique, produit


def _quantite_scenario(
    sit: dict,
    dec: dict,
    sim: dict,
    quantite: float,
) -> dict[str, Any] | None:
    """Comparaison chiffrée « Q unités vs recommandation » (déterministe).

    Mêmes formules que le moteur : RaR = max(0, déficit − q) × prix.
    """
    if sit.get("scope") != "distribution":
        return None
    deficit = _num(sit.get("deficit_potentiel"))
    prix = _num(sit.get("prix_unitaire"))
    if deficit <= 0 or prix <= 0:
        return None
    reco = _num(dec.get("quantite") or sim.get("quantite"))
    rar_avant = _num(sim.get("rar_avant") or sit.get("revenue_at_risk"))
    rar_q = max(0.0, deficit - quantite) * prix
    rar_reco = max(0.0, deficit - reco) * prix
    protege_reco = _num(sim.get("protege")) or (rar_avant - rar_reco)
    return {
        "quantite": quantite,
        "deficit": deficit,
        "prix": prix,
        "reco": reco,
        "rar_avant": rar_avant,
        "rar_q": rar_q,
        "protege_q": rar_avant - rar_q,
        "rar_reco": rar_reco,
        "protege_reco": protege_reco,
        "pct_reco": (reco / deficit * 100) if deficit else 0.0,
        "pct_q": (quantite / deficit * 100) if deficit else 0.0,
    }


# ============================================================================
# 3. Blocs Faits / Hypothèses / Interprétation / Incertitude — INC-20
# ============================================================================


def _build_blocks(
    ctx: dict[str, Any],
    scenario: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construit les 4 blocs à partir des SEULS résultats calculés du moteur."""
    sit = ctx.get("situation") or {}
    dec = ctx.get("decision") or {}
    sim = ctx.get("simulation") or {}
    boutique, produit = _labels(sit)
    scope = sit.get("scope", "distribution")

    faits: list[str] = []
    hypotheses: list[str] = []
    interpretation = ""
    incertitude: list[str] = []

    if scope == "reputation":
        faits = [
            f"Réputation DABA sous tension : {sit.get('signal', 'signaux faibles détectés')}.",
            f"Revenue-at-Risk réputation : {sit.get('revenue_at_risk', 0):,.0f} FCFA.",
        ]
        faits += [
            f"Facteur {d.get('libelle')} : {d.get('impact')}" for d in sit.get("drivers", [])
        ][:4]
        faits.append(f"Décision moteur : {dec.get('libelle', 'améliorer visibilité et avis')}.")
        if sim:
            faits.append(
                f"Simulation : RaR {sim.get('rar_avant', 0):,.0f} → {sim.get('rar_apres', 0):,.0f} FCFA "
                f"· revenu potentiellement protégé {sim.get('protege', 0):,.0f} FCFA."
            )
        facteur = _num(sit.get("metriques_extra", {}).get("facteur_risque"))
        hypotheses = [
            (
                f"Facteur de risque cumulé : {facteur:.2f} "
                "(note < 3,5 + engagement < 1 % + absence d'avis + faible visibilité)."
                if facteur
                else "Facteurs de risque cumulés (note, engagement, avis, visibilité)."
            ),
            "Une meilleure réputation stimule la demande (+20 % — hypothèse, non mesurée).",
        ]
        interpretation = (
            f"La réputation est le maillon faible de DABA : les signaux (avis, engagement, visibilité) "
            f"exposent {sit.get('revenue_at_risk', 0):,.0f} FCFA de revenu potentiel. "
            f"L'action « {dec.get('libelle', '…')} » est prioritaire car elle traite les causes "
            f"identifiées par l'audit numérique, avant qu'elles n'érodent la demande."
        )
        incertitude = [
            "L'impact réputation → ventes est estimé par des facteurs cumulés : l'effet réel peut être plus lent.",
            "Les gains ne sont garantis que si la demande suit (+20 % est une hypothèse, pas une mesure).",
        ]
    else:
        deficit = _num(sit.get("deficit_potentiel"))
        prix = _num(sit.get("prix_unitaire"))
        stock = _num(sit.get("stock_disponible"))
        demande = _num(sit.get("demande_attendue"))
        faits = [
            f"Chez {boutique}, « {produit} » : stock {stock:,.0f} u · demande attendue "
            f"({sit.get('horizon_jours', 7)} j) {demande:,.0f} u · déficit {deficit:,.0f} u.",
            f"Revenue-at-Risk : {sit.get('revenue_at_risk', 0):,.0f} FCFA = {deficit:,.0f} u × {prix:,.0f} FCFA.",
            f"Sévérité : {sit.get('severite', 'n/a')} · confiance moteur : {sit.get('confiance', 0):.0%}.",
        ]
        faits += [
            f"Facteur {d.get('libelle')} : {d.get('impact')}" for d in sit.get("drivers", [])
        ]
        src = (dec.get("boutique_source") or {}).get("nom")
        faits.append(
            f"Décision moteur : {dec.get('libelle', 'réallouer du stock')} "
            f"({_num(dec.get('quantite')):,.0f} u" + (f" depuis {src}" if src else "") + ")."
        )
        if sim:
            faits.append(
                f"Simulation : RaR {sim.get('rar_avant', 0):,.0f} → {sim.get('rar_apres', 0):,.0f} FCFA "
                f"· revenu potentiellement protégé {sim.get('protege', 0):,.0f} FCFA."
            )
        if scenario:
            faits.append(
                f"Scénario {scenario['quantite']:,.0f} u : déficit "
                f"{max(0.0, deficit - scenario['quantite']):,.0f} u · RaR {scenario['rar_q']:,.0f} FCFA "
                f"· protégé {scenario['protege_q']:,.0f} FCFA (recommandation {scenario['reco']:,.0f} u : "
                f"{scenario['protege_reco']:,.0f} FCFA)."
            )
        hypotheses = [
            f"{h.get('libelle')} : {h.get('valeur')}"
            for h in sit.get("hypotheses", [])
            if h.get("libelle")
        ]
        hypotheses += [
            f"Demande = moyenne des ventes 7 j × tendance (horizon {sit.get('horizon_jours', 7)} j) "
            f"— méthode versionnée {HYPOTHESES.get('version', '?')}.",
            f"Prix unitaire constant à {prix:,.0f} FCFA pendant l'horizon.",
            "Réapprovisionnement hors horizon simulé (le délai n'est pas absorbé par l'action).",
        ]
        rar_avant = _num(sim.get("rar_avant"))
        protege = _num(sim.get("protege"))
        pct_protege = (protege / rar_avant * 100) if rar_avant else 0.0
        interpretation = (
            f"Le déficit de {deficit:,.0f} u signifie que {boutique} ne peut pas couvrir la demande attendue "
            f"de « {produit} » sur {sit.get('horizon_jours', 7)} j. "
            f"L'action recommandée protège {protege:,.0f} FCFA, soit {pct_protege:.0f} % du RaR de la situation — "
            f"c'est la raison pour laquelle elle est prioritaire."
        )
        if scenario and scenario["protege_q"] < scenario["protege_reco"]:
            interpretation += (
                f" En challengant avec {scenario['quantite']:,.0f} u, le moteur protège "
                f"{scenario['protege_q']:,.0f} FCFA, soit {scenario['protege_reco'] - scenario['protege_q']:,.0f} FCFA "
                f"de moins que la recommandation ({scenario['reco']:,.0f} u) : la recommandation maximise "
                f"le revenu protégé."
            )
        rar_sit = _num(sit.get("revenue_at_risk"))
        incertitude = [
            f"La demande est estimée, non mesurée : ±20 % ferait passer le RaR de {rar_sit:,.0f} à environ "
            f"{max(0.0, deficit * 0.8) * prix:,.0f}–{deficit * 1.2 * prix:,.0f} FCFA.",
            f"Niveau de confiance : {sit.get('niveau_confiance', 'moyen')} ({sit.get('confiance', 0):.0%}).",
            "Le délai de réapprovisionnement réel peut décaler l'effet de l'action dans le temps.",
            "Données synthétiques : estimations illustratives, pas une prédiction certaine.",
        ]

    return {
        "faits": faits,
        "hypotheses": hypotheses,
        "interpretation": interpretation
        or f"Décision moteur : {dec.get('libelle', 'n/a')} — voir l'impact simulé.",
        "incertitude": incertitude or ["Aucune incertitude spécifique détectée — confiance élevée."],
    }


# ============================================================================
# 4. Réponses par intention (fallback déterministe)
# ============================================================================


def _answer_limits(sit: dict, sim: dict) -> str:
    hypo = sit.get("hypotheses") or []
    drivers = sit.get("drivers") or []
    fragile_h = next(
        (h for h in hypo if "demande" in h.get("libelle", "").lower()),
        hypo[0] if hypo else None,
    )
    fragile_d = min(drivers, key=lambda d: d.get("poids", 1)) if drivers else None
    deficit = _num(sit.get("deficit_potentiel"))
    prix = _num(sit.get("prix_unitaire"))
    rar = _num(sit.get("revenue_at_risk"))
    parts = [
        f"L'hypothèse la plus fragile est : "
        f"{fragile_h.get('libelle') + ' — ' + str(fragile_h.get('valeur')) if fragile_h else 'méthode demande (moyenne 7 j × tendance)'}.",
        f"Confiance globale : {sit.get('confiance', 0):.0%} ({sit.get('niveau_confiance', 'moyen')}).",
    ]
    if fragile_d:
        parts.append(
            f"Facteur le plus sensible : {fragile_d.get('libelle')} "
            f"({int(_num(fragile_d.get('poids')) * 100)} %)."
        )
    if prix and deficit:
        parts.append(
            f"Si la demande était sur-estimée de 20 %, le RaR passerait de {rar:,.0f} à "
            f"{max(0.0, deficit * 0.8) * prix:,.0f} FCFA ; sous-estimée de 20 %, jusqu'à "
            f"{deficit * 1.2 * prix:,.0f} FCFA."
        )
    return " ".join(parts)


def _answer_alternative(ctx: dict) -> str:
    alt = ctx.get("alternative") or {}
    if alt:
        return (
            f"Alternative moteur : {alt.get('libelle', 'n/a')}. "
            f"Quantité : {_num(alt.get('quantite')):,.0f} u. Revenu potentiellement protégé : "
            f"{_num(alt.get('revenu_potentiellement_protege')):,.0f} FCFA — approche progressive qui "
            f"réduit le risque tout en limitant le mouvement de stock."
        )
    return "Aucune alternative quantitative n'est associée à cette situation."


def _answer_compare(
    q: str,
    sit: dict,
    dec: dict,
    sim: dict,
    ctx: dict,
    params: dict,
) -> str:
    quantite = params.get("quantite")
    scenario = _quantite_scenario(sit, dec, sim, float(quantite)) if quantite else None
    if scenario:
        return (
            f"Avec {scenario['quantite']:,.0f} u : déficit {scenario['deficit']:,.0f} → "
            f"{max(0.0, scenario['deficit'] - scenario['quantite']):,.0f} u, "
            f"RaR {scenario['rar_q']:,.0f} FCFA (protégé {scenario['protege_q']:,.0f}). "
            f"Recommandation {scenario['reco']:,.0f} u : RaR {scenario['rar_reco']:,.0f} FCFA "
            f"(protégé {scenario['protege_reco']:,.0f}). "
            f"Écart : {scenario['protege_reco'] - scenario['protege_q']:,.0f} FCFA de plus protégés "
            f"avec {scenario['reco']:,.0f} u. Raison : {scenario['reco']:,.0f} u couvre "
            f"{scenario['pct_reco']:.0f} % du déficit vs {scenario['pct_q']:.0f} % pour "
            f"{scenario['quantite']:,.0f} u."
        )
    # Pas de quantité : comparer avec l'alternative progressive du moteur (70 %).
    alt = ctx.get("alternative") or {}
    if alt:
        reco = _num(dec.get("quantite") or sim.get("quantite"))
        protege = _num(sim.get("protege"))
        alt_q = _num(alt.get("quantite"))
        alt_p = _num(alt.get("revenu_potentiellement_protege"))
        return (
            f"Comparaison moteur : recommandation {reco:,.0f} u protège {protege:,.0f} FCFA ; "
            f"approche progressive {alt_q:,.0f} u (70 %) protège {alt_p:,.0f} FCFA. "
            f"Écart : {protege - alt_p:,.0f} FCFA — la quantité complète maximise le revenu protégé, "
            f"mais l'alternative limite le mouvement de stock."
        )
    return _answer_explain(q, sit, dec, sim, ctx)


def _answer_challenge(
    q: str,
    sit: dict,
    dec: dict,
    sim: dict,
) -> str:
    # Et si on n'agit pas / aucune action → le RaR reste exposé.
    if any(
        w in q
        for w in [
            "rien",
            "n'agit",
            "n-agit",
            "n agit",
            "pas d'action",
            "aucune action",
            "0 unité",
            "0 unites",
            "ne rien faire",
        ]
    ):
        rar_avant = _num(sim.get("rar_avant") or sit.get("revenue_at_risk"))
        return (
            f"Si aucune action : le déficit de {_num(sit.get('deficit_potentiel')):,.0f} unités persiste, "
            f"le Revenue-at-Risk reste à {rar_avant:,.0f} FCFA. Aucun revenu n'est protégé. "
            f"L'action recommandée ({_num(dec.get('quantite')):,.0f} u) ramènerait le RaR à "
            f"{_num(sim.get('rar_apres')):,.0f} FCFA (protégé {_num(sim.get('protege')):,.0f} FCFA)."
        )
    # Challenge générique : tester la robustesse de la recommandation.
    deficit = _num(sit.get("deficit_potentiel"))
    prix = _num(sit.get("prix_unitaire"))
    demande = _num(sit.get("demande_attendue"))
    reco = _num(dec.get("quantite") or sim.get("quantite"))
    lo = max(0.0, deficit * 0.8) * prix
    hi = deficit * 1.2 * prix
    return (
        f"Pour challenger la recommandation ({reco:,.0f} u) : elle repose sur la demande estimée de "
        f"{demande:,.0f} u (moyenne 7 j × tendance). Si la demande réelle est inférieure, une partie "
        f"du transfert créerait du surstock ; si elle est supérieure, le déficit resterait partiellement "
        f"couvert. L'incertitude chiffre cette fourchette : ±20 % fait varier le RaR entre {lo:,.0f} "
        f"et {hi:,.0f} FCFA."
    )


def _answer_justify(sit: dict, dec: dict, sim: dict) -> str:
    deficit = _num(sit.get("deficit_potentiel"))
    reco = _num(dec.get("quantite") or sim.get("quantite"))
    protege = _num(sim.get("protege"))
    pct = (reco / deficit * 100) if deficit else 0.0
    parts = [
        f"La quantité recommandée est de {reco:,.0f} unités : elle couvre {pct:.0f} % du déficit de "
        f"{deficit:,.0f} u (demande {_num(sit.get('demande_attendue')):,.0f} − stock "
        f"{_num(sit.get('stock_disponible')):,.0f}).",
        f"Elle protège {protege:,.0f} FCFA de revenu (RaR {_num(sim.get('rar_avant')):,.0f} → "
        f"{_num(sim.get('rar_apres')):,.0f} FCFA).",
    ]
    raisons = dec.get("raisons") or []
    if raisons:
        parts.append("Justification moteur : " + " ; ".join(raisons[:3]) + ".")
    src = (dec.get("boutique_source") or {}).get("nom")
    if src:
        parts.append(f"Le stock provient de {src}, qui dispose d'un surplus mobilisable.")
    return " ".join(parts)


def _answer_resume(sit: dict, dec: dict, sim: dict) -> str:
    boutique, produit = _labels(sit)
    libelle = str(dec.get("libelle", "réallouer du stock"))
    return (
        f"1. {boutique} risque de manquer « {produit} » : déficit de "
        f"{_num(sit.get('deficit_potentiel')):,.0f} u sur {sit.get('horizon_jours', 7)} j, soit "
        f"{sit.get('revenue_at_risk', 0):,.0f} FCFA exposés. "
        f"2. La décision recommandée est : « {libelle} », qui protège "
        f"{_num(sim.get('protege')):,.0f} FCFA. "
        f"3. L'incertitude principale est la demande estimée (±20 %)."
    )


def _answer_explain(q: str, sit: dict, dec: dict, sim: dict, ctx: dict) -> str:
    boutique, produit = _labels(sit)

    if any(w in q for w in ["boutique", "point de vente", "pourquoi lui", "pourquoi elle"]):
        return (
            f"{boutique} est prioritaire car elle cumule le déficit le plus élevé "
            f"({sit.get('deficit_potentiel', '?')} unités) et un Revenue-at-Risk de "
            f"{sit.get('revenue_at_risk', 0):,.0f} FCFA sur « {produit} ». "
            f"Signal : {sit.get('signal', 'n/a')}. "
            f"Niveau de confiance : {sit.get('confiance', 0):.0%}."
        )

    if any(w in q for w in ["quantit", "combien", "unités", "unite", "envoi"]):
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

    # Défaut structuré.
    return (
        f"**Situation** — {sit.get('signal', 'n/a')} chez {boutique} / {produit}. "
        f"RaR {sit.get('revenue_at_risk', 0):,.0f} FCFA.\n\n"
        f"**Décision** — {dec.get('libelle', 'n/a')}\n\n"
        f"**Impact** — RaR {sim.get('rar_avant', 0):,.0f} → {sim.get('rar_apres', 0):,.0f} FCFA "
        f"(protégé : {sim.get('protege', 0):,.0f} FCFA)."
    )


# ============================================================================
# 5. Fallback déterministe (aucun LLM requis)
# ============================================================================


def _fallback_explanation(
    ctx: dict[str, Any],
    question: str | None = None,
) -> AIExplainResponse:
    sit = ctx.get("situation") or {}
    dec = ctx.get("decision") or {}
    sim = ctx.get("simulation") or {}

    intent = IntentType.EXPLAIN
    params: dict[str, Any] = {}
    scenario: dict[str, Any] | None = None
    if question:
        intent, params = classify_intent(question)
        if params.get("quantite"):
            scenario = _quantite_scenario(sit, dec, sim, float(params["quantite"]))

    blocks = _build_blocks(ctx, scenario)
    faits = blocks["faits"]
    interpretation = blocks["interpretation"]

    if question:
        reponse = _answer_question(question, sit, dec, sim, ctx, intent, params)
    else:
        reponse = (
            "**Situation**\n" + (faits[0] if faits else "Situation à risque détectée.")
            + "\n\n**Décision**\n" + str(dec.get("libelle", "Appliquer l'action recommandée"))
            + "\n\n**Impact**\n" + interpretation
            + "\n\n_Données synthétiques — estimation, non une prédiction certaine._"
        )

    sources = [
        "Risk Engine (calcul déterministe)",
        "Decision Engine (règles explicables)",
        "What-if Simulator",
        "Dataset synthétique local",
    ]

    return AIExplainResponse(
        situation=faits[0] if faits else "",
        facteurs=faits,
        decision=str(dec.get("libelle", "Voir l'impact simulé")),
        impact=interpretation,
        reponse=reponse,
        sources=sources,
        fallback=True,
        model=None,
        faits=faits,
        hypotheses=blocks["hypotheses"],
        interpretation=interpretation,
        incertitude=blocks["incertitude"],
        intention=intent.value,
    )


def _answer_question(
    q: str,
    sit: dict,
    dec: dict,
    sim: dict,
    ctx: dict,
    intent: IntentType,
    params: dict[str, Any],
) -> str:
    """Dispatch par intention (INC-20) — le moteur reste la seule source de chiffres."""
    if intent is IntentType.LIMITS:
        return _answer_limits(sit, sim)
    if intent is IntentType.ALTERNATIVE:
        return _answer_alternative(ctx)
    if intent is IntentType.COMPARE:
        return _answer_compare(q, sit, dec, sim, ctx, params)
    if intent is IntentType.CHALLENGE:
        return _answer_challenge(q, sit, dec, sim)
    if intent is IntentType.JUSTIFY:
        return _answer_justify(sit, dec, sim)
    if intent is IntentType.RESUME:
        return _answer_resume(sit, dec, sim)
    return _answer_explain(q, sit, dec, sim, ctx)


# ============================================================================
# 6. Orchestration + chemin LLM optionnel
# ============================================================================


async def explain(
    store: DataStore,
    situation_id: str | None = None,
    question: str | None = None,
    mode: str = "resume",
) -> AIExplainResponse:
    ctx = _build_context(store, situation_id)
    settings = get_settings()

    # Toujours capable de répondre sans LLM.
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
        "Tu réponds en français, de façon claire et professionnelle, structurée en 4 sections exactement : "
        "FAITS (liste à puces des chiffres calculés), HYPOTHÈSES (liste à puces des suppositions), "
        "INTERPRÉTATION (ce que cela signifie pour la décision), "
        "INCERTITUDE (liste à puces de ce qui pourrait changer la recommandation). "
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
                    "Produis une explication structurée en 4 sections (FAITS / HYPOTHÈSES / "
                    "INTERPRÉTATION / INCERTITUDE).\n\n"
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

    # 4 blocs demandés au LLM (INC-20).
    faits_raw = _extract_section(text, "FAITS") or ""
    hypotheses_raw = _extract_section(text, "HYPOTHÈSES") or _extract_section(text, "HYPOTHESES") or ""
    interpretation = _extract_section(text, "INTERPRÉTATION") or _extract_section(text, "INTERPRETATION") or ""
    incertitude_raw = _extract_section(text, "INCERTITUDE") or ""

    faits = [
        re.sub(r"^[\-•*\d.)\s]+", "", ln).strip()
        for ln in faits_raw.splitlines()
        if ln.strip()
    ] or fallback_facteurs(ctx)
    hypotheses = [
        re.sub(r"^[\-•*\d.)\s]+", "", ln).strip()
        for ln in hypotheses_raw.splitlines()
        if ln.strip()
    ] or fallback_hypotheses(ctx)
    incertitude = [
        re.sub(r"^[\-•*\d.)\s]+", "", ln).strip()
        for ln in incertitude_raw.splitlines()
        if ln.strip()
    ] or fallback_incertitude(ctx)

    # Champs historiques (rétro-compat).
    situation = faits[0] if faits else _extract_section(text, "SITUATION") or text[:280]
    decision = _extract_section(text, "DÉCISION") or _extract_section(text, "DECISION") or ""
    impact = interpretation or _extract_section(text, "IMPACT") or ""

    return AIExplainResponse(
        situation=situation.strip(),
        facteurs=faits,
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
        faits=faits,
        hypotheses=hypotheses,
        interpretation=interpretation.strip() or fallback_interpretation(ctx),
        incertitude=incertitude,
        intention=None,
    )


def fallback_facteurs(ctx: dict) -> list[str]:
    sit = ctx.get("situation") or {}
    return [
        f"{d.get('libelle')}: {d.get('impact')}" for d in sit.get("drivers", [])
    ] or ["Déficit demande/stock"]


def fallback_hypotheses(ctx: dict) -> list[str]:
    sit = ctx.get("situation") or {}
    hypotheses = [
        f"{h.get('libelle')} : {h.get('valeur')}"
        for h in sit.get("hypotheses", [])
        if h.get("libelle")
    ]
    if hypotheses:
        return hypotheses
    return [
        f"Demande = moyenne 7 j × tendance (horizon {sit.get('horizon_jours', 7)} j)",
        "Prix unitaire constant sur l'horizon",
    ]


def fallback_incertitude(ctx: dict) -> list[str]:
    sit = ctx.get("situation") or {}
    deficit = _num(sit.get("deficit_potentiel"))
    prix = _num(sit.get("prix_unitaire"))
    lines = ["La demande est estimée (moyenne 7 j × tendance) : ±20 % change le RaR."]
    if deficit and prix:
        lines.append(
            f"Fourchette ±20 % : {max(0.0, deficit * 0.8) * prix:,.0f}–{deficit * 1.2 * prix:,.0f} FCFA."
        )
    lines.append("Données synthétiques : estimations illustratives, pas une prédiction certaine.")
    return lines


def fallback_interpretation(ctx: dict) -> str:
    sit = ctx.get("situation") or {}
    dec = ctx.get("decision") or {}
    sim = ctx.get("simulation") or {}
    libelle = str(dec.get("libelle") or "appliquer l'action recommandée")
    return (
        f"La situation « {sit.get('signal', 'risque détecté')} » est traitée par la décision "
        f"« {libelle} », qui fait passer le RaR de "
        f"{sim.get('rar_avant', 0):,.0f} à {sim.get('rar_apres', 0):,.0f} FCFA "
        f"(revenu potentiellement protégé : {sim.get('protege', 0):,.0f} FCFA)."
    )


def _extract_section(text: str, title: str) -> str | None:
    pattern = (
        rf"(?:^|\n)\s*[*#]*\s*{title}\s*[*#:]*\s*\n(.*?)"
        r"(?=\n\s*[*#]*\s*(?:FAITS|HYPOTH[ÈE]SES|INTERPR[ÉE]TATION|INCERTITUDE|"
        r"SITUATION|FACTEURS|D[ÉE]CISION|IMPACT)\b|$)"
    )
    m = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else None
