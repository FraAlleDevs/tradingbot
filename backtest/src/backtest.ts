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

  const trades = tradingMoments.map(
    ({ date, entry }): Trade<Name> => ({
      date,
      entry,
      estimates: (Object.entries(algorithms) as [Name, Algorithm][]).reduce(
        (acc, [name, algorithm]) => {
          acc[name] = algorithm(localData, date);

          return acc;
        },
        {} as Record<Name, Estimate>,
      ),
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
  console.log();

  return trades;
}

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
    acc[name] =
      (
        ((newValuations[name] - initialValuation) / initialValuation) *
        100
      ).toFixed(2) + '%';

    return acc;
  }, {} as Record<Name, string>);

  const tradeResultStep = {
    date: trade.date,
    closePrice: trade.entry.close,
    ...algorithmNames.reduce((acc, name) => {
      acc[name + '-estimate'] = trade.estimates[name];
      acc[name + '-assets'] = newAssets[name];
      acc[name + '-valuation'] = newValuations[name];
      acc[name + '-valuationDifference'] = valuationDifferences[name];

      return acc;
    }, {} as Record<string, any>),
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

  const tradeResults: any[] = [];

  let assets = algorithmNames.reduce((acc, name) => {
    acc[name] = { ...initialAssets };

    return acc;
  }, {} as Record<Name, Assets>);

  // Initial state (just for reference when analyzing)
  tradeResults.push({
    date: trades[0].date,
    closePrice: trades[0].entry.close,
    volume: trades[0].entry.volume,
    ...algorithmNames.reduce((acc, name) => {
      acc[name + '-estimate'] = { signal: 'hold', confidence: 1 };
      acc[name + '-assets'] = assets[name];
      acc[name + '-valuation'] = initialValuation;
      acc[name + '-valuationDifference'] = '0.00%';

      return acc;
    }, {} as Record<string, any>),
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
  // Load data from CSV for specific date range
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
