import { Estimate, PriceData } from '../utils/types.js';

export type Assets = {
  dollar: number;
  bitcoin: number;
};

export function calculateValuation(
  assets: Assets,
  dataEntry: PriceData,
  date: Date,
) {
  const valuation = Math.floor(
    assets.dollar + assets.bitcoin * dataEntry.close,
  );

  return valuation;
}

function convertDollarsToBitcoin(priceData: PriceData, dollars: number) {
  return dollars / priceData.close;
}

function convertBitcoinToDollars(priceData: PriceData, bitcoin: number) {
  return bitcoin * priceData.close;
}

export function calculateNewAssets(
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
