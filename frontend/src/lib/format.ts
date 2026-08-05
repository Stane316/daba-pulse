/** Formatage monétaire et numérique FR — FCFA */

export function formatFCFA(value: number | null | undefined, compact = false): string {
  if (value == null || Number.isNaN(value)) return '—'
  const abs = Math.abs(value)
  if (compact && abs >= 1_000_000) {
    return `${(value / 1_000_000).toLocaleString('fr-FR', { maximumFractionDigits: 2 })} M FCFA`
  }
  if (compact && abs >= 1_000) {
    return `${(value / 1_000).toLocaleString('fr-FR', { maximumFractionDigits: 0 })} k FCFA`
  }
  return `${Math.round(value).toLocaleString('fr-FR')} FCFA`
}

export function formatNumber(value: number | null | undefined, digits = 0): string {
  if (value == null || Number.isNaN(value)) return '—'
  return value.toLocaleString('fr-FR', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })
}

export function formatPct(value: number | null | undefined, alreadyRatio = true): string {
  if (value == null || Number.isNaN(value)) return '—'
  const v = alreadyRatio ? value * 100 : value
  return `${v.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %`
}

export function severityLabel(s: string): string {
  const map: Record<string, string> = {
    critique: 'Critique',
    eleve: 'Élevé',
    modere: 'Modéré',
    faible: 'Faible',
  }
  return map[s] ?? s
}

export function confidenceLabel(s: string): string {
  const map: Record<string, string> = {
    eleve: 'Élevée',
    moyen: 'Moyenne',
    faible: 'Faible',
  }
  return map[s] ?? s
}

export function riskTypeLabel(t: string): string {
  const map: Record<string, string> = {
    rupture_stock: 'Rupture de stock',
    surstock: 'Surstock',
    demande_croissante: 'Demande croissante',
    desalignement: 'Désalignement',
    reputation_note: 'Réputation — note',
    reputation_engagement: 'Réputation — engagement',
    reputation_avis: 'Réputation — avis',
    reputation_visibilite: 'Réputation — visibilité',
    reputation_conversion: 'Réputation — conversion',
  }
  return map[t] ?? t
}
