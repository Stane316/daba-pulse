import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ReallocationFlow } from '../components/FlowDiagram'
import {
  ConfidenceBadge,
  ErrorBanner,
  GhostButton,
  LoadingScreen,
  MetricBlock,
  Panel,
  PrimaryButton,
  SceneQuestion,
  ScopeTag,
} from '../components/ui'
import { usePulse } from '../context/PulseContext'
import { api } from '../lib/api'
import { formatFCFA, formatNumber } from '../lib/format'

export function DecisionScreen() {
  const { loading, error, selected, decision, simQuantity, reload } = usePulse()
  const navigate = useNavigate()
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  if (loading) return <LoadingScreen />
  if (error) return <ErrorBanner message={error} onRetry={() => void reload()} />
  if (!selected || !decision)
    return (
      <ErrorBanner
        message="Décision indisponible. Sélectionnez d'abord une situation."
        onRetry={() => navigate('/')}
      />
    )

  const d = decision
  const isDist = d.scope === 'distribution'

  const handleExport = async (format: 'markdown' | 'json') => {
    setExporting(true)
    setExportError(null)
    try {
      await api.downloadExport(selected.id, {
        format,
        quantite: simQuantity ?? d.quantite ?? undefined,
      })
    } catch (e) {
      setExportError(e instanceof Error ? e.message : 'Export impossible')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div>
      <SceneQuestion
        index={3}
        question="Que devons-nous faire ?"
        eyebrow="Decision Engine"
      />

      {/* Decision as visual center */}
      <section className="animate-fade-up relative mb-8 overflow-hidden rounded-3xl border border-amber/25 bg-gradient-to-br from-charcoal via-charcoal to-amber/10 p-6 md:p-10">
        <div className="absolute -left-16 top-0 h-48 w-48 rounded-full bg-petrol/20 blur-3xl" />
        <div className="relative">
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <ScopeTag scope={d.scope} />
            <ConfidenceBadge level={d.niveau_confiance} score={d.confiance} />
            <span className="rounded-full border border-white/10 px-2.5 py-0.5 text-[11px] text-mineral">
              Score priorité{' '}
              <span className="num text-amber">{d.score_priorite}</span>
            </span>
          </div>

          <div className="text-[11px] uppercase tracking-[0.2em] text-amber">
            Action recommandée
          </div>
          <h2 className="font-display mt-3 max-w-4xl text-[clamp(1.5rem,3.5vw,2.4rem)] leading-snug text-bone">
            {d.libelle}
          </h2>
          <p className="mt-4 max-w-3xl text-sm leading-relaxed text-bone-dim">
            {d.description}
          </p>

          {/* QUOI / OÙ / COMBIEN / POURQUOI / IMPACT */}
          <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <Fact
              q="Quoi ?"
              a={d.produit?.nom ?? (isDist ? 'Réallocation stock' : 'Action visibilité')}
            />
            <Fact
              q="Où ?"
              a={
                d.boutique_destination?.nom ??
                (isDist ? '—' : 'Entreprise (global)')
              }
            />
            <Fact
              q="Combien ?"
              a={
                d.quantite != null
                  ? `${formatNumber(d.quantite)} unités`
                  : 'Campagne qualitative'
              }
            />
            <Fact
              q="Depuis ?"
              a={d.boutique_source?.nom ?? (isDist ? 'Entrepôt / prod.' : '—')}
            />
            <Fact
              q="Impact ?"
              a={formatFCFA(d.revenu_potentiellement_protege, true)}
              highlight
            />
          </div>
        </div>
      </section>

      {isDist && d.boutique_source && d.boutique_destination && (
        <div className="animate-fade-up delay-1 mb-8">
          <ReallocationFlow
            source={d.boutique_source.nom}
            destination={d.boutique_destination.nom}
            quantite={d.quantite}
            produit={d.produit?.nom ?? 'Produit'}
          />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel delay={2}>
          <div className="mb-4 text-[11px] uppercase tracking-[0.16em] text-mineral">
            Pourquoi cette action ?
          </div>
          <ol className="space-y-3">
            {d.raisons.map((r, i) => (
              <li key={i} className="flex gap-3 text-sm leading-relaxed">
                <span className="num mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber/15 text-[11px] font-semibold text-amber">
                  {i + 1}
                </span>
                <span className="text-bone-dim">{r}</span>
              </li>
            ))}
          </ol>
        </Panel>

        <Panel delay={3}>
          <div className="mb-5 text-[11px] uppercase tracking-[0.16em] text-mineral">
            Valeur économique
          </div>
          <div className="grid grid-cols-2 gap-5">
            <MetricBlock
              label="RaR avant"
              value={formatFCFA(d.revenue_at_risk_avant, true)}
              tone="risk"
              large
            />
            <MetricBlock
              label="Revenu protégé"
              value={formatFCFA(d.revenu_potentiellement_protege, true)}
              tone="success"
              large
            />
          </div>
          <div className="mt-6 h-2 overflow-hidden rounded-full bg-charcoal-soft">
            <div
              className="h-full rounded-full bg-gradient-to-r from-risk to-sage"
              style={{
                width: `${Math.min(
                  100,
                  d.revenue_at_risk_avant > 0
                    ? (d.revenu_potentiellement_protege /
                        d.revenue_at_risk_avant) *
                      100
                    : 0,
                )}%`,
              }}
            />
          </div>
          <div className="mt-2 text-xs text-mineral">
            Part du risque potentiellement neutralisée par l'action
          </div>
        </Panel>
      </div>

      {d.alternative && (
        <Panel className="mt-6" delay={4}>
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <div className="text-[11px] uppercase tracking-[0.16em] text-mineral">
              Alternative
            </div>
            <span className="num text-xs text-mineral">
              score {d.alternative.score_priorite}
            </span>
          </div>
          <div className="text-sm font-medium text-bone">{d.alternative.libelle}</div>
          <p className="mt-2 text-xs leading-relaxed text-bone-dim">
            {d.alternative.description}
          </p>
          <div className="mt-3 text-xs text-sage-light">
            Protégé estimé :{' '}
            {formatFCFA(d.alternative.revenu_potentiellement_protege, true)}
          </div>
        </Panel>
      )}

      <div className="mt-8 flex flex-wrap items-center justify-end gap-3">
        <GhostButton
          disabled={exporting}
          onClick={() => void handleExport('markdown')}
        >
          {exporting ? 'Export…' : 'Exporter résumé (.md)'}
        </GhostButton>
        <GhostButton
          disabled={exporting}
          onClick={() => void handleExport('json')}
        >
          Exporter JSON
        </GhostButton>
        <PrimaryButton onClick={() => navigate('/simulation')}>
          Simuler l'impact
        </PrimaryButton>
      </div>
      {exportError && (
        <p className="mt-3 text-right text-xs text-risk-soft">{exportError}</p>
      )}
    </div>
  )
}

function Fact({
  q,
  a,
  highlight,
}: {
  q: string
  a: string
  highlight?: boolean
}) {
  return (
    <div className="rounded-xl border border-white/8 bg-charcoal-deep/50 p-3">
      <div className="text-[10px] uppercase tracking-[0.16em] text-mineral">{q}</div>
      <div
        className={`mt-1.5 text-sm font-medium leading-snug ${
          highlight ? 'text-sage-light' : 'text-bone'
        }`}
      >
        {a}
      </div>
    </div>
  )
}