"""
GROWTH DECISION OS — Risk Engine (implémentation Python)
=========================================================

Principe central (cf. document d'architecture) : le moteur est une
fonction PURE et STATELESS. evaluer_risques() ne modifie jamais l'état
qu'on lui passe et ne dépend d'aucune variable globale. C'est ce qui
permet à simuler() de réutiliser exactement le même moteur sans
dupliquer la logique métier.

Structure d'un "etat" (dict) attendu en entrée :
{
    "produits": {product_id: {"nom":..., "prix_unitaire":..., "categorie":...}},
    "boutiques": {store_id: {"nom":..., "zone":...}},
    "ventes": [{"store_id":, "product_id":, "date": "YYYY-MM-DD", "quantite":}, ...],
    "stocks": [{"store_id":, "product_id":, "date": "YYYY-MM-DD",
                "quantite_disponible":, "seuil_min":}, ...],
    "avis": [{"store_id":, "product_id": (optionnel), "date":, "note": 1-5,
               "sentiment": "positif"/"neutre"/"negatif"}, ...],
}
"""

from __future__ import annotations
import sqlite3
from copy import deepcopy
from datetime import date, timedelta
from statistics import mean, pstdev


# ------------------------------------------------------------------
# 0. CHARGEMENT DEPUIS LA BASE RÉELLE (remplace l'exemple codé en dur)
# ------------------------------------------------------------------

def charger_etat_depuis_sqlite(chemin_db: str) -> dict:
    """
    Construit un `etat` (au format attendu par evaluer_risques) à partir
    de la base growth_decision_os.db générée par generate_dataset.py +
    load_dataset.py. Aucune donnée n'est modifiée ici — lecture seule.
    """
    conn = sqlite3.connect(chemin_db)
    conn.row_factory = sqlite3.Row

    produits = {
        r["product_id"]: {"nom": r["nom"], "prix_unitaire": r["prix_unitaire"],
                           "categorie_id": r["categorie_id"]}
        for r in conn.execute("SELECT product_id, nom, prix_unitaire, categorie_id FROM produit")
    }
    boutiques = {
        r["store_id"]: {"nom": r["nom"], "zone": r["zone"]}
        for r in conn.execute("SELECT store_id, nom, zone FROM boutique")
    }
    ventes = [
        {"store_id": r["store_id"], "product_id": r["product_id"],
         "date": r["date"], "quantite": r["quantite"]}
        for r in conn.execute("SELECT store_id, product_id, date, quantite FROM vente")
    ]
    stocks = [
        {"store_id": r["store_id"], "product_id": r["product_id"], "date": r["date"],
         "quantite_disponible": r["quantite_disponible"], "seuil_min": r["seuil_min"]}
        for r in conn.execute(
            "SELECT store_id, product_id, date, quantite_disponible, seuil_min FROM stock"
        )
    ]
    avis = [
        {"store_id": r["store_id"], "product_id": r["product_id"], "date": r["date"],
         "note": r["note"], "sentiment": r["sentiment"]}
        for r in conn.execute("SELECT store_id, product_id, date, note, sentiment FROM avis_client")
    ]

    conn.close()
    return {"produits": produits, "boutiques": boutiques, "ventes": ventes,
            "stocks": stocks, "avis": avis}


# ------------------------------------------------------------------
# 1. CALCUL DES KPI (par couple boutique/produit)
# ------------------------------------------------------------------

def _ventes_recentes(ventes, store_id, product_id, ref_date, jours):
    borne = ref_date - timedelta(days=jours)
    return [
        v["quantite"] for v in ventes
        if v["store_id"] == store_id and v["product_id"] == product_id
        and borne <= date.fromisoformat(v["date"]) <= ref_date
    ]


def _dernier_stock(stocks, store_id, product_id, ref_date):
    candidats = [
        s for s in stocks
        if s["store_id"] == store_id and s["product_id"] == product_id
        and date.fromisoformat(s["date"]) <= ref_date
    ]
    if not candidats:
        return None
    return max(candidats, key=lambda s: s["date"])


