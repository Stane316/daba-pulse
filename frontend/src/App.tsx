import { Suspense, lazy } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { TheaterShell } from './components/TheaterShell'
import { LoadingScreen } from './components/ui'
import { PulseProvider } from './context/PulseContext'
import { SituationScreen } from './screens/SituationScreen'

// Lazy — les 5 scènes secondaires ne sont chargées qu'à la navigation
// (code-split pour passer 662kB → ~450kB initial)
const InvestigationScreen = lazy(() =>
  import('./screens/InvestigationScreen').then((m) => ({ default: m.InvestigationScreen })),
)
const DecisionScreen = lazy(() =>
  import('./screens/DecisionScreen').then((m) => ({ default: m.DecisionScreen })),
)
const SimulationScreen = lazy(() =>
  import('./screens/SimulationScreen').then((m) => ({ default: m.SimulationScreen })),
)
const ExplanationScreen = lazy(() =>
  import('./screens/ExplanationScreen').then((m) => ({ default: m.ExplanationScreen })),
)
const HorizonScreen = lazy(() =>
  import('./screens/HorizonScreen').then((m) => ({ default: m.HorizonScreen })),
)

export default function App() {
  return (
    <PulseProvider>
      <BrowserRouter>
        <TheaterShell>
          <Suspense fallback={<LoadingScreen />}>
            <Routes>
              <Route path="/" element={<SituationScreen />} />
              <Route path="/investigation" element={<InvestigationScreen />} />
              <Route path="/decision" element={<DecisionScreen />} />
              <Route path="/simulation" element={<SimulationScreen />} />
              <Route path="/explication" element={<ExplanationScreen />} />
              <Route path="/horizon" element={<HorizonScreen />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </TheaterShell>
      </BrowserRouter>
    </PulseProvider>
  )
}
