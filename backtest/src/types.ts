export type PriceData = {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type Signal = 'buy' | 'sell' | 'hold';