def calculer_kpis(etat, store_id, product_id, ref_date):
    """Calcule les KPI Distribution pour un couple (boutique, produit) à une date donnée."""
    ventes_7j = _ventes_recentes(etat["ventes"], store_id, product_id, ref_date, 7)
    ventes_30j = _ventes_recentes(etat["ventes"], store_id, product_id, ref_date, 30)
    stock = _dernier_stock(etat["stocks"], store_id, product_id, ref_date)

    vente_moy_7j = mean(ventes_7j) if ventes_7j else 0.0
    vente_moy_30j = mean(ventes_30j) if ventes_30j else 0.0

    couverture_jours = None
    if stock and vente_moy_7j > 0:
        couverture_jours = round(stock["quantite_disponible"] / vente_moy_7j, 1)

    return {
        "store_id": store_id,
        "product_id": product_id,
        "vente_moy_7j": vente_moy_7j,
        "vente_moy_30j": vente_moy_30j,
        "nb_semaines_historique": len(ventes_30j) // 7,
        "stock_disponible": stock["quantite_disponible"] if stock else None,
        "seuil_min": stock["seuil_min"] if stock else None,
        "couverture_jours": couverture_jours,
        "stabilite_ventes": pstdev(ventes_7j) if len(ventes_7j) > 1 else 0.0,
        "date_dernier_snapshot": stock["date"] if stock else None,
    }


def calculer_reputation(etat, store_id, ref_date, jours=7, product_id=None):
    """
    Si product_id est fourni, ne garde que les avis explicitement rattachés
    à CE produit (pas les avis généraux de la boutique) — évite qu'un avis
    négatif sur un produit A ne "contamine" à tort le KPI d'un produit B
    vendu dans la même boutique.
    """
    avis = [
        a for a in etat["avis"]
        if a["store_id"] == store_id
        and (product_id is None or a["product_id"] == product_id)
        and ref_date - timedelta(days=jours) <= date.fromisoformat(a["date"]) <= ref_date
    ]
    if not avis:
        return {"note_moyenne": None, "nb_avis": 0, "pct_negatifs": None}
    negatifs = sum(1 for a in avis if a["sentiment"] == "negatif")
    return {
        "note_moyenne": round(mean(a["note"] for a in avis), 2),
        "nb_avis": len(avis),
        "pct_negatifs": round(negatifs / len(avis), 2),
    }


# ------------------------------------------------------------------
# 2. RÈGLES MÉTIER (cf. doc d'architecture §5)
# ------------------------------------------------------------------

NB_AVIS_MIN_POUR_SIGNAL = 2  # sous ce seuil, un avis isolé est trop bruité pour justifier une alerte "critique"


def evaluer_regles(kpis, reputation_boutique, reputation_produit):
    """Retourne une liste de signaux de risque bruts pour un couple (boutique, produit).

    reputation_boutique : réputation globale de la boutique (tous produits confondus)
      -> utilisée pour `alerte_reputation` (un problème de boutique, pas de produit précis).
    reputation_produit : réputation spécifique à CE produit dans CETTE boutique
      -> utilisée pour `reputation_adjusted_demand_risk` (le lien doit être spécifique
      au produit concerné, pas une moyenne boutique qui contaminerait tous ses produits).
    """
    signaux = []

    if kpis["stock_disponible"] is None or kpis["seuil_min"] is None:
        return signaux  # pas assez de données pour statuer

    rupture_proche = kpis["stock_disponible"] < kpis["seuil_min"]
    forte_vente = (
        kpis["vente_moy_30j"] > 0
        and kpis["vente_moy_7j"] > kpis["vente_moy_30j"] * 1.2
    )
    vente_stable = kpis["vente_moy_7j"] > 0  # rupture "silencieuse" = stock bas mais vente stable

    if rupture_proche and forte_vente:
        signaux.append({"regle": "rupture_imminente_forte_vente", "niveau": "eleve"})
    elif rupture_proche and vente_stable:
        signaux.append({"regle": "rupture_silencieuse", "niveau": "moyen"})

    if kpis["couverture_jours"] is not None and kpis["couverture_jours"] > 45:
        signaux.append({"regle": "surstock", "niveau": "faible"})

    if (
        reputation_boutique["note_moyenne"] is not None
        and reputation_boutique["nb_avis"] >= NB_AVIS_MIN_POUR_SIGNAL
        and reputation_boutique["note_moyenne"] < 3.0
        and forte_vente is False
    ):
        signaux.append({"regle": "alerte_reputation", "niveau": "moyen"})

    if (
        reputation_produit["note_moyenne"] is not None
        and reputation_produit["nb_avis"] >= NB_AVIS_MIN_POUR_SIGNAL
        and reputation_produit["note_moyenne"] < 3.5
        and kpis["vente_moy_7j"] < kpis["vente_moy_30j"]
    ):
        signaux.append({"regle": "reputation_adjusted_demand_risk", "niveau": "eleve"})

    return signaux


