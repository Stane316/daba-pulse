# ============================================================================
# REVENUE-AT-RISK DECISION ENGINE — BACKEND
# ============================================================================
# API FastAPI pour l'IA Engine avec bascule automatique Gemini -> Groq ->
# Fallback analytique, ENRICHIE de la boucle de "Decision Challenge" :
#
#     Décision -> Question -> Nouvelle hypothèse -> Nouveau calcul
#     -> Comparaison -> Contre-argument -> Décision réévaluée
#
# Corrections intégrées dans cette version (cf. revue d'architecture) :
#   1. Reconnaissance d'intention (IntentClassifier) au lieu d'un
#      prompt_type fixe choisi côté frontend.
#   2. L'IA ne simule JAMAIS elle-même : tout nouveau chiffre provient
#      du SimulationEngine, déterministe, testable indépendamment du LLM.
#   3. La réponse du endpoint /challenge affiche les PREUVES (Faits)
#      séparément de l'interprétation : "voici les résultats calculés,
#      voici pourquoi j'en déduis cela" plutôt que "croyez-moi".
#   4. Séparation stricte Faits / Hypothèses / Interprétation / Incertitude,
#      pour éviter l'effet "IA = oracle" et la fausse précision.
#
# Version: 2.0 — Decision Challenge Edition
# Date: 18 août 2026
# ============================================================================

import os
import json
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()

# ============================================================================
# 1. MODÈLES PYDANTIC
# ============================================================================

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    role: MessageRole
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    context_data: Optional[Dict[str, Any]] = None
    prompt_type: str = "general_assistant"
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 1000

class RiskData(BaseModel):
    distribution_risk: Dict[str, Any]
    reputation_risk: Dict[str, Any]
    total_rar: float

class RecommendationRequest(BaseModel):
    recommendation: Dict[str, Any]
    context_data: Dict[str, Any]

class ScenarioRequest(BaseModel):
    before: Dict[str, Any]
    after: Dict[str, Any]
    context_data: Optional[Dict[str, Any]] = None

class AIResponse(BaseModel):
    success: bool
    content: str
    provider_used: str
    model: str
    usage: Optional[Dict[str, int]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class HealthResponse(BaseModel):
    status: str
    providers: Dict[str, bool]
    version: str
    timestamp: str

class StatsResponse(BaseModel):
    total_requests: int
    gemini_used: int
    groq_used: int
    fallback_used: int
    errors: int
    success_rate: float
    gemini_share: float
    groq_share: float
    fallback_share: float


# ----------------------------------------------------------------------
# NOUVEAU — modèles liés au Simulation Engine (déterministe)
# ----------------------------------------------------------------------
class SimulationRequest(BaseModel):
    """
    Contrat attendu par le Simulation Engine.
    situation_id : identifie l'entité à recalculer (cf. registre SITUATIONS)
    quantite     : quantité additionnelle envisagée (scénario distribution)
    action_id    : action envisagée (scénario réputation : "collecte_avis", ...)
    params       : extension libre pour de futurs paramètres de simulation
    """
    situation_id: str
    quantite: Optional[int] = None
    action_id: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)

class SimulationResponse(BaseModel):
    situation_id: str
    type: str  # "distribution" ou "reputation"
    avant: Dict[str, Any]
    apres: Dict[str, Any]


# ----------------------------------------------------------------------
# NOUVEAU — modèles liés à la boucle de Decision Challenge
# ----------------------------------------------------------------------
class IntentType(str, Enum):
    """Intentions reconnues derrière la question du dirigeant."""
    EXPLAIN = "EXPLAIN"          # "Pourquoi cette décision ?"
    CHALLENGE = "CHALLENGE"      # "Pourquoi cette recommandation pourrait être mauvaise ?"
    COMPARE = "COMPARE"          # "Que se passe-t-il si je réduis la quantité ?"
    ALTERNATIVE = "ALTERNATIVE"  # "Quelle autre option ai-je ?"
    JUSTIFY = "JUSTIFY"          # "Justifie ce choix."
    RESUME = "RESUME"            # "Résume-moi ça pour mon équipe."
    LIMITS = "LIMITS"            # "Quelles sont les limites de cette recommandation ?"

class DecisionChallengeRequest(BaseModel):
    question: str
    context_data: Dict[str, Any] = Field(default_factory=dict)
    # Requis uniquement si la question implique un nouveau calcul
    # (CHALLENGE / COMPARE / ALTERNATIVE). Cf. registre SITUATIONS.
    situation_id: Optional[str] = None

class DecisionChallengeResponse(BaseModel):
    """
    Réponse structurée en 4 blocs distincts — jamais fusionnés — afin que
    le dirigeant voie explicitement "voici les faits, voici pourquoi j'en
    déduis cela" plutôt qu'un texte qui mélange calcul et opinion.
    """
    intent: str
    faits: List[str]
    hypotheses: List[str]
    interpretation: str
    incertitude: List[str]
    simulation_declenchee: bool
    provider_used: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# 2. PROVIDERS LLM
# ============================================================================

