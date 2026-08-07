import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ErrorBanner,
  GhostButton,
  LoadingScreen,
  Panel,
  PrimaryButton,
  SceneQuestion,
} from '../components/ui'
import { usePulse } from '../context/PulseContext'
import { api } from '../lib/api'
import type { AIExplainResponse } from '../types'

const SUGGESTIONS = [
  'Pourquoi cette boutique ?',
  'Pourquoi cette quantité ?',
  'Quels facteurs expliquent le risque ?',
  'Que se passe-t-il si je réduis la quantité ?',
  'Quel revenu est potentiellement protégé ?',
]

export function ExplanationScreen() {
  const { loading, error, selectedId, selected, reload } = usePulse()
  const navigate = useNavigate()
  const [explanation, setExplanation] = useState<AIExplainResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const [question, setQuestion] = useState('')
  const [qaError, setQaError] = useState<string | null>(null)

  useEffect(() => {
    if (!selectedId) return
    let cancelled = false
    setBusy(true)
    api
      .explain(selectedId)
      .then((res) => {
        if (!cancelled) setExplanation(res)
      })
      .catch((e) => {
        if (!cancelled)
          setQaError(e instanceof Error ? e.message : 'Erreur explication')
      })
      .finally(() => {
        if (!cancelled) setBusy(false)
      })
    return () => {
      cancelled = true
    }
  }, [selectedId])

  const ask = async (q: string) => {
    if (!selectedId || !q.trim()) return
    setBusy(true)
    setQaError(null)
    try {
      const res = await api.explain(selectedId, q.trim())
      setExplanation(res)
      setQuestion('')
    } catch (e) {
      setQaError(e instanceof Error ? e.message : 'Erreur')
    } finally {
      setBusy(false)
    }
  }

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    void ask(question)
  }

  if (loading) return <LoadingScreen />
  if (error) return <ErrorBanner message={error} onRetry={() => void reload()} />
  if (!selected)
    return (
      <ErrorBanner
        message="Aucune situation sélectionnée."
        onRetry={() => navigate('/')}
      />
    )

  return (
    <div>
      <SceneQuestion
        index={5}
        question="Explique-moi pourquoi cette décision est recommandée."
        eyebrow="Explication décisionnelle"
      />

      <div className="mb-6 flex flex-wrap items-center gap-3 text-xs text-mineral">
        <span>
          Contexte : {selected.boutique?.nom ?? 'Réputation globale'}
          {selected.produit ? ` · ${selected.produit.nom}` : ''}
        </span>
        {explanation && (
          <span
            className={
              explanation.fallback
                ? 'rounded-full border border-amber/30 bg-amber/10 px-2.5 py-0.5 text-[11px] font-medium text-amber'
                : 'rounded-full border border-sage/30 bg-sage/10 px-2.5 py-0.5 text-[11px] text-sage-light'
            }
          >
            {explanation.fallback
              ? 'Mode déterministe (sans LLM) — traçable'
              : `LLM · ${explanation.model ?? 'connecté'}`}
          </span>
        )}
      </div>

      {/* Éditorial — max-w-3xl centré (HorizonX editorial, pas dashboard) */}
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 rounded-xl border border-white/5 bg-charcoal/30 px-4 py-3 text-center text-[11px] leading-relaxed text-mineral">
          Cette explication s'appuie exclusivement sur les résultats du <span className="text-sand">Risk Engine</span>, du{' '}
          <span className="text-sand">Decision Engine</span> et du <span className="text-sand">simulateur</span>. Aucun chiffre
          n'est inventé — l'application reste fonctionnelle sans modèle de langage.
        </div>

        <div className="space-y-4">
          <StoryBlock step="01" title="Situation" body={explanation?.situation} loading={busy && !explanation} accent />
          <StoryBlock step="02" title="Facteurs" body={explanation?.facteurs?.length ? explanation.facteurs.map((f) => `• ${f}`).join('\n') : undefined} loading={busy && !explanation} />
          <StoryBlock step="03" title="Décision" body={explanation?.decision} loading={busy && !explanation} />
          <StoryBlock step="04" title="Impact" body={explanation?.impact} loading={busy && !explanation} accent />
        </div>

        {explanation?.reponse && (
          <div className="mt-6 rounded-2xl border border-sage/20 bg-gradient-to-br from-charcoal via-charcoal to-sage/5 p-6 md:p-8">
            <div className="mb-3 text-[11px] uppercase tracking-[0.16em] text-sage-light">Synthèse</div>
            <div className="whitespace-pre-wrap font-display text-[15px] leading-relaxed text-bone md:text-[16px]">{explanation.reponse}</div>
            {explanation.sources && (
              <div className="mt-4 flex flex-wrap gap-2">
                {explanation.sources.map((s) => (
                  <span key={s} className="rounded-full border border-white/8 bg-white/5 px-2.5 py-1 text-[10px] text-mineral">
                    {s}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Q&A — editorial */}
        <div className="mt-8 rounded-2xl border border-white/5 bg-charcoal/50 p-6 md:p-7">
          <div className="mb-4 text-[11px] uppercase tracking-[0.16em] text-mineral">Interroger le moteur</div>
          <div className="mb-4 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <GhostButton key={s} onClick={() => void ask(s)} disabled={busy}>
                {s}
              </GhostButton>
            ))}
          </div>
          <form onSubmit={onSubmit} className="flex flex-col gap-3 sm:flex-row">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Posez une question sur les résultats calculés…"
              className="flex-1 rounded-full border border-white/10 bg-charcoal-deep px-4 py-2.5 text-sm text-bone placeholder:text-mineral focus:border-amber/40 focus:outline-none"
            />
            <PrimaryButton type="submit" disabled={busy || !question.trim()}>
              {busy ? 'Analyse…' : 'Demander'}
            </PrimaryButton>
          </form>
          {qaError && <p className="mt-3 text-xs text-risk-soft">{qaError}</p>}
        </div>

        <div className="mt-8 flex justify-center">
          <PrimaryButton onClick={() => navigate('/horizon')}>Voir l'horizon de croissance</PrimaryButton>
        </div>
      </div>
    </div>
  )
}

function StoryBlock({
  step,
  title,
  body,
  loading,
  delay,
  accent,
}: {
  step: string
  title: string
  body?: string
  loading?: boolean
  delay?: number
  accent?: boolean
}) {
  return (
    <Panel
      delay={delay}
      className={accent ? 'border-sage/25 bg-sage/5' : undefined}
    >
      <div className="mb-2 flex items-center gap-2">
        <span className="num text-xs text-amber">{step}</span>
        <span className="text-[11px] uppercase tracking-[0.18em] text-mineral">
          {title}
        </span>
      </div>
      {loading ? (
        <div className="h-16 animate-pulse rounded-lg bg-white/5" />
      ) : (
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-bone-dim">
          {body || '—'}
        </p>
      )}
    </Panel>
  )
}