# ------------------------------------------------------------------
# 3. REVENUE AT RISK & SCORE DE CONFIANCE
# ------------------------------------------------------------------

def calculer_revenue_at_risk(kpis, prix_unitaire, jours_avant_rupture=7):
    """Revenu estimé menacé si aucune action n'est prise avant `jours_avant_rupture` jours."""
    return round(kpis["vente_moy_7j"] * prix_unitaire * jours_avant_rupture, 2)


def calculer_score_confiance(kpis, ponderations=None, aujourdhui=None):
    """Score 0-100, décomposé pour rester explicable (cf. doc §8)."""
    p = ponderations or {"qualite": 0.30, "fraicheur": 0.20, "stabilite": 0.30, "historique": 0.20}
    aujourdhui = aujourdhui or date.today()

    qualite = 100.0 if kpis["stock_disponible"] is not None else 40.0

    if kpis["date_dernier_snapshot"] is not None:
        ecart_jours = (aujourdhui - date.fromisoformat(kpis["date_dernier_snapshot"])).days
        # 100% si <=1 jour, dégradation linéaire jusqu'à 0% à 30 jours
        fraicheur = max(0.0, 100.0 - max(0, ecart_jours - 1) * (100.0 / 29.0))
    else:
        fraicheur = 0.0

    if kpis["vente_moy_7j"] > 0:
        cv = kpis["stabilite_ventes"] / kpis["vente_moy_7j"]
        stabilite = max(0.0, 100.0 - min(cv, 1.0) * 100.0)
    else:
        stabilite = 50.0
    historique = min(kpis["nb_semaines_historique"] / 8.0, 1.0) * 100.0  # plafond à 8 semaines

    composantes = {
        "qualite": round(qualite, 1),
        "fraicheur": round(fraicheur, 1),
        "stabilite": round(stabilite, 1),
        "historique": round(historique, 1),
    }
    score = sum(composantes[k] * p[k] for k in p)
    return round(score, 1), composantes


# ------------------------------------------------------------------
# 3bis. SUGGESTION AUTOMATIQUE DE PARTENAIRE DE TRANSFERT
#       (répond à quoi / où / combien / pourquoi — cf. Écran "Decision Engine")
# ------------------------------------------------------------------

def suggerer_partenaire_transfert(etat, store_id_cible, product_id, ref_date):
    """
    Cherche, parmi les autres boutiques, celle en meilleure position pour
    fournir un transfert vers store_id_cible sur product_id. Retourne None
    si aucune boutique n'a d'excédent exploitable.
    """
    candidats = []
    for store_id in etat["boutiques"]:
        if store_id == store_id_cible:
            continue
        kpis = calculer_kpis(etat, store_id, product_id, ref_date)
        if kpis["stock_disponible"] is None or kpis["seuil_min"] is None:
            continue
        excedent = kpis["stock_disponible"] - kpis["seuil_min"]
        if excedent > 0:
            candidats.append((store_id, excedent))

    if not candidats:
        return None

    candidats.sort(key=lambda c: -c[1])
    store_source, excedent = candidats[0]

    kpis_cible = calculer_kpis(etat, store_id_cible, product_id, ref_date)
    seuil_min_cible = kpis_cible["seuil_min"] or 0
    stock_cible = kpis_cible["stock_disponible"] or 0
    besoin = max(0, seuil_min_cible * 2 - stock_cible)  # cible : revenir à 2x le seuil_min
    quantite = min(excedent, besoin)

    if quantite <= 0:
        return None

    return {
        "store_source": store_source,
        "quantite_suggeree": quantite,
        "excedent_disponible_source": excedent,
        "pourquoi": (
            f"Boutique {store_source} dispose d'un excédent de {excedent} unités "
            f"au-dessus de son propre seuil_min sur ce produit."
        ),
    }