class BaseLLMProvider:
    """Classe de base pour les fournisseurs LLM"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        raise NotImplementedError

    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError

    def is_available(self) -> bool:
        return self.config.get("enabled", False) and bool(self.config.get("api_key"))

class GeminiProvider(BaseLLMProvider):
    """Provider Google Gemini via API OpenAI-compatible"""

    def _initialize_client(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.config["api_key"],
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            logger.info(f"✅ Gemini client initialisé avec le modèle {self.config['model']}")
        except Exception as e:
            logger.error(f"❌ Erreur d'initialisation Gemini: {e}")
            self.client = None

    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> Dict[str, Any]:
        if not self.is_available() or not self.client:
            return {"success": False, "error": "Gemini non disponible"}

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=messages,
                max_tokens=kwargs.get("max_tokens", self.config.get("max_tokens", 2048)),
                reasoning_effort=kwargs.get("reasoning_effort", self.config.get("reasoning_effort", "low")),
            )

            choice = response.choices[0]
            content = choice.message.content
            finish_reason = getattr(choice, "finish_reason", None)

            if not content or not content.strip():
                logger.warning(
                    f"⚠️ Gemini a renvoyé un contenu vide (finish_reason={finish_reason}). "
                    "Le budget de réflexion (thinking) a probablement consommé tout le max_tokens. "
                    "Augmentez max_tokens ou passez reasoning_effort='low'/'minimal'."
                )
                return {
                    "success": False,
                    "error": f"Réponse vide de Gemini (finish_reason={finish_reason})"
                }

            if finish_reason == "length":
                logger.warning(
                    "⚠️ Réponse Gemini tronquée (finish_reason=length). "
                    "Augmentez max_tokens pour éviter la coupure."
                )

            return {
                "success": True,
                "content": content,
                "provider": "gemini",
                "model": self.config["model"],
                "finish_reason": finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            }
        except Exception as e:
            logger.error(f"❌ Erreur Gemini: {e}")
            return {"success": False, "error": str(e)}

class GroqProvider(BaseLLMProvider):
    """Provider Groq avec Llama"""

    def _initialize_client(self):
        try:
            from groq import Groq
            self.client = Groq(api_key=self.config["api_key"])
            logger.info(f"✅ Groq client initialisé avec le modèle {self.config['model']}")
        except Exception as e:
            logger.error(f"❌ Erreur d'initialisation Groq: {e}")
            self.client = None

    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> Dict[str, Any]:
        if not self.is_available() or not self.client:
            return {"success": False, "error": "Groq non disponible"}

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=messages,
                temperature=kwargs.get("temperature", self.config.get("temperature", 0.2)),
                max_tokens=kwargs.get("max_tokens", self.config.get("max_tokens", 1000)),
            )

            return {
                "success": True,
                "content": response.choices[0].message.content,
                "provider": "groq",
                "model": self.config["model"],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            }
        except Exception as e:
            logger.error(f"❌ Erreur Groq: {e}")
            return {"success": False, "error": str(e)}

# ============================================================================
# 3. FALLBACK ANALYTIQUE
# ============================================================================

class AnalyticalFallback:
    """Moteur de réponse analytique sans LLM"""

    @staticmethod
    def generate_response(data: Dict[str, Any], question: str = None) -> Dict[str, Any]:
        try:
            response_parts = []

            # 1. Revenue-at-Risk
            rar_data = data.get("revenue_at_risk", {})
            if rar_data:
                total_rar = rar_data.get("total", 0)
                distribution_rar = rar_data.get("distribution", 0)
                reputation_rar = rar_data.get("reputation", 0)

                response_parts.append(f"📊 REVENUE-AT-RISK TOTAL: {total_rar:,.0f} FCFA")
                response_parts.append(f"   └── Distribution: {distribution_rar:,.0f} FCFA")
                response_parts.append(f"   └── Réputation: {reputation_rar:,.0f} FCFA")

            # 2. Risques détectés
            risks = data.get("risks", [])
            if risks:
                response_parts.append("\n⚠️ RISQUES DÉTECTÉS:")
                for risk in risks[:5]:
                    response_parts.append(f"   • {risk}")

            # 3. Recommandations
            recommendations = data.get("recommendations", [])
            if recommendations:
                response_parts.append("\n💡 RECOMMANDATIONS:")
                for rec in recommendations[:3]:
                    response_parts.append(f"   • {rec}")

            # 4. Simulation
            simulation = data.get("simulation", {})
            if simulation:
                before = simulation.get("before", {})
                after = simulation.get("after", {})
                if before and after:
                    response_parts.append("\n🔄 SIMULATION:")
                    rar_before = before.get("rar", 0)
                    rar_after = after.get("rar", 0)
                    response_parts.append(f"   • Avant: {rar_before:,.0f} FCFA")
                    response_parts.append(f"   • Après: {rar_after:,.0f} FCFA")
                    reduction = rar_before - rar_after
                    response_parts.append(f"   • Réduction: {reduction:,.0f} FCFA")
                    if reduction > 0:
                        response_parts.append(f"   • Taux de réduction: {(reduction/rar_before*100):.1f}%")

            return {
                "success": True,
                "content": "\n".join(response_parts) if response_parts else "Données disponibles. Consultez le dashboard.",
                "provider": "fallback_analytical",
                "model": "analytical_engine",
                "usage": None
            }

        except Exception as e:
            logger.error(f"❌ Erreur fallback: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "Erreur lors de la génération de la réponse analytique."
            }

# ============================================================================
# 4. MOTEUR IA PRINCIPAL
# ============================================================================

class AIEngine:
    """Moteur IA principal avec bascule automatique"""

    SYSTEM_PROMPTS = {
        "explain_risk": """
        Tu es un assistant décisionnel pour DABA, une entreprise agroalimentaire.
        Tu expliques les risques de perte de revenu identifiés par le moteur analytique.
        Utilise UNIQUEMENT les données fournies. Ne fais AUCUNE supposition.
        Sois clair, concis et orienté action.
        """,

        "recommend_action": """
        Tu es un conseiller stratégique pour DABA.
        Tu recommandes des actions basées sur les risques identifiés et les données disponibles.
        Structure ta réponse en: 1) Problème, 2) Action recommandée, 3) Impact attendu.
        """,

        "compare_scenarios": """
        Tu compares les scénarios avant/après pour DABA.
        Mets en évidence les différences et l'impact économique.
        Utilise les chiffres calculés par le moteur.
        """,

        "general_assistant": """
        Tu es l'assistant IA de DABA pour le pilotage décisionnel.
        Tu réponds aux questions du dirigeant sur les données de l'entreprise.
        Base-toi EXCLUSIVEMENT sur les données fournies.
        Si les données ne contiennent pas l'information, dis-le clairement.
        """,

        "executive_briefing": """
        Tu es l'analyste IA de DABA (Revenue-at-Risk Decision Engine).
        Tu rédiges un briefing exécutif automatique, déclenché sans qu'on te le demande,
        pour un dirigeant pressé qui vient d'ouvrir son tableau de bord.
        Réponds en Markdown, structuré EXACTEMENT ainsi, sans aucun texte avant ou après :

        **Situation** : une phrase factuelle sur l'état global.
        **Risques clés** : 2 à 3 puces courtes, chiffrées si les données le permettent.
        **Action prioritaire** : une recommandation unique, concrète et actionnable.
        **Impact attendu** : un chiffre ou pourcentage si disponible dans les données.

        Base-toi UNIQUEMENT sur les données fournies. Ne fais AUCUNE supposition.
        Pas de préambule ("Voici le briefing..."), pas de conclusion générique. Va droit au but.
        """,

        "challenge_decision": """
        Tu es la couche d'interprétation du moteur décisionnel DABA.

        RÈGLES STRICTES :
        1. Le prompt utilisateur contient trois blocs : FAITS (calculés par le
           Risk Engine / Decision Engine / Simulation Engine), HYPOTHÈSES
           (configuration versionnée), INCERTITUDE (limites connues). Tu ne
           dois RIEN ajouter en dehors de ces trois blocs : aucun chiffre,
           aucune probabilité, aucune donnée inventée.
        2. Tu n'effectues aucun calcul ni simulation toi-même. Si une
           simulation serait nécessaire pour répondre précisément et
           qu'elle n'apparaît pas dans les FAITS, dis-le clairement au lieu
           de l'estimer ou de l'improviser.
        3. Ne dis jamais "croyez-moi" ni une formulation d'autorité : appuie
           chaque phrase sur un FAIT ou une HYPOTHÈSE cité explicitement.
        4. Adapte ton ton à l'intention détectée (comprendre, comparer,
           contredire, justifier, résumer, ou lister les limites) sans
           jamais sortir des données fournies.
        5. Réponds en français, en moins de 150 mots.
        """,
    }

    def __init__(self):
        self.providers = {}
        self._initialize_providers()
        self.fallback = AnalyticalFallback()
        self.stats = {
            "total_requests": 0,
            "gemini_used": 0,
            "groq_used": 0,
            "fallback_used": 0,
            "errors": 0
        }
        logger.info("🚀 AI Engine initialisé avec bascule automatique")

    def _initialize_providers(self):
        """Initialise tous les providers LLM"""
        # Google Gemini
        gemini_config = {
            "name": "gemini",
            "enabled": True,
            "api_key": os.getenv("GEMINI_API_KEY", ""),
            "model": os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            "max_tokens": 2048,
            "reasoning_effort": "low",
        }
        self.providers["gemini"] = GeminiProvider(gemini_config)

        # Groq avec Llama
        groq_config = {
            "name": "groq",
            "enabled": True,
            "api_key": os.getenv("GROQ_API_KEY", ""),
            # NOTE : "llama-3.3-70b-versatile" a été déprécié par Groq le
            # 17 juin 2026. Migration recommandée par Groq elle-même vers
            # "openai/gpt-oss-120b" (meilleures performances, inférence plus
            # rapide). Cf. https://console.groq.com/docs/deprecations
            "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            "max_tokens": 1000,
            "temperature": 0.2
        }
        self.providers["groq"] = GroqProvider(groq_config)

        logger.info(f"✅ Providers configurés: {list(self.providers.keys())}")

    def generate(
        self,
        prompt: str,
        context_data: Dict[str, Any] = None,
        prompt_type: str = "general_assistant",
        history: List["Message"] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Génère une réponse IA avec bascule automatique, en enrichissant
        le prompt avec le contexte et l'historique (utilisé par /chat et
        les endpoints /explain-risk, /recommend, /compare-scenarios)."""
        full_prompt = self._build_prompt(prompt, context_data, history=history)
        system_prompt = self.SYSTEM_PROMPTS.get(
            prompt_type,
            self.SYSTEM_PROMPTS["general_assistant"]
        )
        return self.generate_raw(full_prompt, system_prompt, **kwargs)

    def generate_raw(self, prompt: str, system_prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Cascade Gemini -> Groq -> Fallback SANS reconstruction de prompt.

        Introduit pour la boucle de Decision Challenge : le prompt y est
        déjà entièrement assemblé (blocs Faits/Hypothèses/Incertitude) par
        `build_challenge_prompt()`, donc _build_prompt() ne doit pas
        l'envelopper une seconde fois. `generate()` reste la méthode à
        utiliser pour les endpoints existants (/chat, /explain-risk, ...).
        """
        self.stats["total_requests"] += 1

        # Tentative 1: Google Gemini
        try:
            if self.providers["gemini"].is_available():
                logger.info("📤 Tentative avec Gemini...")
                response = self.providers["gemini"].generate(prompt, system_prompt, **kwargs)
                if response.get("success"):
                    self.stats["gemini_used"] += 1
                    response["provider_used"] = "gemini"
                    logger.info("✅ Réponse générée avec Gemini")
                    return response
        except Exception as e:
            logger.warning(f"⚠️ Gemini échoué: {e}")

        # Tentative 2: Groq
        try:
            if self.providers["groq"].is_available():
                logger.info("📤 Tentative avec Groq...")
                response = self.providers["groq"].generate(prompt, system_prompt, **kwargs)
                if response.get("success"):
                    self.stats["groq_used"] += 1
                    response["provider_used"] = "groq"
                    logger.info("✅ Réponse générée avec Groq")
                    return response
        except Exception as e:
            logger.warning(f"⚠️ Groq échoué: {e}")

        # Fallback: réponse analytique générique
        logger.info("📤 Fallback analytique...")
        self.stats["fallback_used"] += 1
        return {
            "success": True,
            "content": (
                "Interprétation indisponible en mode analytique : reportez-vous "
                "directement aux données déjà calculées par le moteur analytique."
            ),
            "provider": "fallback_analytical",
            "model": "analytical_engine",
            "provider_used": "fallback",
            "usage": None,
        }

    def _build_prompt(
        self,
        user_prompt: str,
        context_data: Dict[str, Any] = None,
        history: List["Message"] = None,
    ) -> str:
        """Construit le prompt complet avec les données contextuelles et l'historique"""
        history_str = ""
        if history:
            turns = []
            for m in history[:-1]:
                role_label = "Dirigeant" if m.role == MessageRole.USER else "Assistant"
                turns.append(f"{role_label}: {m.content}")
            if turns:
                history_str = "\nHISTORIQUE DE LA CONVERSATION:\n" + "\n".join(turns) + "\n"

        if not context_data:
            return f"{history_str}\nQUESTION DU DIRIGEANT:\n{user_prompt}" if history_str else user_prompt

        context_str = json.dumps(context_data, indent=2, default=str, ensure_ascii=False)

        return f"""
        CONTEXTE DE L'ENTREPRISE DABA:
        {context_str}
        {history_str}
        QUESTION DU DIRIGEANT:
        {user_prompt}

        INSTRUCTIONS:
        - Base-toi UNIQUEMENT sur les données ci-dessus
        - Ne fais AUCUNE supposition
        - Cite des chiffres précis quand c'est possible
        - Si une information n'est pas disponible, dis-le clairement
        """

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'utilisation"""
        total = self.stats["total_requests"]
        errors = self.stats["errors"]
        return {
            **self.stats,
            "success_rate": (total - errors) / max(1, total),
            "gemini_share": self.stats["gemini_used"] / max(1, total),
            "groq_share": self.stats["groq_used"] / max(1, total),
            "fallback_share": self.stats["fallback_used"] / max(1, total),
        }


# ============================================================================
# 4bis. SIMULATION ENGINE — moteur de calcul déterministe
# ============================================================================
# Correction prioritaire n°2 : "Ne jamais laisser l'IA simuler elle-même."
#
#     AI -> Simulation Engine -> résultat déterministe -> AI -> explication
#
# Ce moteur applique STRICTEMENT les formules du cadrage (§7.1 et §7.2) :
#     RaR_distribution = déficit * prix_unitaire
#     RaR_réputation   = visiteurs * taux_conversion * prix_moyen * facteur_risque
#
# Aucun LLM n'intervient dans ce module. Il est appelable et testable
# indépendamment de toute clé API.
# ============================================================================

# Registre des situations simulables (en mémoire pour la démo — remplaçable
# par une vraie base de données sans changer l'interface de SimulationEngine).
SITUATIONS: Dict[str, Dict[str, Any]] = {
    "cotonou_distribution": {
        "type": "distribution",
        "boutique_id": "Cotonou",
        "produit_id": "P012",
        "stock_actuel": 8,
        "ventes_prevues": 35,
        "prix_unitaire": 18000,
    },
    "reputation_globale": {
        "type": "reputation",
        "visiteurs_jour": 1200,
        "taux_conversion": 0.015,
        "prix_moyen": 18000,
        "note_google": 2.5,
        "nb_avis": 3,
        "engagement_reseaux": 0.008,
    },
}

# Règles de facteur de risque réputation — reprises telles quelles du
# cadrage (§7.2). Configuration versionnée : c'est ici, et nulle part
# ailleurs (surtout pas dans un prompt), que ces seuils sont définis.
FACTEUR_RISQUE_RULES: List[Tuple[str, callable, float]] = [
    ("note_google_critique (< 3.5)", lambda s: s.get("note_google", 5) < 3.5, 0.20),
    ("engagement_reseaux_faible (< 1%)", lambda s: s.get("engagement_reseaux", 1) < 0.01, 0.10),
    ("absence_avis (<= 5 avis)", lambda s: s.get("nb_avis", 999) <= 5, 0.15),
]

# Catalogue des actions de réputation simulables et de leur effet sur les
# indicateurs D'ENTRÉE (jamais sur le résultat directement) — cf. cadrage
# Table 4 "Types de recommandations".
REPUTATION_ACTIONS: Dict[str, Dict[str, Any]] = {
    "collecte_avis": {"nb_avis": 15, "note_google": 4.2},
    "refonte_contenu": {"engagement_reseaux": 0.035},
    "optimisation_gmb": {"note_google": 3.8},
}


class SimulationEngine:
    """
    Moteur de calcul déterministe. L'IA ne l'appelle jamais "à sa place" :
    elle lui délègue TOUJOURS le calcul, puis se contente d'interpréter
    le résultat qu'il retourne.
    """

    @staticmethod
    def _facteur_risque(situation: Dict[str, Any]) -> Tuple[float, str]:
        total = 0.0
        raisons: List[str] = []
        for nom, condition, valeur in FACTEUR_RISQUE_RULES:
            if condition(situation):
                total += valeur
                raisons.append(nom)
        raison = ", ".join(raisons) if raisons else "aucun facteur de risque actif"
        return round(total, 2), raison

    @classmethod
    def _compute_distribution(cls, situation: Dict[str, Any], quantite: Optional[int]) -> Dict[str, Any]:
        stock = situation["stock_actuel"] + (quantite or 0)
        demande = situation["ventes_prevues"]
        deficit = max(0, demande - stock)
        rar = deficit * situation["prix_unitaire"]
        return {
            "boutique_id": situation["boutique_id"],
            "produit_id": situation["produit_id"],
            "stock": stock,
            "demande": demande,
            "deficit": deficit,
            "prix_unitaire": situation["prix_unitaire"],
            "rar_distribution": rar,
        }

    @classmethod
    def _compute_reputation(cls, situation: Dict[str, Any], action_id: Optional[str]) -> Dict[str, Any]:
        s = dict(situation)
        if action_id and action_id in REPUTATION_ACTIONS:
            for champ, valeur in REPUTATION_ACTIONS[action_id].items():
                s[champ] = valeur
        facteur, raison = cls._facteur_risque(s)
        rar = s["visiteurs_jour"] * s["taux_conversion"] * s["prix_moyen"] * facteur
        return {
            "visiteurs_jour": s["visiteurs_jour"],
            "taux_conversion": s["taux_conversion"],
            "prix_moyen": s["prix_moyen"],
            "note_google": s["note_google"],
            "nb_avis": s["nb_avis"],
            "engagement_reseaux": s["engagement_reseaux"],
            "facteur_risque": facteur,
            "facteur_risque_raison": raison,
            "rar_reputation": round(rar, 0),
        }

    @classmethod
    def run(
        cls,
        situation_id: str,
        quantite: Optional[int] = None,
        action_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calcule l'état "avant" (situation actuelle inchangée) et l'état
        "après" (avec le paramètre proposé appliqué), tous deux de façon
        purement déterministe.
        """
        if situation_id not in SITUATIONS:
            raise ValueError(f"Situation inconnue : {situation_id}")

        situation = SITUATIONS[situation_id]

        if situation["type"] == "distribution":
            avant = cls._compute_distribution(situation, quantite=None)
            apres = cls._compute_distribution(situation, quantite=quantite)
        else:
            avant = cls._compute_reputation(situation, action_id=None)
            apres = cls._compute_reputation(situation, action_id=action_id)

        return {
            "situation_id": situation_id,
            "type": situation["type"],
            "avant": avant,
            "apres": apres,
        }


# ============================================================================
# 4ter. INTENT CLASSIFIER — reconnaissance d'intention
# ============================================================================
# Correction prioritaire n°1 : "Le moteur IA ne devrait pas simplement
# faire du keyword matching."
#
# Stratégie : classification par LLM (JSON strict) en priorité ; repli sur
# une heuristique de mots-clés UNIQUEMENT si aucun LLM n'est disponible
# (mode explicitement dégradé et journalisé comme tel).
# ============================================================================

INTENT_SYSTEM_PROMPT = """Tu es un classifieur d'intention pour un moteur décisionnel d'entreprise.

Étant donné la question d'un dirigeant, identifie UNE intention parmi :
- EXPLAIN : il veut comprendre une décision ou un risque déjà calculé
- CHALLENGE : il veut tester ou contredire la recommandation ("pourquoi ce serait une mauvaise idée", "et si...")
- COMPARE : il veut comparer un scénario alternatif (quantité différente, action différente)
- ALTERNATIVE : il demande une autre option / un plan B
- JUSTIFY : il veut une justification formelle de la décision
- RESUME : il veut un résumé synthétique pour son équipe
- LIMITS : il demande les limites, incertitudes ou hypothèses fragiles de la recommandation

Réponds STRICTEMENT en JSON, sans aucun texte autour, au format exact :
{"intent": "<UNE_DES_VALEURS_CI-DESSUS>", "params": {"quantite": <entier ou null>, "action_id": <chaine ou null>}}

Valeurs possibles pour "action_id" (uniquement si mentionné explicitement) :
"collecte_avis", "refonte_contenu", "optimisation_gmb".

Extrait "quantite" UNIQUEMENT si un nombre précis est mentionné en vue d'une simulation
(ex: "si j'envoie 30 unités" -> quantite: 30). N'invente jamais une valeur absente : mets null.
"""

_KEYWORD_FALLBACK_RULES: List[Tuple[IntentType, List[str]]] = [
    (IntentType.CHALLENGE, ["mauvaise idée", "risqué", "contredi", "et si", "pourquoi pas"]),
    (IntentType.COMPARE, ["compar", "réduire", "augmenter", "que se passe-t-il si"]),
    (IntentType.ALTERNATIVE, ["autre option", "alternative", "plan b"]),
    (IntentType.JUSTIFY, ["justifi", "prouve", "preuve"]),
    (IntentType.RESUME, ["résume", "résumé", "pour mon équipe", "synthèse"]),
    (IntentType.LIMITS, ["limite", "hypothèse", "incertitude", "fragile", "faille"]),
]


class IntentClassifier:
    """Classifie l'intention d'une question en s'appuyant sur les mêmes
    providers LLM que l'AIEngine principal (réutilisation, pas de
    duplication de la logique de cascade)."""

    def __init__(self, engine: AIEngine):
        self.engine = engine

    def classify(self, question: str) -> Tuple[IntentType, Dict[str, Any]]:
        for provider_name in ("gemini", "groq"):
            provider = self.engine.providers.get(provider_name)
            if not provider or not provider.is_available():
                continue
            try:
                # max_tokens porté à 900 (au lieu de 150) : sur un modèle
                # "thinking" comme Gemini, une partie du budget part dans la
                # réflexion interne (invisible) avant même la sortie JSON.
                #
                # réflexion -> réponse tronquée -> JSON invalide -> échec
                # de classification alors même que Gemini avait répondu.
                result = provider.generate(
                    question, INTENT_SYSTEM_PROMPT,
                    max_tokens=900, temperature=0.0, reasoning_effort="low",
                )
                if result.get("success"):
                    intent, params = self._parse(result["content"])
                    logger.info(f"🎯 Intention classifiée par {provider_name}: {intent} | params={params}")
                    return intent, params
            except Exception as e:
                logger.warning(f"⚠️ Échec classification via {provider_name}: {e}")

        return self._keyword_fallback(question)

    @staticmethod
    def _parse(raw: str) -> Tuple[IntentType, Dict[str, Any]]:
        raw = raw.strip()
        raw = re.sub(r"^```json|```$", "", raw, flags=re.MULTILINE).strip()

        # Robustesse supplémentaire : un modèle "thinking" ajoute parfois un
        # commentaire avant/après le JSON malgré la consigne stricte. On
        # extrait le premier bloc {...} plutôt que d'exiger que la réponse
        # soit un JSON pur, pour éviter des échecs de classification évitables.
        if not raw.startswith("{"):
            match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if match:
                raw = match.group(0)

        data = json.loads(raw)
        intent = IntentType(data["intent"])
        params = data.get("params") or {}
        return intent, params

    @staticmethod
    def _keyword_fallback(question: str) -> Tuple[IntentType, Dict[str, Any]]:
        logger.warning(
            "AUCUN LLM disponible pour la classification d'intention -> "
            "repli sur heuristique de mots-clés (mode dégradé)."
        )
        q = question.lower()
        for intent, keywords in _KEYWORD_FALLBACK_RULES:
            if any(k in q for k in keywords):
                match = re.search(r"\b(\d{1,5})\b", q)
                quantite = int(match.group(1)) if match else None
                return intent, {"quantite": quantite, "action_id": None}
        return IntentType.EXPLAIN, {"quantite": None, "action_id": None}


# ============================================================================
# 4quater. DECISION CHALLENGE ORCHESTRATOR
# ============================================================================
# Implémente la boucle complète :
#     Décision -> Question -> Simulation -> Comparaison -> Contre-argument
#
# Correction prioritaire n°3 : afficher les preuves ("voici les résultats
# calculés, voici pourquoi j'en déduis cela").
# Correction prioritaire n°4 : séparer Faits / Hypothèses / Interprétation
# / Incertitude, pour éviter l'effet "IA = oracle".
# ============================================================================

INTENTS_REQUIRING_SIMULATION = {IntentType.CHALLENGE, IntentType.COMPARE, IntentType.ALTERNATIVE}

INTENT_INSTRUCTIONS: Dict[IntentType, str] = {
    IntentType.EXPLAIN: "Explique la décision en t'appuyant sur les FAITS et les HYPOTHÈSES.",
    IntentType.CHALLENGE: (
        "Le dirigeant veut tester la recommandation. Présente d'abord les FAITS qui la "
        "soutiennent, PUIS les HYPOTHÈSES et INCERTITUDES qui pourraient la fragiliser."
    ),
    IntentType.COMPARE: (
        "Compare explicitement l'état 'avant' et l'état 'après simulation' présents dans "
        "les FAITS. Si aucune nouvelle simulation n'apparaît, indique-le clairement."
    ),
    IntentType.ALTERNATIVE: (
        "Indique si une alternative figure dans les FAITS (résultat d'une nouvelle "
        "simulation). Sinon, invite explicitement à préciser un scénario à simuler."
    ),
    IntentType.JUSTIFY: "Construis une justification structurée, uniquement à partir des FAITS et HYPOTHÈSES.",
    IntentType.RESUME: "Résume la situation en 3 phrases maximum, pour une équipe non technique.",
    IntentType.LIMITS: (
        "Liste les limites de la recommandation en t'appuyant exclusivement sur les blocs "
        "HYPOTHÈSES et INCERTITUDE. Ne présente jamais la recommandation comme certaine."
    ),
}


def _extract_faits(context_data: Dict[str, Any], simulation_result: Optional[Dict[str, Any]]) -> List[str]:
    """FAITS = valeurs strictement calculées par les moteurs, jamais par le LLM."""
    faits: List[str] = []
    rar = context_data.get("revenue_at_risk", {})
    if rar:
        faits.append(f"Revenue-at-Risk total actuel : {rar.get('total', 0):,.0f} FCFA")
        faits.append(f"Dont distribution : {rar.get('distribution', 0):,.0f} FCFA, réputation : {rar.get('reputation', 0):,.0f} FCFA")

    for risque in context_data.get("risks", [])[:5]:
        faits.append(f"Risque détecté : {risque}")

    for reco in context_data.get("recommendations", [])[:3]:
        faits.append(f"Recommandation existante : {reco}")

    if simulation_result:
        avant, apres = simulation_result["avant"], simulation_result["apres"]
        if simulation_result["type"] == "distribution":
            faits.append(
                f"[Nouvelle simulation — {simulation_result['situation_id']}] "
                f"stock {avant['stock']} -> {apres['stock']}, "
                f"déficit {avant['deficit']} -> {apres['deficit']} unités, "
                f"RaR distribution {avant['rar_distribution']:,.0f} -> {apres['rar_distribution']:,.0f} FCFA"
            )
        else:
            faits.append(
                f"[Nouvelle simulation — {simulation_result['situation_id']}] "
                f"note Google {avant['note_google']} -> {apres['note_google']}, "
                f"nb avis {avant['nb_avis']} -> {apres['nb_avis']}, "
                f"engagement {avant['engagement_reseaux']:.1%} -> {apres['engagement_reseaux']:.1%}, "
                f"RaR réputation {avant['rar_reputation']:,.0f} -> {apres['rar_reputation']:,.0f} FCFA"
            )

    return faits or ["Aucune donnée calculée disponible pour cette situation."]


def _extract_hypotheses(context_data: Dict[str, Any]) -> List[str]:
    """HYPOTHÈSES = configuration versionnée, jamais du texte libre du LLM."""
    hyp = [f"{nom} -> facteur de risque {valeur}" for nom, _, valeur in FACTEUR_RISQUE_RULES]
    hyp.append("Le Revenue-at-Risk est une estimation, pas une prédiction financière certaine (cadrage §7).")
    return hyp


def _extract_incertitude(intent: IntentType, simulation_declenchee: bool) -> List[str]:
    """INCERTITUDE = limites connues, jamais dissimulées (cadrage : 'afficher les
    hypothèses et éviter la fausse précision')."""
    incertitudes = [
        "Les chiffres reposent sur des hypothèses de demande et de comportement client "
        "qui peuvent diverger de la réalité observée sur le terrain."
    ]
    if intent in INTENTS_REQUIRING_SIMULATION and not simulation_declenchee:
        incertitudes.append(
            "Aucune nouvelle simulation n'a pu être exécutée pour cette question "
            "(situation non identifiée) : la réponse se limite aux données déjà connues."
        )
    if intent == IntentType.CHALLENGE:
        incertitudes.append(
            "Si la demande réelle diverge de la demande prévue, le déficit — et donc "
            "le Revenue-at-Risk — varierait proportionnellement."
        )
    return incertitudes


def build_challenge_prompt(question: str, intent: IntentType, faits: List[str],
                            hypotheses: List[str], incertitude: List[str]) -> str:
    faits_txt = "\n".join(f"- {f}" for f in faits)
    hyp_txt = "\n".join(f"- {h}" for h in hypotheses)
    inc_txt = "\n".join(f"- {i}" for i in incertitude)

    return f"""INTENTION DÉTECTÉE : {intent.value}
CONSIGNE : {INTENT_INSTRUCTIONS[intent]}

### FAITS (calculés par le moteur analytique / Simulation Engine)
{faits_txt}

### HYPOTHÈSES (configuration versionnée)
{hyp_txt}

### INCERTITUDE (limites connues du système)
{inc_txt}

QUESTION DU DIRIGEANT :
{question}
"""


def handle_decision_challenge(
    engine: AIEngine,
    classifier: IntentClassifier,
    question: str,
    context_data: Dict[str, Any],
    situation_id: Optional[str],
) -> Dict[str, Any]:
    """
    Point d'entrée de la boucle complète :
        Décision -> Question -> Simulation -> Comparaison -> Contre-argument
    """
    # --- Étape 1 : reconnaissance d'intention ---
    intent, params = classifier.classify(question)

    # --- Étape 2 : nouveau calcul déterministe si nécessaire ---
    simulation_result = None
    simulation_declenchee = False
    if intent in INTENTS_REQUIRING_SIMULATION and situation_id:
        try:
            simulation_result = SimulationEngine.run(
                situation_id,
                quantite=params.get("quantite"),
                action_id=params.get("action_id"),
            )
            simulation_declenchee = True
            logger.info(f"🧮 Simulation exécutée par le Simulation Engine pour '{situation_id}'")
        except ValueError as e:
            logger.warning(f"⚠️ Simulation impossible ({e}) -> poursuite sans nouveau calcul.")

    # --- Étape 3 : assemblage des blocs Faits / Hypothèses / Incertitude ---
    faits = _extract_faits(context_data, simulation_result)
    hypotheses = _extract_hypotheses(context_data)
    incertitude = _extract_incertitude(intent, simulation_declenchee)

    # --- Étape 4 : interprétation par le LLM, strictement bornée aux faits ---
    prompt = build_challenge_prompt(question, intent, faits, hypotheses, incertitude)
    system_prompt = AIEngine.SYSTEM_PROMPTS["challenge_decision"]
    result = engine.generate_raw(prompt, system_prompt, max_tokens=1000, temperature=0.1)

    interpretation = result.get("content") if result.get("success") else (
        "Interprétation indisponible : reportez-vous à la section « Faits » ci-dessus."
    )

    return {
        "intent": intent.value,
        "faits": faits,
        "hypotheses": hypotheses,
        "interpretation": interpretation,
        "incertitude": incertitude,
        "simulation_declenchee": simulation_declenchee,
        "provider_used": result.get("provider_used", "fallback"),
    }


# ============================================================================
# 5. DONNÉES DE DÉMONSTRATION
# ============================================================================

DEMO_DATA = {
    "revenue_at_risk": {
        "total": 550800,
        "distribution": 486000,
        "reputation": 64800,
    },
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
            "rar": 550800,
            "stock_health": 45,
            "reputation_score": 2.5,
            "stores": [
                {"name": "Cotonou", "stock": 8, "demand": 35, "deficit": 27},
                {"name": "Parakou", "stock": 15, "demand": 20, "deficit": 5},
                {"name": "Lomé", "stock": 25, "demand": 15, "surplus": 10},
            ]
        },
        "after": {
            "rar": 0,
            "stock_health": 95,
            "reputation_score": 4.5,
            "stores": [
                {"name": "Cotonou", "stock": 38, "demand": 35, "status": "OK"},
                {"name": "Parakou", "stock": 20, "demand": 20, "status": "OK"},
                {"name": "Lomé", "stock": 15, "demand": 15, "status": "OK"},
            ]
        },
        "reduction": 550800,
        "improvement": 50,
        "additional_demand": 20
    }
}


