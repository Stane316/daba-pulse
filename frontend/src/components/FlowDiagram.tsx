import { useEffect, useRef, useState } from 'react'

/** Visualisation du flux de réallocation — spatial + parallax 3 profondeurs + camion 24px (HorizonX Parallax Totem) */

export function ReallocationFlow({
  source,
  destination,
  quantite,
  produit,
}: {
  source: string
  destination: string
  quantite: number | null
  produit: string
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [offset, setOffset] = useState({ x: 0, y: 0 })
  const [reduced, setReduced] = useState(false)

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    setReduced(mq.matches)
    const h = (e: MediaQueryListEvent) => setReduced(e.matches)
    mq.addEventListener('change', h)
    return () => mq.removeEventListener('change', h)
  }, [])

  useEffect(() => {
    if (reduced) return
    const el = ref.current
    if (!el) return
    const onMove = (e: MouseEvent) => {
      const r = el.getBoundingClientRect()
      const x = (e.clientX - r.left) / r.width - 0.5
      const y = (e.clientY - r.top) / r.height - 0.5
      setOffset({ x, y })
    }
    const onLeave = () => setOffset({ x: 0, y: 0 })
    el.addEventListener('mousemove', onMove)
    el.addEventListener('mouseleave', onLeave)
    return () => {
      el.removeEventListener('mousemove', onMove)
      el.removeEventListener('mouseleave', onLeave)
    }
  }, [reduced])

  return (
    <div
      ref={ref}
      className="relative overflow-hidden rounded-xl border border-white/5 bg-charcoal-deep/50 p-5"
      style={{ perspective: '800px' }}
    >
      {/* Profondeur 1 — halo petrol lointain */}
      <div
        className="pointer-events-none absolute -left-12 top-1/2 h-24 w-24 rounded-full bg-petrol/10 blur-2xl"
        style={{
          transform: reduced ? undefined : `translate3d(${offset.x * 8}px, ${offset.y * 6}px, 0)`,
          transition: 'transform 400ms ease-out',
        }}
      />
      {/* Profondeur 1b — halo amber lointain */}
      <div
        className="pointer-events-none absolute -right-12 top-1/2 h-20 w-20 rounded-full bg-amber/8 blur-2xl"
        style={{
          transform: reduced ? undefined : `translate3d(${offset.x * -10}px, ${offset.y * -4}px, 0)`,
          transition: 'transform 500ms ease-out',
        }}
      />

      <div className="relative mb-4 flex items-center justify-between">
        <span className="text-[11px] uppercase tracking-[0.16em] text-mineral">Flux de réallocation</span>
        <span className="hidden items-center gap-1 text-[10px] text-mineral md:inline-flex">
          <span className="h-1 w-1 rounded-full bg-amber" />
          Survolez pour la profondeur
        </span>
      </div>

      <div className="relative flex flex-col items-stretch gap-3 md:flex-row md:items-center md:gap-0">
        <div
          style={{
            transform: reduced ? undefined : `translate3d(${offset.x * 12}px, ${offset.y * 4}px, 0)`,
            transition: 'transform 350ms ease-out',
          }}
          className="flex-1"
        >
          <Node label="Source" name={source} tone="sage" sub={quantite != null ? `−${quantite} u.` : undefined} />
        </div>

        {/* Profondeur 2 — flux central */}
        <div
          className="relative flex flex-1 flex-col items-center px-2 py-2 md:py-0"
          style={{
            transform: reduced ? undefined : `translate3d(${offset.x * -6}px, ${offset.y * -2}px, 0)`,
            transition: 'transform 300ms ease-out',
          }}
        >
          <svg viewBox="0 0 200 40" className="hidden h-10 w-full md:block" preserveAspectRatio="none">
            <defs>
              <linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#4F7463" />
                <stop offset="100%" stopColor="#C9963A" />
              </linearGradient>
            </defs>
            <line x1="4" y1="20" x2="196" y2="20" stroke="url(#flowGrad)" strokeWidth="2" className="flow-line" />
            <polygon points="190,14 200,20 190,26" fill="#C9963A" />
          </svg>

          {/* Camion 24px — profondeur 3 (premier plan) */}
          <div
            className="relative -mt-1 hidden md:flex h-6 w-6 items-center justify-center rounded-md border border-amber/30 bg-charcoal text-amber shadow-[0_0_0_4px_rgba(201,150,58,0.1)] md:-mt-6"
            style={{
              transform: reduced ? undefined : `translate3d(${offset.x * 16}px, ${offset.y * 8}px, 0)`,
              transition: 'transform 250ms ease-out',
            }}
            title="Transport"
          >
            <svg width="14" height="14" viewBox="0 0 24 14" fill="none" aria-hidden>
              <rect x="1" y="3" width="10" height="7" rx="1" stroke="#C9963A" strokeWidth="1.4" />
              <rect x="11" y="5" width="6" height="5" rx="1" stroke="#C9963A" strokeWidth="1.2" />
              <circle cx="6" cy="12" r="1.6" fill="#C9963A" />
              <circle cx="15" cy="12" r="1.6" fill="#C9963A" />
              <rect x="3" y="5" width="4" height="2" rx="0.5" fill="#C9963A" opacity="0.9" />
            </svg>
          </div>

          <div className="rounded-full border border-amber/30 bg-charcoal px-3 py-1 text-center shadow-sm">
            <div className="num text-sm font-semibold text-amber">{quantite != null ? `${quantite} u.` : '—'}</div>
            <div className="max-w-[140px] truncate text-[10px] text-mineral">{produit}</div>
          </div>
          <div className="mt-1 text-[10px] text-mineral md:hidden">↓</div>

          {/* Trajectoire pointillée subtile (profondeur 1) */}
          <svg viewBox="0 0 200 2" className="pointer-events-none absolute left-0 right-0 top-1/2 hidden h-[2px] w-full opacity-20 md:block" preserveAspectRatio="none">
            <line x1="0" y1="1" x2="200" y2="1" stroke="#D8C9AE" strokeWidth="0.6" strokeDasharray="3 4" />
          </svg>
        </div>

        <div
          style={{
            transform: reduced ? undefined : `translate3d(${offset.x * -12}px, ${offset.y * -4}px, 0)`,
            transition: 'transform 350ms ease-out',
          }}
          className="flex-1"
        >
          <Node label="Destination" name={destination} tone="amber" sub={quantite != null ? `+${quantite} u.` : undefined} />
        </div>
      </div>

      <div className="pointer-events-none mt-3 flex justify-center">
        <span className="rounded bg-white/5 px-2 py-0.5 text-[10px] tracking-[0.14em] text-mineral">hover → profondeur</span>
      </div>
    </div>
  )
}