# ------------------------------------------------------------------
# 3ter. DATA HEALTH MONITOR (version simplifiée MVP — cf. doc §9)
#       Vue d'ensemble du dataset entier, affichée AVANT toute
#       recommandation (Écran 'Executive Situation').
# ------------------------------------------------------------------

def evaluer_sante_donnees(etat, ref_date=None, type_donnees="synthetique", aujourdhui=None):
    """
    Badge de statut global du dataset — ne dépend d'aucune recommandation
    spécifique. Répond à : les données sont-elles complètes, fraîches,
    et couvrent-elles assez d'historique pour qu'on fasse confiance
    aux recommandations qui vont suivre ?
    """
    ref_date = ref_date or _date_max(etat["ventes"])
    aujourdhui = aujourdhui or date.today()

    couples_stock = {(s["store_id"], s["product_id"]) for s in etat["stocks"]}
    couples_theoriques = {
        (sid, pid) for sid in etat["boutiques"] for pid in etat["produits"]
    }

    nb_avec_stock = len(couples_stock)
    nb_theoriques = len(couples_theoriques) or 1
    pct_completude = round(100 * nb_avec_stock / nb_theoriques, 1)

    date_derniere_vente = _date_max(etat["ventes"]) if etat["ventes"] else None
    date_dernier_stock = _date_max(
        [{"date": s["date"]} for s in etat["stocks"]]
    ) if etat["stocks"] else None
    date_plus_recente = max(d for d in [date_derniere_vente, date_dernier_stock] if d) \
        if (date_derniere_vente or date_dernier_stock) else None
    fraicheur_jours = (aujourdhui - date_plus_recente).days if date_plus_recente else None

    nb_semaines_historique = round(
        (max(date.fromisoformat(v["date"]) for v in etat["ventes"])
         - min(date.fromisoformat(v["date"]) for v in etat["ventes"])).days / 7, 1
    ) if etat["ventes"] else 0

    if fraicheur_jours is None:
        statut = "critique"
    elif pct_completude >= 95 and fraicheur_jours <= 7 and nb_semaines_historique >= 6:
        statut = "bon"
    elif pct_completude >= 80 and fraicheur_jours <= 30:
        statut = "moyen"
    else:
        statut = "faible"

    return {
        "type_donnees": type_donnees,
        "statut_global": statut,
        "pct_completude_stock": pct_completude,
        "nb_couples_boutique_produit_avec_stock": nb_avec_stock,
        "nb_couples_boutique_produit_theoriques": nb_theoriques,
        "date_donnee_la_plus_recente": date_plus_recente.isoformat() if date_plus_recente else None,
        "fraicheur_jours": fraicheur_jours,
        "nb_semaines_historique_disponible": nb_semaines_historique,
        "nb_ventes_total": len(etat["ventes"]),
        "nb_avis_total": len(etat["avis"]),
    }


def _date_max(lignes_avec_date):
    return max(date.fromisoformat(l["date"]) for l in lignes_avec_date)


# ------------------------------------------------------------------
# 4. RISK ENGINE — point d'entrée principal (pur, stateless)
# ------------------------------------------------------------------

NIVEAU_VERS_PRIORITE = {"eleve": "critique", "moyen": "haute", "faible": "moyenne"}


