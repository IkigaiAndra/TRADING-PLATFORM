import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders the application title', () => {
    render(<App />)
    expect(screen.getByText('Trading Analytics Platform')).toBeInTheDocument()
  })

  it('renders the welcome message', () => {
    render(<App />)
    expect(screen.getByText('Welcome to Trading Analytics Platform')).toBeInTheDocument()
  })

  it('renders all feature cards', () => {
    render(<App />)
    
    expect(screen.getByText('📊 Professional Charting')).toBeInTheDocument()
    expect(screen.getByText('📈 Technical Analysis')).toBeInTheDocument()
    expect(screen.getByText('🔔 Smart Alerts')).toBeInTheDocument()
    expect(screen.getByText('💼 Portfolio Tracking')).toBeInTheDocument()
  })
})