function Node({
  label,
  name,
  tone,
  sub,
}: {
  label: string
  name: string
  tone: 'sage' | 'amber'
  sub?: string
}) {
  const border = tone === 'sage' ? 'border-sage/40 bg-sage/10' : 'border-amber/40 bg-amber/10'
  const text = tone === 'sage' ? 'text-sage-light' : 'text-amber'
  return (
    <div className={`min-w-[140px] flex-1 rounded-xl border px-4 py-3 ${border}`}>
      <div className={`text-[10px] uppercase tracking-[0.16em] ${text}`}>{label}</div>
      <div className="mt-1 text-sm font-medium text-bone">{name}</div>
      {sub && <div className={`num mt-1 text-xs ${text}`}>{sub}</div>}
    </div>
  )
}

export function BeforeAfterTransform({
  rarAvant,
  rarApres,
  protege,
}: {
  rarAvant: number
  rarApres: number
  protege: number
}) {
  const reduction = rarAvant > 0 ? ((rarAvant - rarApres) / rarAvant) * 100 : 0
  return (
    <div className="grid gap-3 md:grid-cols-[1fr_auto_1fr]">
      <StateCard label="Avant" rar={rarAvant} tone="risk" caption="Exposition actuelle" />
      <div className="flex flex-col items-center justify-center px-2">
        <div className="text-[10px] uppercase tracking-[0.16em] text-mineral">Action</div>
        <div className="my-2 text-amber">→</div>
        <div className="num text-center text-xs text-sage-light">−{reduction.toFixed(0)} % RaR</div>
        <div className="num mt-1 text-center text-[11px] text-bone-dim">{Math.round(protege).toLocaleString('fr-FR')} FCFA protégés</div>
      </div>
      <StateCard label="Après" rar={rarApres} tone="success" caption="Exposition simulée" />
    </div>
  )
}

function StateCard({
  label,
  rar,
  tone,
  caption,
}: {
  label: string
  rar: number
  tone: 'risk' | 'success'
  caption: string
}) {
  const border = tone === 'risk' ? 'border-risk/30 bg-risk/10' : 'border-sage/30 bg-sage/10'
  const value = tone === 'risk' ? 'text-risk-soft' : 'text-sage-light'
  return (
    <div className={`rounded-xl border p-4 ${border}`}>
      <div className="text-[10px] uppercase tracking-[0.18em] text-mineral">{label}</div>
      <div className={`num mt-2 text-2xl font-semibold md:text-3xl ${value}`}>{Math.round(rar).toLocaleString('fr-FR')}</div>
      <div className="text-xs text-mineral">FCFA</div>
      <div className="mt-2 text-xs text-bone-dim">{caption}</div>
    </div>
  )
}