def evaluer_risques(etat, ref_date=None):
    """
    Fonction principale du moteur : état des données -> liste de recommandations.
    Ne modifie jamais `etat`. Peut être appelée sur un état réel ou hypothétique
    (c'est exactement ce que fait simuler() ci-dessous).
    """
    ref_date = ref_date or date.today()
    recommandations = []

    couples = {(s["store_id"], s["product_id"]) for s in etat["stocks"]}

    for store_id, product_id in couples:
        kpis = calculer_kpis(etat, store_id, product_id, ref_date)
        reputation_boutique = calculer_reputation(etat, store_id, ref_date)
        reputation_produit = calculer_reputation(etat, store_id, ref_date, product_id=product_id)
        signaux = evaluer_regles(kpis, reputation_boutique, reputation_produit)
        if not signaux:
            continue

        produit = etat["produits"].get(product_id, {})
        prix = produit.get("prix_unitaire", 0)
        rar = calculer_revenue_at_risk(kpis, prix)
        score_confiance, decomposition = calculer_score_confiance(kpis)

        # niveau le plus élevé parmi les signaux détectés pour ce couple
        niveau_max = max(signaux, key=lambda s: {"faible": 0, "moyen": 1, "eleve": 2}[s["niveau"]])["niveau"]

        # Pour les ruptures, on cherche automatiquement un partenaire de transfert
        # (répond directement à quoi / où / combien / pourquoi)
        transfert_suggere = None
        if signaux[0]["regle"] in ("rupture_imminente_forte_vente", "rupture_silencieuse"):
            transfert_suggere = suggerer_partenaire_transfert(etat, store_id, product_id, ref_date)

        recommandations.append({
            "store_id": store_id,
            "product_id": product_id,
            "prix_unitaire": prix,
            "type": signaux[0]["regle"],
            "signaux": [s["regle"] for s in signaux],
            "revenue_at_risk": rar,
            "score_confiance": score_confiance,
            "score_confiance_details": decomposition,
            "priorite": NIVEAU_VERS_PRIORITE[niveau_max],
            "transfert_suggere": transfert_suggere,
        })

    recommandations.sort(key=lambda r: (-r["revenue_at_risk"], -r["score_confiance"]))
    return recommandations


# ------------------------------------------------------------------
# 5. SIMULATEUR — réutilise evaluer_risques(), ne duplique aucune règle
# ------------------------------------------------------------------

def appliquer_action(etat, action):
    """Applique une action hypothétique (ex: transfert) sur une COPIE de l'état."""
    nouvel_etat = deepcopy(etat)

    if action["type"] == "transfert":
        store_source, store_dest = action["store_source"], action["store_destination"]
        product_id, quantite = action["product_id"], action["quantite"]
        for s in nouvel_etat["stocks"]:
            if s["store_id"] == store_source and s["product_id"] == product_id:
                s["quantite_disponible"] = max(0, s["quantite_disponible"] - quantite)
            if s["store_id"] == store_dest and s["product_id"] == product_id:
                s["quantite_disponible"] += quantite

    return nouvel_etat


def simuler(action, etat, ref_date=None):
    """
    Compare risques_avant / risques_apres pour une action hypothétique.
    C'est le même moteur (evaluer_risques) appelé deux fois — aucune logique
    métier n'est réécrite ici.
    """
    ref_date = ref_date or date.today()
    etat_hypothetique = appliquer_action(etat, action)

    risques_avant = evaluer_risques(etat, ref_date)
    risques_apres = evaluer_risques(etat_hypothetique, ref_date)

    rar_avant = sum(r["revenue_at_risk"] for r in risques_avant)
    rar_apres = sum(r["revenue_at_risk"] for r in risques_apres)

    return {
        "action": action,
        "revenue_at_risk_avant": round(rar_avant, 2),
        "revenue_at_risk_apres": round(rar_apres, 2),
        "revenue_protege": round(rar_avant - rar_apres, 2),
        "nb_risques_avant": len(risques_avant),
        "nb_risques_apres": len(risques_apres),
        "risques_apres": risques_apres,
    }


def simuler_trois_scenarios(action_base, etat, ref_date=None):
    """Génère automatiquement prudent / équilibré / agressif en faisant varier
    un seul paramètre (la quantité transférée) — cf. doc §7."""
    facteurs = {"prudent": 0.5, "equilibre": 1.0, "agressif": 1.5}
    resultats = {}
    for nom, facteur in facteurs.items():
        action = dict(action_base)
        action["quantite"] = max(1, round(action_base["quantite"] * facteur))
        resultats[nom] = simuler(action, etat, ref_date)
    return resultats


