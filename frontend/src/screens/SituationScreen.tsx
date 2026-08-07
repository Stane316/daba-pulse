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

        {/* Mini vue */}
        <Panel className="flex flex-col justify-between" delay={1}>
          <div>
            <div className="mb-4 text-[11px] uppercase tracking-[0.16em] text-mineral">
              Mini-vue opérationnelle
            </div>
            <div className="grid grid-cols-2 gap-4">
              <MetricBlock
                label="Stock total"
                value={formatNumber(mini.stock_total)}
                hint="unités"
              />
              <MetricBlock
                label="Demande 7j"
                value={formatNumber(mini.demande_totale)}
                hint="unités estimées"
              />
              <MetricBlock
                label="Déficit total"
                value={formatNumber(mini.deficit_total)}
                tone="risk"
                hint="unités non servies"
              />
              <MetricBlock
                label="Note Google"
                value={mini.visibilite?.note_google?.toFixed(1) ?? '—'}
                hint={`${mini.visibilite?.nb_avis ?? 0} avis`}
                tone="amber"
              />
            </div>
          </div>

          {mini.demande_par_boutique && (
            <div className="mt-6 space-y-2">
              <div className="text-[10px] uppercase tracking-[0.16em] text-mineral">
                Demande par boutique
              </div>
              {mini.demande_par_boutique.slice(0, 4).map((b) => {
                const max = mini.demande_par_boutique![0].demande || 1
                return (
                  <div key={b.boutique_id}>
                    <div className="mb-0.5 flex justify-between text-[11px]">
                      <span className="text-bone-dim">{b.nom}</span>
                      <span className="num text-mineral">{b.demande}</span>
                    </div>
                    <div className="h-1 overflow-hidden rounded-full bg-charcoal-soft">
                      <div
                        className="h-full rounded-full bg-petrol-light"
                        style={{ width: `${(b.demande / max) * 100}%` }}
                      />
                    </div>
                  </div>
                )
              })}
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
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => selectSituation(s.id)}
              className={cn(
                'animate-fade-up group grid w-full grid-cols-1 items-center gap-4 rounded-2xl border p-4 text-left transition md:grid-cols-[auto_1fr_auto_auto]',
                active
                  ? 'border-amber/40 bg-amber/8 shadow-[0_0_0_1px_rgba(201,150,58,0.15)]'
                  : 'border-white/5 bg-charcoal/50 hover:border-white/15 hover:bg-charcoal-soft/40',
                i < 5 && `delay-${Math.min(i + 1, 5)}`,
              )}
            >
              <div className="flex items-center gap-3">
                <span
                  className={cn(
                    'num flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold',
                    s.severite === 'critique'
                      ? 'bg-risk/20 text-risk-soft'
                      : 'bg-white/5 text-mineral',
                  )}
                >
                  {s.priorite}
                </span>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <ScopeTag scope={s.scope} />
                    <SeverityBadge value={s.severite} />
                  </div>
                  <div className="mt-1.5 text-sm font-medium text-bone">
                    {s.boutique?.nom ?? 'DABA — global'}
                    {s.produit ? (
                      <span className="text-bone-dim"> · {s.produit.nom}</span>
                    ) : null}
                  </div>
                </div>
              </div>

              <div className="min-w-0">
                <div className="truncate text-xs text-mineral">
                  {riskTypeLabel(s.type_risque)}
                </div>
                <div className="mt-0.5 truncate text-sm text-bone-dim">{s.signal}</div>
              </div>

              <div className="text-left md:text-right">
                <div className="text-[10px] uppercase tracking-[0.14em] text-mineral">
                  Revenu exposé
                </div>
                <div className="num text-lg font-semibold text-risk-soft">
                  {formatFCFA(s.revenue_at_risk, true)}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <ConfidenceBadge level={s.niveau_confiance} score={s.confiance} />
                <span
                  className={cn(
                    'text-xs font-medium transition',
                    active ? 'text-amber' : 'text-mineral group-hover:text-sand',
                  )}
                >
                  {active ? 'Sélectionnée' : 'Ouvrir'}
                </span>
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