# ============================================================================
# 6. APPLICATION FASTAPI
# ============================================================================
#
# NOTE IMPORTANTE — erreur "Router.__init__() got an unexpected keyword
# argument 'on_startup'" :
#     Cette erreur ne vient PAS d'un usage de on_startup dans ce fichier
#     (aucune occurrence ici). Elle vient d'un CONFLIT DE VERSIONS entre
#     fastapi et starlette installées dans l'environnement (Starlette 1.0,
#     sorti en mars 2026, a supprimé on_startup/on_shutdown de
#     Router.__init__ ; une version de fastapi trop ancienne pour cette
#     Starlette continue de les passer en interne -> crash au démarrage).
#     Fix indispensable côté environnement, AVANT de relancer :
#         pip install --upgrade "fastapi>=0.115" "starlette>=1.0.1" "uvicorn[standard]"
#     Le code ci-dessous utilise `lifespan` (API moderne, non dépréciée,
#     recommandée par FastAPI) : il est donc déjà compatible avec
#     Starlette 1.0 une fois l'environnement corrigé.
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Démarrage de Revenue-at-Risk Decision Engine API")
    app.state.ai_engine = AIEngine()
    app.state.intent_classifier = IntentClassifier(app.state.ai_engine)
    yield
    # Shutdown
    logger.info("🛑 Arrêt de Revenue-at-Risk Decision Engine API")


