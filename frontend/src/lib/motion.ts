import { useEffect, useRef, useState } from 'react'

/**
 * Respecte les préférences d'accessibilité : désactive les animations
 * si l'utilisateur a activé "Réduire les animations".
 */
export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false)
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    setReduced(mq.matches)
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])
  return reduced
}

/**
 * Compteur animé pour les KPI financiers (RaR).
 * Utilise requestAnimationFrame + easing douce, sans dépendance externe.
 * Retourne la valeur courante (arrondie) à afficher.
 */
export function useCountUp(target: number, opts?: { duration?: number; enabled?: boolean }) {
  const duration = opts?.duration ?? 900
  const enabled = opts?.enabled ?? true
  const [value, setValue] = useState(enabled ? 0 : target)
  const prevTarget = useRef(target)
  const raf = useRef<number | null>(null)

  useEffect(() => {
    if (!enabled) {
      setValue(target)
      return
    }
    // Si la cible change peu (même ordre de grandeur), on anime depuis l'ancienne valeur
    const from = prevTarget.current
    prevTarget.current = target
    const start = performance.now()

    const tick = (now: number) => {
      const elapsed = now - start
      const t = Math.min(1, elapsed / duration)
      // easeOutCubic
      const eased = 1 - Math.pow(1 - t, 3)
      setValue(Math.round(from + (target - from) * eased))
      if (t < 1) raf.current = requestAnimationFrame(tick)
    }

    // Réduit le temps si la cible est proche de la source (évite animation trop longue)
    const delta = Math.abs(target - from)
    const adjustedDuration = delta < target * 0.1 ? duration * 0.6 : duration
    // On relance avec la durée ajustée
    if (adjustedDuration !== duration) {
      // noop — on garde duration simple pour la v1
    }

    raf.current = requestAnimationFrame(tick)
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current)
    }
  }, [target, duration, enabled])

  return value
}

/**
 * Délais d'apparition en cascade pour les cartes (stagger).
 * Utilitaire simple pour `style={{ animationDelay: `${i * 80}ms` }}`.
 */
export function staggerDelay(index: number, baseMs = 80): string {
  return `${index * baseMs}ms`
}
