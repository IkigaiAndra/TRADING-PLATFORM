/**
 * Type definitions for the Trading Analytics Platform
 */

export interface Instrument {
  instrument_id: number
  symbol: string
  instrument_type: 'equity' | 'option' | 'future'
  metadata: Record<string, any>
}

export interface Candle {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface Indicator {
  timestamp: string
  indicator_name: string
  value: number
  metadata?: Record<string, any>
}

export interface Pattern {
  pattern_id: number
  pattern_type: string
  start_timestamp: string
  end_timestamp?: string
  confidence: number
}

export interface Signal {
  signal_id: number
  timestamp: string
  signal_type: 'BUY' | 'SELL' | 'HOLD'
  confidence: number
  contributing_factors: string[]
}

export interface Alert {
  alert_id: number
  instrument_id: number
  condition_type: string
  condition_params: Record<string, any>
  delivery_channels: string[]
  is_active: boolean
  triggered_at?: string
}

export interface Position {
  instrument_id: number
  symbol: string
  quantity: number
  avg_entry_price: number
  current_price: number
  unrealized_pnl: number
}

export interface PerformanceMetrics {
  total_pnl: number
  max_drawdown: number
  sharpe_ratio: number
  win_rate: number
  avg_win: number
  avg_loss: number
  total_trades: number
}

export type Timeframe = '1D' | '5m' | '1m'
