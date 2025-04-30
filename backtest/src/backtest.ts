import { getLocalRangeData } from './csvParser.js';
import { getDataFilterFromDateToDate } from './dateUtils.js';
import { PriceData, Signal } from './types.js';

type Assets = {
  dollar: number;
  bitcoin: number;
};

function calculateValuation(assets: Assets, dataEntry: PriceData, date: Date) {
  const valuation = Number(
    (assets.dollar + assets.bitcoin * dataEntry.close).toFixed(),
  );

  return valuation;
}

function calculateNewAssets(
  assets: Assets,
  priceData: PriceData,
  signal: Signal,
  tradeDollarAmount: number,
): Assets {
  if (signal === 'buy') {
    return {
      dollar: assets.dollar - tradeDollarAmount,
      bitcoin: assets.bitcoin + tradeDollarAmount / priceData.close,
    };
  }

  if (signal === 'sell') {
    return {
      dollar: assets.dollar + tradeDollarAmount,
      bitcoin: assets.bitcoin - tradeDollarAmount / priceData.close,
    };
  }

  return { ...assets };
}

export async function backtest(
  fromDate: Date,
  toDate: Date,
  tradeDollarAmount: number,
  algorithm: (dataEntries: PriceData[], date: Date) => Signal,
) {
  const localData = await getLocalRangeData(fromDate, toDate);

  const tradingDates = localData
    .filter(getDataFilterFromDateToDate(fromDate, toDate))
    .map((entry) => ({ date: new Date(entry.timestamp * 1_000), entry }));

  console.log('Executing algorithm on all entries...');

  const timeAlgorithmStart = new Date();

  const trades = tradingDates.map(({ date, entry }) => ({
    date,
    entry,
    signal: algorithm(localData, date),
  }));

  const timeAlgorithmEnd = new Date();

  const algorithmDurationMS =
    timeAlgorithmEnd.getTime() - timeAlgorithmStart.getTime();

  console.log(
    `Algorithm ran (${(algorithmDurationMS / 1_000 / 60).toFixed()} m ${
      (algorithmDurationMS / 1_000) % 60
    } s)`,
  );

  const initialAssets: Assets = {
    dollar: 1_000,
    bitcoin: 1_000,
  };

  let assets = {
    ...initialAssets,
  };

  const states: {
    date: Date;
    signal: Signal;
    closePrice: number;
    assets: Assets;
    valuation: number;
    valuationDifference: number;
    marketDifference: number;
  }[] = [];

  console.log('Calculating trade results...');

  const timeTradesStart = new Date();

  const initialClosePrice = trades[0].entry.close;

  const initialValuation = calculateValuation(
    assets,
    trades[0].entry,
    trades[0].date,
  );

  states.push({
    date: trades[0].date,
    signal: 'hold',
    closePrice: trades[0].entry.close,
    assets: { ...assets },
    valuation: initialValuation,
    valuationDifference: 0,
    marketDifference: 0,
  });

  for (const { date, entry, signal } of trades) {
    assets = calculateNewAssets(assets, entry, signal, tradeDollarAmount);

    const valuation = calculateValuation(assets, entry, date);

    states.push({
      date,
      signal,
      closePrice: entry.close,
      assets: { ...assets },
      valuation,
      valuationDifference: Number(
        (((valuation - initialValuation) / initialValuation) * 100).toFixed(2),
      ),
      marketDifference: Number(
        (((entry.close - initialClosePrice) / initialClosePrice) * 100).toFixed(
          2,
        ),
      ),
    });
  }

  const timeTradesEnd = new Date();

  const tradesDurationMS =
    (timeTradesEnd.getTime() - timeTradesStart.getTime()) / 1_000;

  console.log(`Trades results calculated (${tradesDurationMS} s)`);

  return states;
}
