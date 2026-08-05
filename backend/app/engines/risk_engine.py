"""Risk Engine + Revenue-at-Risk.

Détecte les risques de distribution et de réputation, estime le revenu exposé.
Toute formule est déterministe et traçable.
"""

from __future__ import annotations

from typing import Any

from app.core.config import HYPOTHESES
from app.engines.analytics import analyze_all, mini_vue_globale
from app.engines.data_loader import DataStore
from app.models.schemas import (
    BoutiqueInfo,
    ExecutiveSummary,
    Hypothese,
    ProduitInfo,
    RiskDriver,
    SituationRisque,
)


def _niveau_confiance(score: float) -> str:
    if score >= 0.75:
        return "eleve"
    if score >= 0.55:
        return "moyen"
    return "faible"


def _severite(rar: float, ratio_deficit: float) -> str:
    if rar >= 300_000 or ratio_deficit >= 0.6:
        return "critique"
    if rar >= 120_000 or ratio_deficit >= 0.35:
        return "eleve"
    if rar >= 40_000 or ratio_deficit >= 0.15:
        return "modere"
    return "faible"


def _boutique_info(store: DataStore, bid: str) -> BoutiqueInfo:
    b = store.boutique(bid)
    return BoutiqueInfo(
        id=b["id"],
        nom=b.get("nom", bid),
        ville=b.get("ville", ""),
        zone=b.get("zone", ""),
    )


def _produit_info(store: DataStore, pid: str, prix: float | None = None) -> ProduitInfo:
    p = store.produit(pid)
    return ProduitInfo(
        id=p["id"],
        nom=p.get("nom", pid),
        categorie=p.get("categorie", ""),
        prix_unitaire=float(prix if prix is not None else p.get("prix", 0)),
    )


def compute_distribution_risks(
    store: DataStore,
    analyses: list[dict[str, Any]],
) -> list[SituationRisque]:
    """Risques liés au désalignement demande / stock."""
    situations: list[SituationRisque] = []
    hyp = HYPOTHESES

    for a in analyses:
        stock = a["stock"]
        demande = a["demande_attendue"]
        deficit = a["deficit_potentiel"]
        surplus = a["surplus"]
        prix = a["prix_unitaire"]
        ratio = a["ratio_stock_cible"]
        tendance = a["tendance"]

        # --- Rupture / déficit ---
        if deficit > 0:
            rar = round(deficit * prix, 0)
            ratio_def = deficit / demande if demande > 0 else 0
            conf = min(
                0.95,
                hyp["confiance_base"]
                + (0.1 if a["ventes_7j"] > 10 else 0)
                + (0.05 if tendance >= 1.05 else 0),
            )

            drivers = [
                RiskDriver(
                    code="deficit_stock",
                    libelle="Stock insuffisant face à la demande attendue",
                    impact=f"Déficit de {deficit:.0f} unités sur {hyp['horizon_jours']} j",
                    poids=0.45,
                ),
                RiskDriver(
                    code="demande",
                    libelle="Demande attendue sur l'horizon",
                    impact=f"{demande:.0f} unités estimées",
                    poids=0.30,
                ),
            ]
            if tendance >= 1.05:
                drivers.append(
                    RiskDriver(
                        code="tendance_hausse",
                        libelle="Demande en hausse",
                        impact=f"Tendance ×{tendance:.2f}",
                        poids=0.15,
                    )
                )
            if a["couverture_jours"] < a["delai_reappro"]:
                drivers.append(
                    RiskDriver(
                        code="delai_reappro",
                        libelle="Couverture inférieure au délai de réappro",
                        impact=(
                            f"{a['couverture_jours']:.1f} j de stock vs "
                            f"{a['delai_reappro']} j de délai"
                        ),
                        poids=0.10,
                    )
                )

            signal = (
                f"Rupture probable — stock {stock:.0f} vs demande {demande:.0f}"
            )
            if tendance >= 1.08:
                type_risque = "demande_croissante"
                signal = (
                    f"Demande croissante + stock bas — "
                    f"stock {stock:.0f}, tendance ×{tendance:.2f}"
                )
            else:
                type_risque = "rupture_stock"

            situations.append(
                SituationRisque(
                    id=f"dist-{a['boutique_id']}-{a['produit_id']}",
                    type_risque=type_risque,  # type: ignore[arg-type]
                    severite=_severite(rar, ratio_def),  # type: ignore[arg-type]
                    boutique=_boutique_info(store, a["boutique_id"]),
                    produit=_produit_info(store, a["produit_id"], prix),
                    signal=signal,
                    horizon_jours=hyp["horizon_jours"],
                    demande_attendue=demande,
                    stock_disponible=stock,
                    stock_cible=a["stock_cible"],
                    deficit_potentiel=deficit,
                    prix_unitaire=prix,
                    revenue_at_risk=rar,
                    confiance=round(conf, 2),
                    niveau_confiance=_niveau_confiance(conf),  # type: ignore[arg-type]
                    drivers=drivers,
                    hypotheses=[
                        Hypothese(
                            cle="formule_rar",
                            libelle="Revenue-at-Risk distribution",
                            valeur=f"{deficit:.0f} × {prix:.0f} = {rar:.0f} FCFA",
                            source="risk_engine",
                        ),
                        Hypothese(
                            cle="horizon",
                            libelle="Horizon d'analyse",
                            valeur=f"{hyp['horizon_jours']} jours",
                            source="configuration",
                        ),
                        Hypothese(
                            cle="methode_demande",
                            libelle="Méthode d'estimation de la demande",
                            valeur=hyp["demande_methode"],
                            source="configuration",
                        ),
                    ],
                    scope="distribution",
                    metriques_extra={
                        "tendance": tendance,
                        "couverture_jours": a["couverture_jours"],
                        "moyenne_journaliere": a["moyenne_journaliere"],
                        "ventes_7j": a["ventes_7j"],
                        "delai_reappro": a["delai_reappro"],
                        "historique_ventes": a.get("historique_ventes", []),
                    },
                )
            )

        # --- Surstock (signal secondaire, RaR = capital immobilisé estimé) ---
        elif surplus > 8 and ratio >= hyp["seuil_surstock_ratio"]:
            # immobilisation partielle : 15 % du surplus × prix (hypothèse)
            rar = round(surplus * prix * 0.15, 0)
            conf = 0.62
            situations.append(
                SituationRisque(
                    id=f"surf-{a['boutique_id']}-{a['produit_id']}",
                    type_risque="surstock",
                    severite="modere" if rar < 80_000 else "eleve",
                    boutique=_boutique_info(store, a["boutique_id"]),
                    produit=_produit_info(store, a["produit_id"], prix),
                    signal=(
                        f"Surstock — {stock:.0f} unités "
                        f"(cible {a['stock_cible']:.0f})"
                    ),
                    horizon_jours=hyp["horizon_jours"],
                    demande_attendue=demande,
                    stock_disponible=stock,
                    stock_cible=a["stock_cible"],
                    deficit_potentiel=0,
                    surplus=surplus,
                    prix_unitaire=prix,
                    revenue_at_risk=rar,
                    confiance=conf,
                    niveau_confiance=_niveau_confiance(conf),  # type: ignore[arg-type]
                    drivers=[
                        RiskDriver(
                            code="surstock",
                            libelle="Stock nettement au-dessus de la cible",
                            impact=f"Surplus de {surplus:.0f} unités",
                            poids=0.6,
                        ),
                        RiskDriver(
                            code="immobilisation",
                            libelle="Capital potentiellement immobilisé",
                            impact=f"Estimation {rar:,.0f} FCFA (15 % du surplus)",
                            poids=0.4,
                        ),
                    ],
                    hypotheses=[
                        Hypothese(
                            cle="formule_surstock",
                            libelle="RaR surstock (immobilisation)",
                            valeur=f"surplus × prix × 0.15 = {rar:.0f}",
                            source="risk_engine",
                        ),
                    ],
                    scope="distribution",
                    metriques_extra={"surplus": surplus, "ratio_stock_cible": ratio},
                )
            )

    return situations


