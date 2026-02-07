import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>Trading Analytics Platform</h1>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<HomePage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

function HomePage() {
  return (
    <div className="home-page">
      <h2>Welcome to Trading Analytics Platform</h2>
      <p>Full-stack market analytics and portfolio management system</p>
      <div className="features">
        <div className="feature-card">
          <h3>📊 Professional Charting</h3>
          <p>TradingView-style charts with indicators and patterns</p>
        </div>
        <div className="feature-card">
          <h3>📈 Technical Analysis</h3>
          <p>Advanced indicators and pattern recognition</p>
        </div>
        <div className="feature-card">
          <h3>🔔 Smart Alerts</h3>
          <p>Real-time notifications for market conditions</p>
        </div>
        <div className="feature-card">
          <h3>💼 Portfolio Tracking</h3>
          <p>Track trades and analyze performance metrics</p>
        </div>
      </div>
    </div>
  )
}

export default App
