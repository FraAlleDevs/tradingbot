import { Assets, calculateNewAssets, calculateValuation } from './assets.js';
import { getLocalRangeData } from './csvParser.js';
import { getDataFilterFromDateToDate } from './dateUtils.js';
import { Estimate, PriceData, Signal } from './types.js';

export type Algorithm = (dataEntries: PriceData[], date: Date) => Estimate;

type TradingDate = {
  date: Date;
  entry: PriceData;
};

/** Returns the list of trade moments in the specified range */
function getTradingMoments(
  localData: PriceData[],
  fromDate: Date,
  toDate: Date,
) {
  return localData.filter(getDataFilterFromDateToDate(fromDate, toDate)).map(
    (entry): TradingDate => ({
      date: new Date(entry.timestamp * 1_000),
      entry,
    }),
  );
}

type Trade = TradingDate & {
  estimate: Estimate;
};

/** Runs the specified algorithm on the given trading moments */
function getTrades(
  localData: PriceData[],
  tradingMoments: TradingDate[],
  algorithm: Algorithm,
) {
  console.log('Executing algorithm on all entries...');

  const timeAlgorithmStart = new Date();

  const trades = tradingMoments.map(
    ({ date, entry }): Trade => ({
      date,
      entry,
      estimate: algorithm(localData, date),
    }),
  );

  const timeAlgorithmEnd = new Date();

  const algorithmDurationMS =
    timeAlgorithmEnd.getTime() - timeAlgorithmStart.getTime();

  console.log(
    `Algorithm ran (${(algorithmDurationMS / 1_000 / 60).toFixed()} m ${
      (algorithmDurationMS / 1_000) % 60
    } s)`,
  );

  return trades;
}

type TradeResult = {
  date: Date;
  signal: Signal;
  confidence: number;
  closePrice: number;
  assets: Assets;
  /** The bot's assets valuation in $ */
  valuation: number;
  /** The percentage difference of the bot's assets valuation in $ */
  valuationDifference: number;
  /** The percentage difference of the market's valuation in $ */
  marketDifference: number;
};

function getTradeResults(
  tradeDollarMaxAmount: number,
  initialAssets: Assets,
  trades: Trade[],
) {
  let assets = {
    ...initialAssets,
  };

  const tradeResults: TradeResult[] = [];

  console.log('Calculating trade results...');

  const timeTradesStart = new Date();

  const initialClosePrice = trades[0].entry.close;

  const initialValuation = calculateValuation(
    assets,
    trades[0].entry,
    trades[0].date,
  );

  // Initial state (just for reference when analyzing)
  tradeResults.push({
    date: trades[0].date,
    signal: 'hold',
    confidence: 1,
    closePrice: trades[0].entry.close,
    assets: { ...assets },
    valuation: initialValuation,
    valuationDifference: 0,
    marketDifference: 0,
  });

  // Recalculate the assets and valuation of the bot after every trade
  for (const { date, entry, estimate } of trades) {
    assets = calculateNewAssets(assets, entry, estimate, tradeDollarMaxAmount);

    const valuation = calculateValuation(assets, entry, date);

    const valuationDifference = Number(
      (((valuation - initialValuation) / initialValuation) * 100).toFixed(2),
    );

    const marketDifference = Number(
      (((entry.close - initialClosePrice) / initialClosePrice) * 100).toFixed(
        2,
      ),
    );

    tradeResults.push({
      date,
      signal: estimate.signal,
      confidence: estimate.confidence,
      closePrice: entry.close,
      assets: { ...assets },
      valuation,
      valuationDifference,
      marketDifference,
    });
  }

  const timeTradesEnd = new Date();

  const tradesDurationMS =
    (timeTradesEnd.getTime() - timeTradesStart.getTime()) / 1_000;

  console.log(`Trades results calculated (${tradesDurationMS} s)`);

  return tradeResults;
}

export async function backtest(
  fromDate: Date,
  toDate: Date,
  tradeDollarMaxAmount: number,
  algorithm: Algorithm,
) {
  // Load data from CSV for specific date range (±200 days)
  const localData = await getLocalRangeData(fromDate, toDate);

  // Get a list of the moments the bot will trade on
  const tradingMoments = getTradingMoments(localData, fromDate, toDate);

  // Get the bot's estimate for each trading moment
  const trades = getTrades(localData, tradingMoments, algorithm);

  // This is the assets the bot will start trading with
  const initialAssets: Assets = {
    dollar: 1_000,
    bitcoin: 1_000,
  };

  // Simulate the trades and get the results
  const tradeResults = getTradeResults(
    tradeDollarMaxAmount,
    initialAssets,
    trades,
  );

  return tradeResults;
}
