export type Severity = 'critique' | 'eleve' | 'modere' | 'faible'
export type ConfidenceLevel = 'eleve' | 'moyen' | 'faible'
export type Scope = 'distribution' | 'reputation'

export interface BoutiqueInfo {
  id: string
  nom: string
  ville: string
  zone: string
}

export interface ProduitInfo {
  id: string
  nom: string
  categorie: string
  unite?: string
  prix_unitaire: number
}

export interface Hypothese {
  cle: string
  libelle: string
  valeur: string | number
  source: string
}

export interface RiskDriver {
  code: string
  libelle: string
  impact: string
  poids: number
}

export interface SituationRisque {
  id: string
  type_risque: string
  severite: Severity
  boutique: BoutiqueInfo | null
  produit: ProduitInfo | null
  signal: string
  horizon_jours: number
  demande_attendue: number | null
  stock_disponible: number | null
  stock_cible: number | null
  deficit_potentiel: number | null
  surplus: number | null
  prix_unitaire: number | null
  revenue_at_risk: number
  confiance: number
  niveau_confiance: ConfidenceLevel
  drivers: RiskDriver[]
  hypotheses: Hypothese[]
  priorite: number
  scope: Scope
  metriques_extra: Record<string, unknown>
}

export interface ExecutiveSummary {
  revenue_at_risk_total: number
  revenue_at_risk_distribution: number
  revenue_at_risk_reputation: number
  nb_situations_critiques: number
  nb_situations_total: number
  situations: SituationRisque[]
  devise: string
  donnees_synthetiques: boolean
  disclaimer: string
  hypotheses_version: string
  date_analyse: string
  mini_vue: {
    stock_total?: number
    demande_totale?: number
    deficit_total?: number
    nb_paires_deficit?: number
    nb_paires_surstock?: number
    demande_par_boutique?: { boutique_id: string; nom: string; demande: number }[]
    visibilite?: {
      note_google?: number
      nb_avis?: number
      engagement?: number
      visiteurs?: number
      conversion?: number
    }
  }
}

export interface DecisionAction {
  id: string
  situation_id: string
  type_action: string
  libelle: string
  description: string
  produit: ProduitInfo | null
  boutique_destination: BoutiqueInfo | null
  boutique_source: BoutiqueInfo | null
  quantite: number | null
  score_priorite: number
  confiance: number
  niveau_confiance: ConfidenceLevel
  raisons: string[]
  revenue_at_risk_avant: number
  revenu_potentiellement_protege: number
  alternative: DecisionAction | null
  metriques: Record<string, unknown>
  scope: Scope
}

export interface SimulationMetric {
  cle: string
  libelle: string
  avant: string | number
  apres: string | number
  variation: string | number
  unite: string
  sens_positif: 'hausse' | 'baisse' | 'neutre'
}

export interface SimulationResult {
  situation_id: string
  action_libelle: string
  quantite_simulee: number | null
  metriques: SimulationMetric[]
  revenue_at_risk_avant: number
  revenue_at_risk_apres: number
  revenu_potentiellement_protege: number
  disponibilite_avant: string
  disponibilite_apres: string
  hypotheses: Hypothese[]
  scope: Scope
}

export interface AIExplainResponse {
  situation: string
  facteurs: string[]
  decision: string
  impact: string
  reponse: string
  sources: string[]
  fallback: boolean
  model: string | null
}

export interface DataStatus {
  source: string
  type: 'synthetiques' | 'reelles'
  nb_lignes: number
  nb_boutiques: number
  nb_produits: number
  periode_debut: string
  periode_fin: string
  charge_le: string
  valide: boolean
  avertissements: string[]
}

export type SceneId =
  | 'situation'
  | 'investigation'
  | 'decision'
  | 'simulation'
  | 'explication'
  | 'horizon'

export interface SceneMeta {
  id: SceneId
  index: number
  label: string
  question: string
  path: string
}
