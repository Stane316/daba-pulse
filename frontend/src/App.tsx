import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { TheaterShell } from './components/TheaterShell'
import { PulseProvider } from './context/PulseContext'
import { DecisionScreen } from './screens/DecisionScreen'
import { ExplanationScreen } from './screens/ExplanationScreen'
import { HorizonScreen } from './screens/HorizonScreen'
import { InvestigationScreen } from './screens/InvestigationScreen'
import { SimulationScreen } from './screens/SimulationScreen'
import { SituationScreen } from './screens/SituationScreen'

export default function App() {
  return (
    <PulseProvider>
      <BrowserRouter>
        <TheaterShell>
          <Routes>
            <Route path="/" element={<SituationScreen />} />
            <Route path="/investigation" element={<InvestigationScreen />} />
            <Route path="/decision" element={<DecisionScreen />} />
            <Route path="/simulation" element={<SimulationScreen />} />
            <Route path="/explication" element={<ExplanationScreen />} />
            <Route path="/horizon" element={<HorizonScreen />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </TheaterShell>
      </BrowserRouter>
    </PulseProvider>
  )
}
