/** Visualisation du flux de réallocation stock source → destination */

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
  return (
    <div className="relative overflow-hidden rounded-xl border border-white/5 bg-charcoal-deep/50 p-5">
      <div className="mb-4 text-[11px] uppercase tracking-[0.16em] text-mineral">
        Flux de réallocation
      </div>
      <div className="flex flex-col items-stretch gap-3 md:flex-row md:items-center md:gap-0">
        <Node
          label="Source"
          name={source}
          tone="sage"
          sub={quantite != null ? `−${quantite} u.` : undefined}
        />

        <div className="relative flex flex-1 flex-col items-center px-2 py-2 md:py-0">
          <svg
            viewBox="0 0 200 40"
            className="hidden h-10 w-full md:block"
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#4F7463" />
                <stop offset="100%" stopColor="#C9963A" />
              </linearGradient>
            </defs>
            <line
              x1="4"
              y1="20"
              x2="196"
              y2="20"
              stroke="url(#flowGrad)"
              strokeWidth="2"
              className="flow-line"
            />
            <polygon points="190,14 200,20 190,26" fill="#C9963A" />
          </svg>
          <div className="rounded-full border border-amber/30 bg-charcoal px-3 py-1 text-center">
            <div className="num text-sm font-semibold text-amber">
              {quantite != null ? `${quantite} u.` : '—'}
            </div>
            <div className="max-w-[140px] truncate text-[10px] text-mineral">
              {produit}
            </div>
          </div>
          <div className="mt-1 text-[10px] text-mineral md:hidden">↓</div>
        </div>

        <Node
          label="Destination"
          name={destination}
          tone="amber"
          sub={quantite != null ? `+${quantite} u.` : undefined}
        />
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
  const border =
    tone === 'sage' ? 'border-sage/40 bg-sage/10' : 'border-amber/40 bg-amber/10'
  const text = tone === 'sage' ? 'text-sage-light' : 'text-amber'
  return (
    <div className={`min-w-[140px] flex-1 rounded-xl border px-4 py-3 ${border}`}>
      <div className={`text-[10px] uppercase tracking-[0.16em] ${text}`}>
        {label}
      </div>
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
      <StateCard
        label="Avant"
        rar={rarAvant}
        tone="risk"
        caption="Exposition actuelle"
      />
      <div className="flex flex-col items-center justify-center px-2">
        <div className="text-[10px] uppercase tracking-[0.16em] text-mineral">
          Action
        </div>
        <div className="my-2 text-amber">→</div>
        <div className="num text-center text-xs text-sage-light">
          −{reduction.toFixed(0)} % RaR
        </div>
        <div className="num mt-1 text-center text-[11px] text-bone-dim">
          {Math.round(protege).toLocaleString('fr-FR')} FCFA protégés
        </div>
      </div>
      <StateCard
        label="Après"
        rar={rarApres}
        tone="success"
        caption="Exposition simulée"
      />
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
  const border =
    tone === 'risk' ? 'border-risk/30 bg-risk/10' : 'border-sage/30 bg-sage/10'
  const value =
    tone === 'risk' ? 'text-risk-soft' : 'text-sage-light'
  return (
    <div className={`rounded-xl border p-4 ${border}`}>
      <div className="text-[10px] uppercase tracking-[0.18em] text-mineral">
        {label}
      </div>
      <div className={`num mt-2 text-2xl font-semibold md:text-3xl ${value}`}>
        {Math.round(rar).toLocaleString('fr-FR')}
      </div>
      <div className="text-xs text-mineral">FCFA</div>
      <div className="mt-2 text-xs text-bone-dim">{caption}</div>
    </div>
  )
}
