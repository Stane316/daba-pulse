import { useEffect, useMemo, useRef, useState } from 'react'
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

      {/* Cinematic — 27 particules RaR qui s'envolent (INC-13, HorizonX P09) */}
      <DeficitParticles
        deficitAvant={sim.metriques.find((m) => m.cle === 'deficit')?.avant as number | undefined}
        deficitApres={sim.metriques.find((m) => m.cle === 'deficit')?.apres as number | undefined}
        protege={sim.revenu_potentiellement_protege}
        qty={qty}
      />

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

function DeficitParticles({
  deficitAvant,
  deficitApres,
  protege,
  qty,
}: {
  deficitAvant?: number
  deficitApres?: number
  protege: number
  qty: number
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const count = Math.max(0, Math.round((deficitAvant ?? 0) - (deficitApres ?? 0)))
  const show = (deficitAvant ?? 0) > 0 && (deficitApres ?? 0) === 0 && count > 0

  useEffect(() => {
    if (!show || reduced || !canvasRef.current) return
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const dpr = window.devicePixelRatio || 1
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr
    ctx.scale(dpr, dpr)
    const W = rect.width
    const H = rect.height

    type P = { x: number; y: number; vx: number; vy: number; r: number; a: number }
    const particles: P[] = Array.from({ length: Math.min(count, 32) }, () => ({
      x: 20 + Math.random() * (W - 40),
      y: H - 10 - Math.random() * 18,
      vx: (Math.random() - 0.5) * 0.8,
      vy: -1.2 - Math.random() * 1.8,
      r: 2.2 + Math.random() * 1.4,
      a: 0.9,
    }))

    let raf = 0
    let t = 0
    const duration = 1400
    const start = performance.now()
    const tick = (now: number) => {
      t = now - start
      const progress = Math.min(1, t / duration)
      ctx.clearRect(0, 0, W, H)
      particles.forEach((p) => {
        p.x += p.vx
        p.y += p.vy
        p.vy -= 0.02 // léger flottement
        p.a = 0.9 * (1 - progress)
        // halo
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r * 2.2, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(201,150,58,${p.a * 0.12})`
        ctx.fill()
        // cœur
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(201,150,58,${p.a})`
        ctx.fill()
      })
      if (progress < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [show, reduced, count, qty, protege])

  if (!show) {
    // Fallback statique si pas de deficit à animer
    return (
      <div className="animate-fade-up mb-6 flex items-center justify-center gap-2 rounded-xl border border-white/5 bg-charcoal/30 px-4 py-3 text-xs text-mineral">
        <span className="h-1.5 w-1.5 rounded-full bg-amber/60" />
        {count > 0 ? `${count} unités manquantes` : 'Ajustez la quantité pour voir les unités s’envoler'} — {formatFCFA(protege, true)} protégés si déficit → 0
      </div>
    )
  }

  return (
    <div className="animate-fade-up mb-6 overflow-hidden rounded-xl border border-amber/20 bg-gradient-to-br from-charcoal via-charcoal to-amber/5 p-4">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[11px] uppercase tracking-[0.16em] text-amber">27 unités s’envolent</span>
        <span className="num text-xs font-semibold text-sage-light">{formatFCFA(protege, true)} protégés</span>
      </div>
      <div className="relative">
        <canvas ref={canvasRef} width={320} height={80} className="h-[80px] w-full" style={{ display: 'block' }} />
        {!reduced && (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <span className="rounded-full bg-amber px-3 py-1 text-[11px] font-semibold text-charcoal shadow">−{count} → 0</span>
          </div>
        )}
      </div>
      <div className="mt-2 text-center text-[11px] text-mineral">
        Chaque point = 1 unité · {reduced ? 'Animation désactivée (préférence système)' : 'Survolez le slider pour rejouer'}
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