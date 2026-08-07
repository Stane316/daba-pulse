import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api } from '../lib/api'
import type {
  DecisionAction,
  ExecutiveSummary,
  SimulationResult,
  SituationRisque,
} from '../types'

interface PulseState {
  loading: boolean
  error: string | null
  summary: ExecutiveSummary | null
  selectedId: string | null
  selected: SituationRisque | null
  decision: DecisionAction | null
  simulation: SimulationResult | null
  simQuantity: number | null
  selectSituation: (id: string) => void
  setSimQuantity: (q: number) => void
  refreshSimulation: (q?: number) => Promise<void>
  reload: () => Promise<void>
}

const PulseContext = createContext<PulseState | null>(null)

export function PulseProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [summary, setSummary] = useState<ExecutiveSummary | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [decision, setDecision] = useState<DecisionAction | null>(null)
  const [simulation, setSimulation] = useState<SimulationResult | null>(null)
  const [simQuantity, setSimQuantityState] = useState<number | null>(null)

  const loadAll = useCallback(async (preferId?: string | null, retry = true) => {
    setLoading(true)
    setError(null)
    try {
      const exec = await api.executive()
      setSummary(exec)

      // Priorité démo : B001/P005 si présent, sinon première critique
      const demo =
        exec.situations.find(
          (s) => s.boutique?.id === 'B001' && s.produit?.id === 'P005',
        ) ||
        exec.situations.find((s) => s.severite === 'critique') ||
        exec.situations[0]

      const id = preferId && exec.situations.some((s) => s.id === preferId)
        ? preferId
        : demo?.id ?? null

      setSelectedId(id)

      if (id) {
        const [dec, sim] = await Promise.all([
          api.decision(id),
          api.simulate(id),
        ])
        setDecision(dec)
        setSimulation(sim)
        setSimQuantityState(sim.quantite_simulee)
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Erreur de chargement'
      // Retry une fois sur cold start Render (503/cold start ~50s) — évite le Failed to fetch jury
      if (retry && (msg.includes('Failed to fetch') || msg.includes('503') || msg.includes('Délai dépassé'))) {
        await new Promise((r) => setTimeout(r, 900))
        return loadAll(preferId, false)
      }
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadAll()
  }, [loadAll])

  const selectSituation = useCallback(
    (id: string) => {
      setSelectedId(id)
      void (async () => {
        try {
          const [dec, sim] = await Promise.all([
            api.decision(id),
            api.simulate(id),
          ])
          setDecision(dec)
          setSimulation(sim)
          setSimQuantityState(sim.quantite_simulee)
        } catch (e) {
          setError(e instanceof Error ? e.message : 'Erreur')
        }
      })()
    },
    [],
  )

  const refreshSimulation = useCallback(
    async (q?: number) => {
      if (!selectedId) return
      const qty = q ?? simQuantity ?? undefined
      const sim = await api.simulate(selectedId, qty)
      setSimulation(sim)
      if (qty != null) setSimQuantityState(qty)
    },
    [selectedId, simQuantity],
  )

  const setSimQuantity = useCallback(
    (q: number) => {
      setSimQuantityState(q)
      void refreshSimulation(q)
    },
    [refreshSimulation],
  )

  const selected = useMemo(
    () => summary?.situations.find((s) => s.id === selectedId) ?? null,
    [summary, selectedId],
  )

  const value: PulseState = {
    loading,
    error,
    summary,
    selectedId,
    selected,
    decision,
    simulation,
    simQuantity,
    selectSituation,
    setSimQuantity,
    refreshSimulation,
    reload: () => loadAll(selectedId),
  }

  return <PulseContext.Provider value={value}>{children}</PulseContext.Provider>
}

export function usePulse() {
  const ctx = useContext(PulseContext)
  if (!ctx) throw new Error('usePulse must be used within PulseProvider')
  return ctx
}
