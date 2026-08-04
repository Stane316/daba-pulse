import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BeforeAfterTransform } from '../components/FlowDiagram'
import { RarComparisonBars } from '../components/StockDemandChart'
import {
  ErrorBanner,
  GhostButton,
  LoadingScreen,
  MetricBlock,
  Panel,
  PrimaryButton,
  SceneQuestion,
} from '../components/ui'
import { usePulse } from '../context/PulseContext'
import { formatFCFA, formatNumber } from '../lib/format'

export function SimulationScreen() {
  const {
    loading,
    error,
    selected,
    decision,
    simulation,
    simQuantity,
    setSimQuantity,
    reload,
  } = usePulse()
  const navigate = useNavigate()
  const [localQty, setLocalQty] = useState<number | null>(null)

  const qty = localQty ?? simQuantity ?? decision?.quantite ?? 0
  const isDist = selected?.scope === 'distribution'

  const maxQty = useMemo(() => {
    if (!selected || !isDist) return 100
    const deficit = selected.deficit_potentiel ?? 30
    return Math.max(60, Math.ceil(deficit * 2))
  }, [selected, isDist])

  if (loading) return <LoadingScreen />
  if (error) return <ErrorBanner message={error} onRetry={() => void reload()} />
  if (!selected || !simulation)
    return (
      <ErrorBanner
        message="Simulation indisponible."
        onRetry={() => navigate('/')}
      />
    )

  const sim = simulation

  const applyQty = (v: number) => {
    setLocalQty(v)
    setSimQuantity(v)
  }

  const reset = () => {
    const reco = decision?.quantite ?? sim.quantite_simulee ?? 0
    applyQty(reco)
  }

  return (
    <div>
      <SceneQuestion
        index={4}
        question="Que se passe-t-il si j'applique cette décision ?"
        eyebrow="What-if Simulator"
      />

      <div className="animate-fade-up mb-6 rounded-xl border border-white/5 bg-charcoal/50 px-4 py-3 text-sm text-bone-dim">
        <span className="text-mineral">Scénario : </span>
        {sim.action_libelle}
      </div>

      {/* AVANT → ACTION → APRÈS */}
      <div className="animate-fade-up delay-1 mb-8">
        <BeforeAfterTransform
          rarAvant={sim.revenue_at_risk_avant}
          rarApres={sim.revenue_at_risk_apres}
          protege={sim.revenu_potentiellement_protege}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
        <Panel delay={2}>
          <div className="mb-5 text-[11px] uppercase tracking-[0.16em] text-mineral">
            Comparaison détaillée
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[320px] text-left text-sm">
              <thead>
                <tr className="border-b border-white/8 text-[10px] uppercase tracking-[0.14em] text-mineral">
                  <th className="pb-2 font-medium">Indicateur</th>
                  <th className="pb-2 font-medium">Avant</th>
                  <th className="pb-2 font-medium">Scénario</th>
                  <th className="pb-2 font-medium">Δ</th>
                </tr>
              </thead>
              <tbody>
                {sim.metriques.map((m) => (
                  <tr key={m.cle} className="border-b border-white/5">
                    <td className="py-2.5 text-bone-dim">{m.libelle}</td>
                    <td className="num py-2.5 text-risk-soft/90">
                      {fmt(m.avant, m.unite)}
                    </td>
                    <td className="num py-2.5 text-sage-light">
                      {fmt(m.apres, m.unite)}
                    </td>
                    <td className="num py-2.5 text-mineral">
                      {fmtDelta(m.variation, m.unite, m.sens_positif)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <div className="space-y-6">
          <Panel delay={3}>
            <div className="mb-4 text-[11px] uppercase tracking-[0.16em] text-mineral">
              Revenue-at-Risk
            </div>
            <RarComparisonBars
              avant={sim.revenue_at_risk_avant}
              apres={sim.revenue_at_risk_apres}
            />
            <div className="mt-6 grid grid-cols-2 gap-4">
              <MetricBlock
                label="Revenu protégé"
                value={formatFCFA(sim.revenu_potentiellement_protege, true)}
                tone="success"
              />
              <MetricBlock
                label="Disponibilité"
                value={`${sim.disponibilite_avant} → ${sim.disponibilite_apres}`}
              />
            </div>
          </Panel>

          {isDist && (
            <Panel delay={4}>
              <div className="mb-3 flex items-center justify-between">
                <div className="text-[11px] uppercase tracking-[0.16em] text-mineral">
                  Quantité simulée
                </div>
                <div className="num text-lg font-semibold text-amber">
                  {formatNumber(qty)} u.
                </div>
              </div>
              <input
                type="range"
                min={0}
                max={maxQty}
                step={1}
                value={qty}
                onChange={(e) => applyQty(Number(e.target.value))}
                className="w-full"
              />
              <div className="mt-2 flex justify-between text-[11px] text-mineral">
                <span>0</span>
                <span>
                  Recommandé : {formatNumber(decision?.quantite ?? 0)}
                </span>
                <span>{maxQty}</span>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {[
                  Math.round((decision?.quantite ?? 20) * 0.5),
                  decision?.quantite ?? 20,
                  Math.round((decision?.quantite ?? 20) * 1.2),
                ].map((v) => (
                  <GhostButton key={v} onClick={() => applyQty(v)}>
                    {v} u.
                  </GhostButton>
                ))}
                <GhostButton onClick={reset}>Réinitialiser</GhostButton>
              </div>
              <p className="mt-4 text-[11px] leading-relaxed text-mineral">
                Le résultat est recalculé immédiatement. La simulation examine
                les conséquences d'une hypothèse — ce n'est pas une prédiction
                certaine.
              </p>
            </Panel>
          )}
        </div>
      </div>

      {sim.hypotheses.length > 0 && (
        <Panel className="mt-6" delay={5}>
          <div className="mb-2 text-[11px] uppercase tracking-[0.16em] text-mineral">
            Hypothèses de simulation
          </div>
          <ul className="space-y-1.5">
            {sim.hypotheses.map((h) => (
              <li key={h.cle} className="text-xs text-bone-dim">
                <span className="text-sand">{h.libelle}</span> — {String(h.valeur)}
              </li>
            ))}
          </ul>
        </Panel>
      )}

      <div className="mt-8 flex justify-end">
        <PrimaryButton onClick={() => navigate('/explication')}>
          Demander l'explication IA
        </PrimaryButton>
      </div>
    </div>
  )
}

function fmt(v: string | number, unite: string) {
  if (typeof v === 'number') {
    if (unite === 'FCFA') return formatFCFA(v, true)
    return `${formatNumber(v)}${unite ? ` ${unite}` : ''}`
  }
  return String(v)
}

function fmtDelta(
  v: string | number,
  unite: string,
  sens: 'hausse' | 'baisse' | 'neutre',
) {
  if (typeof v !== 'number') return String(v)
  const sign = v > 0 ? '+' : ''
  const color =
    sens === 'baisse'
      ? v < 0
        ? 'text-sage-light'
        : v > 0
          ? 'text-risk-soft'
          : ''
      : sens === 'hausse'
        ? v > 0
          ? 'text-sage-light'
          : v < 0
            ? 'text-risk-soft'
            : ''
        : ''
  if (unite === 'FCFA')
    return <span className={color}>{sign}{formatFCFA(v, true)}</span>
  return (
    <span className={color}>
      {sign}
      {formatNumber(v)}
      {unite ? ` ${unite}` : ''}
    </span>
  )
}
