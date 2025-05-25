import { PriceData, Signal } from '../types.js';

export type DbReportCard = {
  id?: number;
  created_at?: string;
  algorithm_version: string;
  start_date: string;
  end_date: string;
  /** Percentage of valuation change */
  performance: number;
};

export type DbResult = {
  id?: number;
  report_card_id: number;
  symbol: 'BTC/USDT';
  signal: Uppercase<Signal>;
  confidence: number;
  quantity: number;
  price: number;
  fees: number;
  /** Date of execution */
  execution_time: string;
  execution_unix: number;
  status: string;
};

export type DbTypes = {
  btc_historical: PriceData;
  report_card: DbReportCard;
  bot_executions: DbResult;
};