app = FastAPI(
    title="Revenue-at-Risk Decision Engine API",
    description=(
        "API pour l'IA Engine avec bascule automatique Gemini/Groq/Fallback, "
        "enrichie de la boucle de Decision Challenge (Simulation Engine "
        "déterministe + reconnaissance d'intention)."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# 7. ENDPOINTS
# ============================================================================

@app.get("/", response_model=Dict[str, str])
async def root():
    return {
        "message": "Revenue-at-Risk Decision Engine API",
        "version": "2.0.0",
        "status": "running",
        "documentation": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    engine = app.state.ai_engine
    providers_status = {
        name: provider.is_available()
        for name, provider in engine.providers.items()
    }
    return HealthResponse(
        status="healthy" if any(providers_status.values()) else "degraded",
        providers=providers_status,
        version="2.0.0",
        timestamp=datetime.now().isoformat()
    )

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    engine = app.state.ai_engine
    stats = engine.get_stats()
    return StatsResponse(**stats)

@app.post("/chat", response_model=AIResponse)
async def chat(request: ChatRequest):
    """Endpoint principal de chat avec l'IA Engine"""
    try:
        engine = app.state.ai_engine

        # Construction du prompt à partir des messages
        last_message = request.messages[-1] if request.messages else None
        if not last_message or last_message.role != "user":
            raise HTTPException(
                status_code=400,
                detail="Le dernier message doit être de l'utilisateur"
            )

        # Génération de la réponse (avec l'historique complet pour garder le contexte)
        response = engine.generate(
            prompt=last_message.content,
            context_data=request.context_data,
            prompt_type=request.prompt_type,
            history=request.messages,
            max_tokens=request.max_tokens
        )

        if not response.get("success"):
            raise HTTPException(
                status_code=500,
                detail=response.get("error", "Erreur lors de la génération")
            )

        return AIResponse(
            success=True,
            content=response.get("content", ""),
            provider_used=response.get("provider_used", "unknown"),
            model=response.get("model", "unknown"),
            usage=response.get("usage")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/explain-risk", response_model=AIResponse)
async def explain_risk(data: Dict[str, Any]):
    """Explique les risques identifiés"""
    try:
        engine = app.state.ai_engine
        response = engine.generate(
            prompt="Explique les risques identifiés pour DABA de manière claire et actionnable.",
            context_data=data,
            prompt_type="explain_risk"
        )

        return AIResponse(
            success=True,
            content=response.get("content", ""),
            provider_used=response.get("provider_used", "unknown"),
            model=response.get("model", "unknown"),
            usage=response.get("usage")
        )

    except Exception as e:
        logger.error(f"❌ Erreur explain-risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend", response_model=AIResponse)
async def recommend(data: Dict[str, Any]):
    """Génère une recommandation"""
    try:
        engine = app.state.ai_engine
        response = engine.generate(
            prompt="Quelle est la meilleure action à entreprendre ?",
            context_data=data,
            prompt_type="recommend_action"
        )

        return AIResponse(
            success=True,
            content=response.get("content", ""),
            provider_used=response.get("provider_used", "unknown"),
            model=response.get("model", "unknown"),
            usage=response.get("usage")
        )

    except Exception as e:
        logger.error(f"❌ Erreur recommend: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare-scenarios", response_model=AIResponse)
async def compare_scenarios(request: ScenarioRequest):
    """Compare deux scénarios"""
    try:
        engine = app.state.ai_engine
        context = {
            "before": request.before,
            "after": request.after,
            **(request.context_data or {})
        }

        response = engine.generate(
            prompt=f"Compare ces deux scénarios. Avant: {request.before}, Après: {request.after}",
            context_data=context,
            prompt_type="compare_scenarios"
        )

        return AIResponse(
            success=True,
            content=response.get("content", ""),
            provider_used=response.get("provider_used", "unknown"),
            model=response.get("model", "unknown"),
            usage=response.get("usage")
        )

    except Exception as e:
        logger.error(f"❌ Erreur compare-scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/demo-data")
async def get_demo_data():
    """Retourne les données de démonstration"""
    return DEMO_DATA


# ----------------------------------------------------------------------
# NOUVEAU — endpoints du Simulation Engine (déterministe, sans LLM)
# ----------------------------------------------------------------------
@app.get("/situations")
async def list_situations():
    """Liste les situations simulables, pour peupler un sélecteur côté frontend."""
    return {sid: {"type": s["type"]} for sid, s in SITUATIONS.items()}

@app.post("/simulate", response_model=SimulationResponse)
async def simulate(request: SimulationRequest):
    """
    Exécute une simulation déterministe. Aucun appel LLM ici : c'est
    volontaire (cf. correction prioritaire n°2, "ne jamais laisser l'IA
    simuler elle-même").
    """
    try:
        result = SimulationEngine.run(
            request.situation_id, quantite=request.quantite, action_id=request.action_id
        )
        return SimulationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/simulate/{situation_id}", response_model=SimulationResponse)
async def get_simulation(situation_id: str):
    """Retourne l'état actuel (avant = après, aucun paramètre appliqué) d'une situation."""
    try:
        result = SimulationEngine.run(situation_id)
        return SimulationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ----------------------------------------------------------------------
# NOUVEAU — endpoint de Decision Challenge
# ----------------------------------------------------------------------
@app.post("/challenge", response_model=DecisionChallengeResponse)
async def challenge(request: DecisionChallengeRequest):
    """
    Transforme l'IA d'une interface d'EXPLICATION passive en une interface
    de CHALLENGE de la décision :

        Décision -> Question -> Simulation -> Comparaison -> Contre-argument

    Le corps de la requête contient :
        - question      : la question du dirigeant
        - context_data  : état actuel (risques, recommandations, RaR déjà calculés)
        - situation_id  : optionnel, requis uniquement si la question implique
                           un nouveau calcul (cf. GET /situations pour la liste)
    """
    try:
        engine = app.state.ai_engine
        classifier = app.state.intent_classifier
        result = handle_decision_challenge(
            engine, classifier, request.question, request.context_data, request.situation_id
        )
        return DecisionChallengeResponse(**result)
    except Exception as e:
        logger.error(f"❌ Erreur challenge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 8. POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )