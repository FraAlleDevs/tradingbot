import { PriceData, Signal } from '../types.js';

export type DbResult = {
  signal: Signal;
  confidence: number;
};

export type DbTypes = {
  btc_historical: PriceData;
  results: DbResult;
};
