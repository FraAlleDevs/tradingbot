export type PriceData = {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type Signal = 'buy' | 'sell' | 'hold';

export type Estimate = {
  signal: Signal;
  /** Number from 0 (low confidence) to 1 (high confidence) */
  confidence: number;
};
