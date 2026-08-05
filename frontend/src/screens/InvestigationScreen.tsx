import { useNavigate } from 'react-router-dom'
import { DemandStockBars, HistoryArea } from '../components/StockDemandChart'
import {
  ConfidenceBadge,
  ErrorBanner,
  LoadingScreen,
  MetricBlock,
  Panel,
  PrimaryButton,
  SceneQuestion,
  ScopeTag,
  SeverityBadge,
} from '../components/ui'
import { usePulse } from '../context/PulseContext'
import {
  formatFCFA,
  formatNumber,
  formatPct,
  riskTypeLabel,
} from '../lib/format'

export function InvestigationScreen() {
  const { loading, error, selected, reload } = usePulse()
  const navigate = useNavigate()

  if (loading) return <LoadingScreen />
  if (error) return <ErrorBanner message={error} onRetry={() => void reload()} />
  if (!selected)
    return (
      <ErrorBanner
        message="Aucune situation sélectionnée. Retournez à l'écran Situation."
        onRetry={() => navigate('/')}
      />
    )

  const s = selected
  const isDist = s.scope === 'distribution'
  const hist =
    (s.metriques_extra?.historique_ventes as
      | { date: string; ventes: number; stock: number }[]
      | undefined) ?? []

  return (
    <div>
      <SceneQuestion
        index={2}
        question="Pourquoi cette situation est-elle critique ?"
        eyebrow="Investigation du risque"
      />

      {/* Identity strip */}
      <div className="animate-fade-up mb-8 flex flex-wrap items-center gap-3">
        <ScopeTag scope={s.scope} />
        <SeverityBadge value={s.severite} />
        <ConfidenceBadge level={s.niveau_confiance} score={s.confiance} />
        <span className="text-sm text-bone-dim">
          {s.boutique ? `${s.boutique.nom} · ${s.boutique.ville}` : 'Périmètre entreprise'}
          {s.produit ? ` · ${s.produit.nom}` : ''}
        </span>
        <span className="rounded bg-white/5 px-2 py-0.5 text-[11px] text-mineral">
          Horizon {s.horizon_jours} jours
        </span>
      </div>

      {/* SIGNAL → CAUSE → RISQUE → IMPACT */}
      <div className="mb-8 grid gap-3 md:grid-cols-4">
        {[
          { k: 'Signal', v: riskTypeLabel(s.type_risque) },
          {
            k: 'Cause',
            v: isDist
              ? `Stock ${formatNumber(s.stock_disponible)} < Demande ${formatNumber(s.demande_attendue)}`
              : s.signal.slice(0, 48) + '…',
          },
          {
            k: 'Risque',
            v: isDist
              ? `Déficit ${formatNumber(s.deficit_potentiel)} u.`
              : 'Visibilité / confiance',
          },
          {
            k: 'Impact',
            v: formatFCFA(s.revenue_at_risk, true),
          },
        ].map((step, i) => (
          <div
            key={step.k}
            className={`animate-fade-up rounded-xl border border-white/5 bg-charcoal/60 p-4 delay-${i + 1}`}
          >
            <div className="text-[10px] uppercase tracking-[0.2em] text-amber">
              {step.k}
            </div>
            <div className="mt-2 text-sm font-medium leading-snug text-bone">
              {step.v}
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        {/* Left: metrics + formula */}
        <div className="space-y-6">
          <Panel>
            <div className="mb-5 text-[11px] uppercase tracking-[0.16em] text-mineral">
              Lecture quantitative
            </div>
            {isDist ? (
              <div className="grid grid-cols-2 gap-5 md:grid-cols-3">
                <MetricBlock
                  label="Demande attendue"
                  value={formatNumber(s.demande_attendue)}
                  hint={`${s.horizon_jours} jours`}
                  tone="amber"
                  large
                />
                <MetricBlock
                  label="Stock disponible"
                  value={formatNumber(s.stock_disponible)}
                  hint={`cible ${formatNumber(s.stock_cible)}`}
                  large
                />
                <MetricBlock
                  label="Déficit potentiel"
                  value={formatNumber(s.deficit_potentiel)}
                  tone="risk"
                  large
                />
                <MetricBlock
                  label="Prix unitaire net"
                  value={formatFCFA(s.prix_unitaire ?? 0, true)}
                />
                <MetricBlock
                  label="Revenue-at-Risk"
                  value={formatFCFA(s.revenue_at_risk, true)}
                  tone="risk"
                />
                <MetricBlock
                  label="Couverture"
                  value={
                    s.metriques_extra?.couverture_jours != null
                      ? `${formatNumber(s.metriques_extra.couverture_jours as number, 1)} j`
                      : '—'
                  }
                  hint={
                    s.metriques_extra?.delai_reappro != null
                      ? `délai réappro ${s.metriques_extra.delai_reappro} j`
                      : undefined
                  }
                />
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-5">
                <MetricBlock
                  label="Note Google"
                  value={String(s.metriques_extra?.note_avis_google ?? '—')}
                  hint="/5"
                  tone="risk"
                  large
                />
                <MetricBlock
                  label="Avis"
                  value={String(s.metriques_extra?.nb_avis_google ?? '—')}
                  large
                />
                <MetricBlock
                  label="Engagement"
                  value={formatPct(s.metriques_extra?.engagement_reseaux as number)}
                />
                <MetricBlock
                  label="Visiteurs / j"
                  value={formatNumber(s.metriques_extra?.visiteurs_jour as number)}
                />
                <MetricBlock
                  label="Conversion"
                  value={formatPct(s.metriques_extra?.taux_conversion_global as number)}
                />
                <MetricBlock
                  label="RaR réputation"
                  value={formatFCFA(s.revenue_at_risk, true)}
                  tone="risk"
                />
              </div>
            )}

            {/* Formula trace */}
            <div className="mt-6 rounded-xl border border-white/5 bg-charcoal-deep/60 p-4">
              <div className="text-[10px] uppercase tracking-[0.16em] text-mineral">
                Formule traçable
              </div>
              {isDist ? (
                <p className="num mt-2 text-sm leading-relaxed text-bone-dim">
                  RaR = déficit × prix ={' '}
                  <span className="text-bone">
                    {formatNumber(s.deficit_potentiel)} ×{' '}
                    {formatNumber(s.prix_unitaire)}
                  </span>{' '}
                  ={' '}
                  <span className="text-risk-soft">
                    {formatFCFA(s.revenue_at_risk)}
                  </span>
                </p>
              ) : (
                <p className="num mt-2 text-sm leading-relaxed text-bone-dim">
                  RaR = visiteurs × conversion × prix × horizon × facteur
                  <br />
                  <span className="text-risk-soft">
                    = {formatFCFA(s.revenue_at_risk)}
                  </span>
                  {s.metriques_extra?.facteur_risque != null && (
                    <span className="text-mineral">
                      {' '}
                      (facteur {String(s.metriques_extra.facteur_risque)})
                    </span>
                  )}
                </p>
              )}
            </div>
          </Panel>

          {isDist && (
            <Panel delay={2}>
              <div className="mb-3 text-[11px] uppercase tracking-[0.16em] text-mineral">
                Demande vs stock vs déficit
              </div>
              <DemandStockBars
                demande={s.demande_attendue ?? 0}
                stock={s.stock_disponible ?? 0}
                deficit={s.deficit_potentiel ?? 0}
              />
            </Panel>
          )}
        </div>

        {/* Right: drivers + hypotheses + history */}
        <div className="space-y-6">
          <Panel delay={1}>
            <div className="mb-4 text-[11px] uppercase tracking-[0.16em] text-mineral">
              Drivers du risque
            </div>
            <ul className="space-y-3">
              {s.drivers.map((d) => (
                <li
                  key={d.code}
                  className="rounded-xl border border-white/5 bg-charcoal-deep/40 p-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-medium text-bone">{d.libelle}</div>
                      <div className="mt-1 text-xs text-bone-dim">{d.impact}</div>
                    </div>
                    <div className="num text-xs text-amber">
                      {Math.round(d.poids * 100)} %
                    </div>
                  </div>
                  <div className="mt-2 h-1 overflow-hidden rounded-full bg-charcoal-soft">
                    <div
                      className="h-full rounded-full bg-clay"
                      style={{ width: `${d.poids * 100}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </Panel>

          <Panel delay={2}>
            <div className="mb-3 text-[11px] uppercase tracking-[0.16em] text-mineral">
              Hypothèses visibles
            </div>
            <ul className="space-y-2">
              {s.hypotheses.map((h) => (
                <li key={h.cle} className="text-xs leading-relaxed">
                  <span className="text-sand">{h.libelle}</span>
                  <span className="text-mineral"> — </span>
                  <span className="text-bone-dim">{String(h.valeur)}</span>
                </li>
              ))}
            </ul>
          </Panel>

          {isDist && hist.length > 0 && (
            <Panel delay={3}>
              <div className="mb-3 text-[11px] uppercase tracking-[0.16em] text-mineral">
                Historique ventes / stock
              </div>
              <HistoryArea data={hist} />
            </Panel>
          )}
        </div>
      </div>

      <div className="mt-8 flex justify-end">
        <PrimaryButton onClick={() => navigate('/decision')}>
          Obtenir la décision recommandée
        </PrimaryButton>
      </div>
    </div>
  )
}
