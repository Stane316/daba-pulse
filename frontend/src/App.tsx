import { Suspense, lazy } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { TheaterShell } from './components/TheaterShell'
import { LoadingScreen } from './components/ui'
import { PulseProvider } from './context/PulseContext'
import { ThemeProvider } from './context/ThemeContext'
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

function AnimatedRoutes() {
  const location = useLocation()
  return (
    <div key={location.pathname} className="animate-fade-up">
      <Suspense fallback={<LoadingScreen />}>
        <Routes location={location}>
          <Route path="/" element={<SituationScreen />} />
          <Route path="/investigation" element={<InvestigationScreen />} />
          <Route path="/decision" element={<DecisionScreen />} />
          <Route path="/simulation" element={<SimulationScreen />} />
          <Route path="/explication" element={<ExplanationScreen />} />
          <Route path="/horizon" element={<HorizonScreen />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <PulseProvider>
        <BrowserRouter>
          <a
            href="#main-content"
            className="sr-only z-[100] bg-amber px-4 py-2 text-sm font-medium text-charcoal focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:rounded-full"
          >
            Aller au contenu principal
          </a>
          <TheaterShell>
            <AnimatedRoutes />
          </TheaterShell>
        </BrowserRouter>
      </PulseProvider>
    </ThemeProvider>
  )
}