def compute_reputation_risks(store: DataStore) -> list[SituationRisque]:
    """Risques de réputation / visibilité globale (entreprise)."""
    v = store.visibilite
    hyp = HYPOTHESES
    facteurs = hyp["facteurs_risque_reputation"]

    visiteurs = float(v.get("visiteurs_jour", 0))
    conv = float(v.get("taux_conversion_global", 0))
    prix_moy = float(v.get("prix_moyen", 18000))
    note = float(v.get("note_avis_google", 5))
    nb_avis = int(v.get("nb_avis_google", 0))
    engagement = float(v.get("engagement_reseaux", 0))
    recherches = float(v.get("recherche_google_jour", 0))

    # Facteur de risque cumulé (plafonné)
    facteur = 0.0
    drivers: list[RiskDriver] = []
    type_principal = "reputation_note"

    if note < hyp["seuil_note_google_critique"]:
        facteur += facteurs["note_google_lt_3_5"]
        drivers.append(
            RiskDriver(
                code="note_google",
                libelle="Note Google sous le seuil critique",
                impact=f"Note {note}/5 (seuil {hyp['seuil_note_google_critique']})",
                poids=0.35,
            )
        )
        type_principal = "reputation_note"

    if engagement < hyp["seuil_engagement_faible"]:
        facteur += facteurs["engagement_lt_1pct"]
        drivers.append(
            RiskDriver(
                code="engagement",
                libelle="Engagement réseaux sociaux très faible",
                impact=f"{engagement * 100:.1f} % (seuil 1 %)",
                poids=0.20,
            )
        )
        if type_principal == "reputation_note" and note >= hyp["seuil_note_google_critique"]:
            type_principal = "reputation_engagement"

    if nb_avis == 0:
        facteur += facteurs["absence_avis"]
        drivers.append(
            RiskDriver(
                code="absence_avis",
                libelle="Absence d'avis Google",
                impact="0 avis publiés",
                poids=0.25,
            )
        )
        type_principal = "reputation_avis"
    elif nb_avis < 10:
        drivers.append(
            RiskDriver(
                code="peu_avis",
                libelle="Volume d'avis insuffisant",
                impact=f"Seulement {nb_avis} avis",
                poids=0.15,
            )
        )

    if recherches < hyp["seuil_visibilite_faible"]:
        facteur += facteurs["faible_visibilite"]
        drivers.append(
            RiskDriver(
                code="visibilite",
                libelle="Faible volume de recherches Google",
                impact=f"{recherches:.0f} recherches/jour",
                poids=0.15,
            )
        )

    if conv < hyp["seuil_conversion_faible"]:
        drivers.append(
            RiskDriver(
                code="conversion",
                libelle="Taux de conversion sous le seuil",
                impact=f"{conv * 100:.1f} % (seuil 2 %)",
                poids=0.15,
            )
        )

    if facteur <= 0 and not drivers:
        return []

    # RaR réputation = visiteurs × conversion × prix × facteur_risque
    # (formule cadrage — estimation journalière valorisée, sans horizon multiplié)
    horizon = hyp["horizon_jours"]
    revenu_potentiel_jour = visiteurs * conv * prix_moy
    rar = round(revenu_potentiel_jour * max(facteur, 0.05), 0)
    revenu_potentiel_horizon = revenu_potentiel_jour * horizon

    conf = 0.58  # réputation = signaux externes, confiance plus basse
    if nb_avis >= 3:
        conf += 0.05
    if visiteurs > 500:
        conf += 0.05

    signal = (
        f"Réputation globale fragile — note {note}/5, "
        f"{nb_avis} avis, engagement {engagement * 100:.1f} %"
    )

    return [
        SituationRisque(
            id="rep-global-daba",
            type_risque=type_principal,  # type: ignore[arg-type]
            severite=_severite(rar, facteur),  # type: ignore[arg-type]
            boutique=None,
            produit=None,
            signal=signal,
            horizon_jours=horizon,
            revenue_at_risk=rar,
            confiance=round(min(conf, 0.85), 2),
            niveau_confiance=_niveau_confiance(conf),  # type: ignore[arg-type]
            drivers=drivers,
            hypotheses=[
                Hypothese(
                    cle="formule_rar_rep",
                    libelle="Revenue-at-Risk réputation",
                    valeur=(
                        f"visiteurs×conv×prix×facteur = "
                        f"{visiteurs}×{conv}×{prix_moy}×{facteur:.2f} = {rar:.0f}"
                    ),
                    source="risk_engine",
                ),
                Hypothese(
                    cle="facteur_risque",
                    libelle="Facteur de risque cumulé",
                    valeur=round(facteur, 2),
                    source="configuration",
                ),
            ],
            scope="reputation",
            metriques_extra={
                "note_avis_google": note,
                "nb_avis_google": nb_avis,
                "engagement_reseaux": engagement,
                "visiteurs_jour": visiteurs,
                "taux_conversion_global": conv,
                "recherche_google_jour": recherches,
                "facteur_risque": round(facteur, 3),
                "prix_moyen": prix_moy,
                "revenu_potentiel_horizon": round(revenu_potentiel_horizon, 0),
            },
        )
    ]


