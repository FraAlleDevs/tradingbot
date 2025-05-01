import { getLocalRangeData } from './csvParser.js';
import { getDataFilterFromDateToDate } from './dateUtils.js';
import { Estimate, PriceData, Signal } from './types.js';

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

function convertDollarsToBitcoin(priceData: PriceData, dollars: number) {
  return dollars / priceData.close;
}

function convertBitcoinToDollars(priceData: PriceData, bitcoin: number) {
  return bitcoin * priceData.close;
}

function calculateNewAssets(
  assets: Assets,
  priceData: PriceData,
  estimate: Estimate,
  tradeDollarMaxAmount: number,
): Assets {
  if (estimate.signal === 'buy') {
    const maxDollarsAllowedToBuy = Math.min(
      tradeDollarMaxAmount,
      assets.dollar,
    );

    const tradeDollarAmount = maxDollarsAllowedToBuy * estimate.confidence;

    const newAssets = {
      dollar: assets.dollar - tradeDollarAmount,
      bitcoin:
        assets.bitcoin + convertDollarsToBitcoin(priceData, tradeDollarAmount),
    };

    return newAssets;
  }

  if (estimate.signal === 'sell') {
    const bitcoinAssetsValue = convertBitcoinToDollars(
      priceData,
      assets.bitcoin,
    );

    const maxDollarsAllowedToSell = Math.min(
      tradeDollarMaxAmount,
      bitcoinAssetsValue,
    );

    const tradeDollarAmount = maxDollarsAllowedToSell * estimate.confidence;

    const newAssets = {
      dollar: assets.dollar + tradeDollarAmount,
      bitcoin:
        assets.bitcoin - convertDollarsToBitcoin(priceData, tradeDollarAmount),
    };

    return newAssets;
  }

  return { ...assets };
}

export async function backtest(
  fromDate: Date,
  toDate: Date,
  tradeDollarMaxAmount: number,
  algorithm: (dataEntries: PriceData[], date: Date) => Estimate,
) {
  // Load data from CSV for specific date range (±200 days)
  const localData = await getLocalRangeData(fromDate, toDate);

  // Get a list of the moments the bot will trade on
  const tradingDates = localData
    .filter(getDataFilterFromDateToDate(fromDate, toDate))
    .map((entry) => ({ date: new Date(entry.timestamp * 1_000), entry }));

  console.log('Executing algorithm on all entries...');

  const timeAlgorithmStart = new Date();

  // Get the bot's estimate for each trading moment
  const trades = tradingDates.map(({ date, entry }) => ({
    date,
    entry,
    estimate: algorithm(localData, date),
  }));

  const timeAlgorithmEnd = new Date();

  const algorithmDurationMS =
    timeAlgorithmEnd.getTime() - timeAlgorithmStart.getTime();

  console.log(
    `Algorithm ran (${(algorithmDurationMS / 1_000 / 60).toFixed()} m ${
      (algorithmDurationMS / 1_000) % 60
    } s)`,
  );

  // This is the assets the bot will start trading with
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
    confidence: number;
    closePrice: number;
    assets: Assets;
    /** The bot's assets valuation in $ */
    valuation: number;
    /** The percentage difference of the bot's assets valuation in $ */
    valuationDifference: number;
    /** The percentage difference of the market's valuation in $ */
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

  // Initial value (just for reference when analyzing)
  states.push({
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

    states.push({
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

  return states;
}
