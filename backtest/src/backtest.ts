import readline from 'readline';
import { Assets, calculateNewAssets, calculateValuation } from './assets.js';
import { getLocalRangeData } from './database/priceReader.js';
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
      date: new Date(entry.timestamp),
      entry,
    }),
  );
}

type Trade<Name extends string> = TradingDate & {
  estimates: Record<Name, Estimate>;
};

/** Runs the specified algorithm on the given trading moments */
function getTrades<Name extends string>(
  localData: PriceData[],
  tradingMoments: TradingDate[],
  algorithms: Record<string, Algorithm>,
) {
  console.log('Executing algorithm on all entries...');

  const timeAlgorithmStart = new Date();

  let calculatedTrades = 0;

  let lastProgressTrackElapsedTime = 10_000;

  function trackProgress() {
    const elapsedTime = new Date().getTime() - timeAlgorithmStart.getTime();

    if (elapsedTime > lastProgressTrackElapsedTime * 1.5) {
      lastProgressTrackElapsedTime = elapsedTime;

      const ETA = new Date(
        timeAlgorithmStart.getTime() +
          elapsedTime * (tradingMoments.length / calculatedTrades),
      );

      console.log(
        `(${Math.floor(elapsedTime / 1_000 / 60)} m ${Math.floor(
          (elapsedTime / 1_000) % 60,
        )} s) - ${calculatedTrades}/${tradingMoments.length} - ${Math.floor(
          (100 * calculatedTrades) / tradingMoments.length,
        )}% - expected to be done by: ${String(ETA.getHours()).padStart(
          2,
          '0',
        )}:${String(ETA.getMinutes()).padStart(2, '0')}`,
      );
    }
  }

  const trades = tradingMoments.map(({ date, entry }) => {
    const trade: Trade<Name> = {
      date,
      entry,
      estimates: (Object.entries(algorithms) as [Name, Algorithm][]).reduce(
        (acc, [name, algorithm]) => {
          acc[name] = algorithm(localData, date);

          return acc;
        },
        {} as Record<Name, Estimate>,
      ),
    };

    calculatedTrades++;

    trackProgress();

    return trade;
  });

  const timeAlgorithmEnd = new Date();

  const algorithmDurationMS =
    timeAlgorithmEnd.getTime() - timeAlgorithmStart.getTime();

  console.log(
    `Algorithm ran (${Math.floor(
      algorithmDurationMS / 1_000 / 60,
    )} m ${Math.floor((algorithmDurationMS / 1_000) % 60)} s)`,
  );
  console.log();

  return trades;
}

type AlgorithmTradeResult = {
  estimate: Estimate;
  assets: Assets;
  valuation: number;
  valuationDifference: number;
};

export type TradeResult<Name extends string> = {
  date: Date;
  closePrice: number;
  volume: number;
  results: Record<Name, AlgorithmTradeResult>;
};

function getTradeResultStep<Name extends string>(
  algorithmNames: Name[],
  tradeDollarMaxAmount: number,
  initialValuation: number,
  currentAssets: Record<Name, Assets>,
  trade: Trade<Name>,
) {
  const newAssets = algorithmNames.reduce((acc, name) => {
    acc[name] = calculateNewAssets(
      currentAssets[name],
      trade.entry,
      trade.estimates[name],
      tradeDollarMaxAmount,
    );

    return acc;
  }, {} as Record<Name, Assets>);

  const newValuations = algorithmNames.reduce((acc, name) => {
    acc[name] = calculateValuation(newAssets[name], trade.entry, trade.date);

    return acc;
  }, {} as Record<Name, number>);

  const valuationDifferences = algorithmNames.reduce((acc, name) => {
    acc[name] = (newValuations[name] - initialValuation) / initialValuation;

    return acc;
  }, {} as Record<Name, number>);

  const tradeResultStep: TradeResult<Name> = {
    date: trade.date,
    closePrice: trade.entry.close,
    volume: trade.entry.volume,
    results: algorithmNames.reduce((acc, name) => {
      acc[name] = {
        estimate: trade.estimates[name],
        assets: newAssets[name],
        valuation: newValuations[name],
        valuationDifference: valuationDifferences[name],
      } satisfies AlgorithmTradeResult;

      return acc;
    }, {} as Record<Name, AlgorithmTradeResult>),
  };

  return { tradeResultStep, newAssets };
}

function getTradeResults<Name extends string>(
  tradeDollarMaxAmount: number,
  initialAssets: Assets,
  trades: Trade<Name>[],
) {
  console.log('Calculating trade results...');

  const timeTradesStart = new Date();

  const algorithmNames = Object.keys(trades[0].estimates) as Name[];

  const initialClosePrice = trades[0].entry.close;

  const initialValuation = calculateValuation(
    initialAssets,
    trades[0].entry,
    trades[0].date,
  );

  const tradeResults: TradeResult<Name>[] = [];

  let assets = algorithmNames.reduce((acc, name) => {
    acc[name] = { ...initialAssets };

    return acc;
  }, {} as Record<Name, Assets>);

  // Initial state (just for reference when analyzing)
  tradeResults.push({
    date: trades[0].date,
    closePrice: trades[0].entry.close,
    volume: trades[0].entry.volume,
    results: algorithmNames.reduce(
      (acc, name) => ({
        ...acc,
        [name]: {
          estimate: { signal: 'hold', confidence: 1 },
          assets: assets[name],
          valuation: initialValuation,
          valuationDifference: 0,
        } satisfies AlgorithmTradeResult,
      }),
      {} as Record<Name, AlgorithmTradeResult>,
    ),
  });

  // Recalculate the assets and valuation of the bot after every trade
  for (const trade of trades) {
    const { tradeResultStep, newAssets } = getTradeResultStep(
      algorithmNames,
      tradeDollarMaxAmount,
      initialValuation,
      assets,
      trade,
    );

    tradeResults.push(tradeResultStep);

    assets = newAssets;
  }

  const timeTradesEnd = new Date();

  const tradesDurationMS =
    (timeTradesEnd.getTime() - timeTradesStart.getTime()) / 1_000;

  console.log(`Trades results calculated (${tradesDurationMS} s)`);
  console.log();

  return tradeResults;
}

export async function backtest<Name extends string>(
  fromDate: Date,
  toDate: Date,
  marginDays: number,
  tradeDollarMaxAmount: number,
  algorithms: Record<Name, Algorithm>,
) {
  // Load data from DB for specific date range
  const localData = await getLocalRangeData(fromDate, toDate, marginDays);

  // Get a list of the moments the bot will trade on
  const tradingMoments = getTradingMoments(localData, fromDate, toDate);

  // Get the bot's estimate for each trading moment
  const trades = getTrades(localData, tradingMoments, algorithms);

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
