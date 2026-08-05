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
          <span className="rounded-full border border-white/10 px-2 py-0.5">
            {explanation.fallback
              ? 'Mode déterministe (sans LLM)'
              : `LLM · ${explanation.model ?? 'connecté'}`}
          </span>
        )}
      </div>

      {/* Structured SITUATION → FACTEURS → DÉCISION → IMPACT */}
      <div className="mb-8 grid gap-4 md:grid-cols-2">
        <StoryBlock
          step="01"
          title="Situation"
          body={explanation?.situation}
          loading={busy && !explanation}
          delay={1}
        />
        <StoryBlock
          step="02"
          title="Facteurs"
          body={
            explanation?.facteurs?.length
              ? explanation.facteurs.map((f) => `• ${f}`).join('\n')
              : undefined
          }
          loading={busy && !explanation}
          delay={2}
        />
        <StoryBlock
          step="03"
          title="Décision"
          body={explanation?.decision}
          loading={busy && !explanation}
          delay={3}
        />
        <StoryBlock
          step="04"
          title="Impact"
          body={explanation?.impact}
          loading={busy && !explanation}
          delay={4}
          accent
        />
      </div>

      {explanation?.reponse && (
        <Panel className="mb-6" delay={3}>
          <div className="mb-3 text-[11px] uppercase tracking-[0.16em] text-mineral">
            Synthèse
          </div>
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-bone-dim">
            {explanation.reponse}
          </div>
        </Panel>
      )}

      {/* Q&A */}
      <Panel delay={4}>
        <div className="mb-4 text-[11px] uppercase tracking-[0.16em] text-mineral">
          Interroger le moteur
        </div>
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
        {qaError && (
          <p className="mt-3 text-xs text-risk-soft">{qaError}</p>
        )}
        <p className="mt-4 text-[11px] leading-relaxed text-mineral">
          L'explication s'appuie exclusivement sur les résultats du Risk Engine,
          du Decision Engine et du simulateur. Aucun chiffre n'est inventé.
          L'application reste fonctionnelle sans modèle de langage.
        </p>
        {explanation?.sources && (
          <div className="mt-3 flex flex-wrap gap-2">
            {explanation.sources.map((s) => (
              <span
                key={s}
                className="rounded border border-white/8 px-2 py-0.5 text-[10px] text-mineral"
              >
                {s}
              </span>
            ))}
          </div>
        )}
      </Panel>

      <div className="mt-8 flex justify-end">
        <PrimaryButton onClick={() => navigate('/horizon')}>
          Voir l'horizon de croissance
        </PrimaryButton>
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
