import clsx from 'clsx'
import type { ReactNode } from 'react'
import { confidenceLabel, severityLabel } from '../lib/format'
import type { ConfidenceLevel, Severity } from '../types'

export function cn(...inputs: (string | false | null | undefined)[]) {
  return clsx(inputs)
}

export function SeverityBadge({ value }: { value: Severity }) {
  const styles: Record<Severity, string> = {
    critique: 'bg-risk/20 text-risk-soft border-risk/40',
    eleve: 'bg-clay/20 text-sand border-clay/40',
    modere: 'bg-amber/15 text-amber border-amber/30',
    faible: 'bg-sage/15 text-sage-light border-sage/30',
  }
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-wider',
        styles[value],
      )}
    >
      <span
        className={cn(
          'h-1.5 w-1.5 rounded-full',
          value === 'critique' && 'bg-risk animate-pulse',
          value === 'eleve' && 'bg-clay',
          value === 'modere' && 'bg-amber',
          value === 'faible' && 'bg-sage',
        )}
      />
      {severityLabel(value)}
    </span>
  )
}

export function ConfidenceBadge({
  level,
  score,
}: {
  level: ConfidenceLevel
  score?: number
}) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-mineral/30 bg-charcoal-soft/60 px-2.5 py-0.5 text-[11px] text-bone-dim">
      Confiance {confidenceLabel(level)}
      {score != null && (
        <span className="num text-bone/80">{Math.round(score * 100)} %</span>
      )}
    </span>
  )
}

export function ScopeTag({ scope }: { scope: 'distribution' | 'reputation' }) {
  return (
    <span
      className={cn(
        'rounded px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em]',
        scope === 'distribution'
          ? 'bg-petrol/30 text-sand'
          : 'bg-plum/40 text-sand',
      )}
    >
      {scope === 'distribution' ? 'Distribution' : 'Réputation'}
    </span>
  )
}

export function SceneQuestion({
  index,
  question,
  eyebrow,
}: {
  index: number
  question: string
  eyebrow?: string
}) {
  return (
    <header className="animate-fade-up mb-8 max-w-3xl">
      <div className="mb-3 flex items-center gap-3 text-[11px] uppercase tracking-[0.22em] text-mineral">
        <span className="num text-amber">0{index}</span>
        <span className="h-px w-8 bg-mineral/40" />
        <span>{eyebrow ?? 'Decision Theater'}</span>
      </div>
      <h1 className="font-display text-[clamp(1.75rem,4vw,2.75rem)] leading-[1.15] text-bone">
        {question}
      </h1>
    </header>
  )
}

export function Panel({
  children,
  className,
  delay,
}: {
  children: ReactNode
  className?: string
  delay?: number
}) {
  return (
    <div
      className={cn(
        'animate-fade-up card-hover rounded-2xl border border-white/5 bg-charcoal/70 p-5 shadow-[0_20px_60px_-30px_rgba(0,0,0,0.7)] backdrop-blur-sm',
        delay === 1 && 'delay-1',
        delay === 2 && 'delay-2',
        delay === 3 && 'delay-3',
        delay === 4 && 'delay-4',
        className,
      )}
    >
      {children}
    </div>
  )
}

export function MetricBlock({
  label,
  value,
  hint,
  tone = 'default',
  large,
}: {
  label: string
  value: ReactNode
  hint?: string
  tone?: 'default' | 'risk' | 'success' | 'amber'
  large?: boolean
}) {
  const toneClass = {
    default: 'text-bone',
    risk: 'text-risk-soft',
    success: 'text-sage-light',
    amber: 'text-amber',
  }[tone]
  return (
    <div>
      <div className="mb-1 text-[11px] uppercase tracking-[0.16em] text-mineral">
        {label}
      </div>
      <div
        className={cn(
          'num font-medium',
          large ? 'text-3xl md:text-4xl' : 'text-xl md:text-2xl',
          toneClass,
        )}
      >
        {value}
      </div>
      {hint && <div className="mt-1 text-xs text-mineral">{hint}</div>}
    </div>
  )
}

export function PrimaryButton({
  children,
  onClick,
  disabled,
  className,
  type = 'button',
}: {
  children: ReactNode
  onClick?: () => void
  disabled?: boolean
  className?: string
  type?: 'button' | 'submit'
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'btn-shine inline-flex items-center justify-center gap-2 rounded-full bg-amber px-5 py-2.5 text-sm font-semibold text-charcoal transition hover:bg-sand disabled:cursor-not-allowed disabled:opacity-40',
        className,
      )}
    >
      {children}
    </button>
  )
}

export function GhostButton({
  children,
  onClick,
  className,
  disabled,
}: {
  children: ReactNode
  onClick?: () => void
  className?: string
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-full border border-white/10 bg-transparent px-4 py-2 text-sm text-bone transition hover:border-sand/40 hover:bg-white/5 disabled:opacity-40',
        className,
      )}
    >
      {children}
    </button>
  )
}

export function LoadingScreen() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
      <div className="h-10 w-10 animate-spin rounded-full border-2 border-amber/30 border-t-amber" />
      <p className="text-sm text-mineral">Analyse des signaux en cours…</p>
    </div>
  )
}

export function ErrorBanner({
  message,
  onRetry,
}: {
  message: string
  onRetry?: () => void
}) {
  return (
    <div className="rounded-xl border border-risk/40 bg-risk/10 px-4 py-3 text-sm text-bone">
      <div className="font-medium text-risk-soft">Impossible de charger les données</div>
      <div className="mt-1 text-bone-dim">{message}</div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 text-xs font-semibold uppercase tracking-wider text-amber"
        >
          Réessayer
        </button>
      )}
    </div>
  )
}

export function SyntheticBadge() {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded border border-white/10 bg-charcoal-soft/80 px-2 py-0.5 text-[10px] uppercase tracking-[0.14em] text-mineral"
      title="Les chiffres sont des estimations illustratives fondées sur des données synthétiques."
    >
      <span className="h-1 w-1 rounded-full bg-amber" />
      Données synthétiques
    </span>
  )
}

export function Divider({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-2">
      <div className="h-px flex-1 bg-white/8" />
      {label && (
        <span className="text-[10px] uppercase tracking-[0.2em] text-mineral">
          {label}
        </span>
      )}
      <div className="h-px flex-1 bg-white/8" />
    </div>
  )
}
