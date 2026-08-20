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
  'Et si on envoyait 20 unités ?',
  'Quelle hypothèse est la plus fragile ?',
  'Et si on n\'agit pas ?',
]

// INC-20 — libellés lisibles des intentions détectées par le moteur.
const INTENT_LABELS: Record<string, string> = {
  EXPLAIN: 'Expliquer',
  CHALLENGE: 'Challenger la recommandation',
  COMPARE: 'Comparer des scénarios',
  ALTERNATIVE: 'Explorer une alternative',
  JUSTIFY: 'Justifier la décision',
  RESUME: 'Résumer',
  LIMITS: 'Tester les limites — hypothèses fragiles',
}

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

  // INC-20 — 4 blocs (rétro-compatibles si l'API répond sans eux).
  const faits = explanation?.faits?.length
    ? explanation.faits
    : explanation
      ? [explanation.situation, ...explanation.facteurs]
      : undefined
  const hypotheses = explanation?.hypotheses?.length
    ? explanation.hypotheses
    : undefined
  const interpretation = explanation?.interpretation || explanation?.decision
  const incertitude = explanation?.incertitude?.length
    ? explanation.incertitude
    : undefined

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
          Cette explication s'appuie exclusivement sur les résultats du{' '}
          <span className="text-sand">Risk Engine</span>, du{' '}
          <span className="text-sand">Decision Engine</span> et du{' '}
          <span className="text-sand">simulateur</span>. Aucun chiffre
          n'est inventé — l'application reste fonctionnelle sans modèle de langage.
        </div>

        {explanation?.intention && (
          <div className="mb-5 flex items-center gap-2.5 text-[11px] uppercase tracking-[0.16em] text-mineral">
            <span className="h-1.5 w-1.5 rounded-full bg-amber" />
            Intention détectée :{' '}
            <span className="font-medium text-bone">
              {INTENT_LABELS[explanation.intention] ?? explanation.intention}
            </span>
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          <ChallengeBlock
            step="01"
            title="Faits"
            badge="calculé par le moteur"
            tone="sage"
            items={faits}
            loading={busy && !explanation}
          />
          <ChallengeBlock
            step="02"
            title="Hypothèses"
            badge="supposé · versionné"
            tone="amber"
            items={hypotheses}
            fallback="L'API n'a pas fourni le bloc Hypothèses (voir Synthèse)."
            loading={busy && !explanation}
          />
          <ChallengeBlock
            step="03"
            title="Interprétation"
            badge="lecture décisionnelle"
            tone="sage"
            body={interpretation}
            loading={busy && !explanation}
          />
          <ChallengeBlock
            step="04"
            title="Incertitude"
            badge="ce qui pourrait changer la décision"
            tone="risk"
            items={incertitude}
            fallback="L'API n'a pas fourni le bloc Incertitude (voir Synthèse)."
            loading={busy && !explanation}
          />
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

const TONES: Record<'sage' | 'amber' | 'risk', string> = {
  sage: 'border-sage/25 bg-sage/5',
  amber: 'border-amber/20 bg-amber/5',
  risk: 'border-risk/25 bg-risk/5',
}

function ChallengeBlock({
  step,
  title,
  badge,
  tone,
  items,
  body,
  fallback,
  loading,
}: {
  step: string
  title: string
  badge: string
  tone: 'sage' | 'amber' | 'risk'
  items?: string[]
  body?: string
  fallback?: string
  loading?: boolean
}) {
  return (
    <Panel className={TONES[tone]}>
      <div className="mb-2 flex items-center gap-2">
        <span className="num text-xs text-amber">{step}</span>
        <span className="text-[11px] uppercase tracking-[0.18em] text-mineral">
          {title}
        </span>
        <span className="ml-auto rounded-full border border-white/8 bg-white/5 px-2 py-0.5 text-[9px] uppercase tracking-[0.12em] text-mineral">
          {badge}
        </span>
      </div>
      {loading ? (
        <div className="h-16 animate-pulse rounded-lg bg-white/5" />
      ) : items?.length ? (
        <ul className="space-y-1.5">
          {items.map((item) => (
            <li key={item} className="flex gap-2 text-sm leading-relaxed text-bone-dim">
              <span className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-amber/70" />
              <span className="whitespace-pre-wrap">{item}</span>
            </li>
          ))}
        </ul>
      ) : body ? (
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-bone-dim">{body}</p>
      ) : (
        <p className="text-sm leading-relaxed text-bone-dim/60">{fallback ?? '—'}</p>
      )}
    </Panel>
  )
}
