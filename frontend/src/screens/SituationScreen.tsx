import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePulse } from '../context/PulseContext'
import { useCountUp, usePrefersReducedMotion } from '../lib/motion'
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
  SeverityBadge,
  cn,
} from '../components/ui'
import { api } from '../lib/api'
import { formatFCFA, formatNumber, riskTypeLabel } from '../lib/format'

export function SituationScreen() {
  const { loading, error, summary, selectedId, selectSituation, reload } =
    usePulse()
  const navigate = useNavigate()
  const fileRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState<string | null>(null)
  const [uploadErr, setUploadErr] = useState<string | null>(null)
  // Hooks must be unconditional (before early returns) — HorizonX motion
  const reducedMotion = usePrefersReducedMotion()
  const animatedRaR = useCountUp(summary?.revenue_at_risk_total ?? 0, {
    enabled: !reducedMotion && !loading && !!summary,
  })

  if (loading) return <LoadingScreen />
  if (error || !summary)
    return <ErrorBanner message={error || 'Données absentes'} onRetry={() => void reload()} />

  const situations = summary.situations
  const mini = summary.mini_vue

  const onFile = async (file: File | null) => {
    if (!file) return
    // Garde-fous jury : validation client avant réseau (évite bruit inutile)
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setUploadErr('Le fichier doit être un CSV (.csv)')
      if (fileRef.current) fileRef.current.value = ''
      return
    }
    if (file.size === 0) {
      setUploadErr('Fichier vide')
      if (fileRef.current) fileRef.current.value = ''
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      setUploadErr(`Fichier trop volumineux (${(file.size/1024).toFixed(0)} Ko). Limite 5120 Ko.`)
      if (fileRef.current) fileRef.current.value = ''
      return
    }
    setUploading(true)
    setUploadErr(null)
    setUploadMsg(null)
    try {
      const res = await api.uploadCsv(file)
      setUploadMsg(res.message)
      await reload()
    } catch (e) {
      const raw = e instanceof Error ? e.message : 'Import impossible'
      // Extrait le detail FastAPI {message, missing_columns, ...} pour message clair
      let friendly = raw
      try {
        const j = JSON.parse(raw)
        if (j.message) friendly = j.message
        if (j.missing_columns) friendly += ` — manquantes: ${j.missing_columns.join(', ')}`
      } catch { /* raw déjà lisible */ }
      setUploadErr(friendly)
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  return (
    <div>
      <SceneQuestion
        index={1}
        question="Où DABA risque-t-elle de perdre du revenu maintenant ?"
        eyebrow="Situation exécutive"
      />

      {/* Hero RaR — dominates the scene */}
      <section className="animate-fade-up mb-10 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="relative overflow-hidden rounded-3xl border border-risk/20 bg-gradient-to-br from-charcoal via-charcoal to-risk/10 p-6 md:p-10">
          <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-risk/10 blur-2xl" />
          <div className="text-[11px] uppercase tracking-[0.22em] text-risk-soft/80">
            Revenue-at-Risk total
          </div>
          <div
            className="num mt-3 font-display text-[clamp(2.8rem,8vw,5rem)] leading-none text-risk-soft"
            style={{ animation: reducedMotion ? undefined : 'count-glow 3s ease-in-out infinite' }}
          >
            {formatNumber(animatedRaR)}
          </div>
          <div className="mt-2 text-lg text-bone-dim">FCFA exposés</div>

          <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-3">
            <MetricBlock
              label="Distribution"
              value={formatFCFA(summary.revenue_at_risk_distribution, true)}
              tone="amber"
            />
            <MetricBlock
              label="Réputation"
              value={formatFCFA(summary.revenue_at_risk_reputation, true)}
              tone="default"
            />
            <MetricBlock
              label="Critiques"
              value={`${summary.nb_situations_critiques} / ${summary.nb_situations_total}`}
              tone="risk"
            />
          </div>

          <p className="mt-6 max-w-xl text-xs leading-relaxed text-mineral">
            {summary.disclaimer}
          </p>
        </div>

        {/* Mini vue — Editorial stack (INC-10: HorizonX 1-col + sparkline) */}
        <Panel className="flex flex-col" delay={1}>
          <div className="mb-5 text-[11px] uppercase tracking-[0.16em] text-mineral">
            Mini-vue opérationnelle
          </div>
          <div className="divide-y divide-white/5">
            <div className="flex items-center justify-between py-3 first:pt-0">
              <span className="text-[11px] uppercase tracking-[0.16em] text-mineral">Stock total</span>
              <span className="num text-lg font-medium text-bone">
                {formatNumber(mini.stock_total)} <span className="text-xs font-normal text-mineral">unités</span>
              </span>
            </div>
            <div className="flex items-center justify-between py-3">
              <span className="text-[11px] uppercase tracking-[0.16em] text-mineral">Demande 7j</span>
              <span className="num text-lg font-medium text-bone">
                {formatNumber(mini.demande_totale)} <span className="text-xs font-normal text-mineral">estimées</span>
              </span>
            </div>
            <div className="flex items-center justify-between py-3">
              <span className="text-[11px] uppercase tracking-[0.16em] text-mineral">Déficit total</span>
              <span className="num text-lg font-semibold text-risk-soft">
                {formatNumber(mini.deficit_total)} <span className="text-xs font-normal text-mineral">non servies</span>
              </span>
            </div>
            <div className="flex items-center justify-between py-3">
              <span className="text-[11px] uppercase tracking-[0.16em] text-mineral">Note Google</span>
              <span className="num text-lg font-medium text-amber">
                {mini.visibilite?.note_google?.toFixed(1) ?? '—'} <span className="text-xs font-normal text-mineral">{mini.visibilite?.nb_avis ?? 0} avis</span>
              </span>
            </div>
          </div>

          {mini.demande_par_boutique && (
            <div className="mt-6">
              <div className="mb-3 text-[10px] uppercase tracking-[0.16em] text-mineral">Demande par boutique</div>
              <div className="space-y-3">
                {mini.demande_par_boutique.slice(0, 4).map((b) => {
                  const max = mini.demande_par_boutique![0].demande || 1
                  return (
                    <div key={b.boutique_id} className="group flex items-center gap-3">
                      <span className="w-28 truncate text-[11px] text-bone-dim">{b.nom}</span>
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-charcoal-soft">
                        <div
                          className="h-full rounded-full bg-petrol-light transition-all duration-700"
                          style={{ width: `${(b.demande / max) * 100}%` }}
                        />
                      </div>
                      <span className="num w-10 text-right text-[11px] text-mineral">{b.demande}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </Panel>
      </section>

      <Panel className="mb-8" delay={2}>
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-[0.16em] text-mineral">
              Observer — données
            </div>
            <p className="mt-1 max-w-xl text-sm text-bone-dim">
              Importez un CSV ventes/stocks (colonnes MVP) ou conservez le jeu
              synthétique de démonstration.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <input
              ref={fileRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => void onFile(e.target.files?.[0] ?? null)}
            />
            <GhostButton disabled={uploading} onClick={() => fileRef.current?.click()}>
              {uploading ? 'Import…' : 'Importer un CSV'}
            </GhostButton>
            <GhostButton
              disabled={uploading}
              onClick={() => {
                void (async () => {
                  setUploading(true)
                  setUploadErr(null)
                  try {
                    await api.dataReload()
                    setUploadMsg('Jeu synthétique de démonstration rechargé.')
                    await reload()
                  } catch (e) {
                    setUploadErr(
                      e instanceof Error ? e.message : 'Rechargement impossible',
                    )
                  } finally {
                    setUploading(false)
                  }
                })()
              }}
            >
              Recharger le sample
            </GhostButton>
          </div>
        </div>
        {uploadMsg && (
          <p className="mt-3 text-xs text-sage-light">{uploadMsg}</p>
        )}
        {uploadErr && (
          <p className="mt-3 text-xs text-risk-soft">{uploadErr}</p>
        )}
      </Panel>

      {/* Situations prioritaires */}
      <div className="mb-4 flex items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl text-bone">Situations prioritaires</h2>
          <p className="mt-1 text-sm text-mineral">
            Sélectionnez une situation pour ouvrir l'investigation.
          </p>
        </div>
      </div>

      <div className="grid gap-3">
        {situations.map((s, i) => {
          const active = s.id === selectedId
          const isHero = i === 0
          if (isHero) {
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => selectSituation(s.id)}
                className={cn(
                  'animate-fade-up group grid w-full grid-cols-1 items-center gap-4 rounded-3xl border-2 p-6 text-left transition md:grid-cols-[auto_1fr_auto_auto]',
                  active
                    ? 'border-amber/40 bg-gradient-to-br from-amber/10 via-charcoal to-charcoal shadow-[0_0_0_1px_rgba(201,150,58,0.15)]'
                    : 'border-amber/20 bg-charcoal/60 hover:border-amber/30 hover:bg-charcoal-soft/40',
                  'delay-1',
                )}
              >
                <div className="flex items-center gap-3">
                  <span className="num flex h-12 w-12 items-center justify-center rounded-full bg-amber text-base font-bold text-charcoal">1</span>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <ScopeTag scope={s.scope} />
                      <SeverityBadge value={s.severite} />
                    </div>
                    <div className="mt-2 text-base font-semibold text-bone">
                      {s.boutique?.nom ?? 'DABA — global'}
                      {s.produit ? <span className="text-bone-dim"> · {s.produit.nom}</span> : null}
                    </div>
                  </div>
                </div>

                <div className="min-w-0">
                  <div className="truncate text-xs uppercase tracking-[0.14em] text-mineral">{riskTypeLabel(s.type_risque)}</div>
                  <div className="mt-1 text-sm leading-snug text-bone-dim">{s.signal}</div>
                </div>

                <div className="text-left md:text-right">
                  <div className="text-[10px] uppercase tracking-[0.14em] text-mineral">Revenu exposé</div>
                  <div className="num text-xl font-bold text-risk-soft">{formatFCFA(s.revenue_at_risk, true)}</div>
                  <div className="mt-1 text-[10px] text-mineral">Priorité absolue — {s.deficit_potentiel ?? '—'} u. manquantes</div>
                </div>

                <div className="flex flex-col items-end gap-2">
                  <ConfidenceBadge level={s.niveau_confiance} score={s.confiance} />
                  <span className={cn('text-xs font-semibold', active ? 'text-amber' : 'text-mineral group-hover:text-sand')}>
                    {active ? 'Sélectionnée' : 'Ouvrir →'}
                  </span>
                </div>
              </button>
            )
          }
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => selectSituation(s.id)}
              className={cn(
                'animate-fade-up group flex w-full items-center justify-between gap-3 rounded-xl border px-4 py-3 text-left transition',
                active
                  ? 'border-amber/30 bg-amber/5'
                  : 'border-white/5 bg-charcoal/40 hover:border-white/10 hover:bg-charcoal-soft/30',
                `delay-${Math.min(i, 5)}`,
              )}
            >
              <div className="flex items-center gap-2.5">
                <span
                  className={cn(
                    'num flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold',
                    s.severite === 'critique' ? 'bg-risk/20 text-risk-soft' : 'bg-white/5 text-mineral',
                  )}
                >
                  {s.priorite}
                </span>
                <span className="hidden sm:inline-flex">
                  <SeverityBadge value={s.severite} />
                </span>
                <span className="text-sm font-medium text-bone truncate max-w-[160px] md:max-w-[200px]">
                  {s.boutique?.nom ?? 'Global'} {s.produit ? <span className="text-bone-dim hidden md:inline">· {s.produit.nom}</span> : null}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="num text-sm font-semibold text-risk-soft hidden md:inline">{formatFCFA(s.revenue_at_risk, true)}</span>
                <span className="num text-sm font-semibold text-risk-soft md:hidden">{(s.revenue_at_risk / 1000).toFixed(0)}k</span>
                <span className={cn('text-xs', active ? 'text-amber' : 'text-mineral group-hover:text-sand')}>{active ? '●' : '→'}</span>
              </div>
            </button>
          )
        })}
      </div>

      <div className="mt-8 flex justify-end">
        <PrimaryButton onClick={() => navigate('/investigation')}>
          Investiguer la situation sélectionnée
        </PrimaryButton>
      </div>
    </div>
  )
}