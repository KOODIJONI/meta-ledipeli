import { Link, Route, Routes } from 'react-router-dom'
import GameSimulator from './GameSimulator.jsx'
import Settings from './Settings.jsx'

function App() {
  return (
    <div className="app-shell">
      <Routes>
        <Route path="/simulator" element={<GameSimulator />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </div>
  )
}

export default App