def build_executive_summary(store: DataStore) -> ExecutiveSummary:
    """Pipeline complet → résumé exécutif priorisé."""
    hyp = HYPOTHESES
    analyses = analyze_all(store, hyp["horizon_jours"])
    dist = compute_distribution_risks(store, analyses)
    rep = compute_reputation_risks(store)

    all_sit = dist + rep

    # Priorisation : sévérité puis RaR
    order = {"critique": 0, "eleve": 1, "modere": 2, "faible": 3}
    all_sit.sort(key=lambda s: (order.get(s.severite, 9), -s.revenue_at_risk))
    for i, s in enumerate(all_sit, start=1):
        s.priorite = i

    # surstocks inclus dans le total distribution
    rar_dist_full = sum(s.revenue_at_risk for s in dist)
    rar_rep = sum(s.revenue_at_risk for s in rep)

    nb_crit = sum(1 for s in all_sit if s.severite == "critique")

    from datetime import datetime

    return ExecutiveSummary(
        revenue_at_risk_total=round(rar_dist_full + rar_rep, 0),
        revenue_at_risk_distribution=round(rar_dist_full, 0),
        revenue_at_risk_reputation=round(rar_rep, 0),
        nb_situations_critiques=nb_crit,
        nb_situations_total=len(all_sit),
        situations=all_sit,
        devise=hyp["devise"],
        donnees_synthetiques=True,
        disclaimer=hyp["disclaimer"],
        hypotheses_version=hyp["version"],
        date_analyse=datetime.utcnow().strftime("%Y-%m-%d"),
        mini_vue=mini_vue_globale(store, analyses),
    )


def get_situation(store: DataStore, situation_id: str) -> SituationRisque | None:
    summary = build_executive_summary(store)
    for s in summary.situations:
        if s.id == situation_id:
            return s
    return None