# ------------------------------------------------------------------
# 6. RAPPORT — enveloppe les recommandations avec le statut des données
#    (P0 obligatoire côté équipe : "données clairement identifiées
#    comme synthétiques si nécessaire")
# ------------------------------------------------------------------

def generer_rapport(etat, ref_date=None, type_donnees="synthetique"):
    """
    Point d'entrée à utiliser côté API/FastAPI plus tard : retourne les
    recommandations ENVELOPPÉES avec les métadonnées obligatoires pour
    le jury (statut des données, date de génération, badge Data Health).
    """
    ref_date = ref_date or date.today()
    return {
        "type_donnees": type_donnees,   # "synthetique" ou "reel" — à afficher à l'écran
        "date_generation": ref_date.isoformat(),
        "sante_donnees": evaluer_sante_donnees(etat, ref_date, type_donnees=type_donnees),
        "nb_recommandations": None,     # rempli ci-dessous
        "revenue_at_risk_total": None,  # rempli ci-dessous
        "recommandations": evaluer_risques(etat, ref_date),
    }


def _finaliser_rapport(rapport):
    rapport["nb_recommandations"] = len(rapport["recommandations"])
    rapport["revenue_at_risk_total"] = round(
        sum(r["revenue_at_risk"] for r in rapport["recommandations"]), 2
    )
    return rapport


# ------------------------------------------------------------------
# DÉMONSTRATION / AUTO-TEST — lit maintenant la vraie base générée par
# generate_dataset.py + load_dataset.py (plus de données codées en dur)
# ------------------------------------------------------------------

CHEMIN_DB_PAR_DEFAUT = "dataset_output/growth_decision_os.db"

if __name__ == "__main__":
    import sys
    import json

    chemin_db = sys.argv[1] if len(sys.argv) > 1 else CHEMIN_DB_PAR_DEFAUT

    try:
        etat = charger_etat_depuis_sqlite(chemin_db)
    except Exception as e:
        print(f"Impossible de lire la base '{chemin_db}' ({e}).")
        print("Vérifiez que generate_dataset.py puis load_dataset.py ont bien été exécutés,")
        print("ou passez le chemin en argument : python3 risk_engine.py chemin/vers/growth_decision_os.db")
        sys.exit(1)

    ref_date = max(date.fromisoformat(v["date"]) for v in etat["ventes"])
    print(f"Base chargée : {chemin_db}  (date de référence détectée : {ref_date.isoformat()})\n")

    rapport = _finaliser_rapport(generer_rapport(etat, ref_date, type_donnees="synthetique"))

    print(f"=== Rapport ({rapport['nb_recommandations']} recommandations, "
          f"Revenue at Risk total = {rapport['revenue_at_risk_total']} FCFA, "
          f"données : {rapport['type_donnees']}) ===\n")
    for r in rapport["recommandations"][:5]:
        print(json.dumps(r, ensure_ascii=False, indent=2))

    if rapport["recommandations"]:
        top = rapport["recommandations"][0]
        if top["transfert_suggere"]:
            print(f"\n=== Simulation automatique de la recommandation prioritaire "
                  f"(boutique {top['store_id']}, produit {top['product_id']}) ===")
            action = {
                "type": "transfert",
                "store_source": top["transfert_suggere"]["store_source"],
                "store_destination": top["store_id"],
                "product_id": top["product_id"],
                "quantite": top["transfert_suggere"]["quantite_suggeree"],
            }
            resultat = simuler(action, etat, ref_date)
            print({k: v for k, v in resultat.items() if k != "risques_apres"})

            print("\n=== 3 scénarios automatiques (prudent/équilibré/agressif) ===")
            for nom, res in simuler_trois_scenarios(action, etat, ref_date).items():
                print(nom, "-> quantite:", res["action"]["quantite"],
                      "| revenu protege:", res["revenue_protege"])
        else:
            print("\nAucun partenaire de transfert détecté pour la recommandation prioritaire.")

