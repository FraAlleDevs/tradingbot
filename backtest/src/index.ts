import { getMeanReversionEstimate } from './algorithms/meanReversion.js';
import { getMeanReversionVolumeCompensatedEstimate } from './algorithms/meanReversionVolumeCompensated.js';
import { getMovingAverageEstimate } from './algorithms/movingAverage.js';
import { getMovingAverageVolumeCompensatedEstimate } from './algorithms/movingAverageVolumeCompensated.js';
import { backtest } from './simulation/backtest.js';
import { storeResults } from './database/resultWriter.js';
import { settings } from './utils/settings.js';

const tradeResults = await backtest(
  settings.startDate,
  settings.endDate,
  settings.marginDays,
  settings.tradeDollarMaxAmount,
  {
    hold: (dataEntries, date) => ({ signal: 'hold', confidence: 1 }),
    movingAverage: (dataEntries, date) =>
      getMovingAverageEstimate(
        dataEntries,
        date,
        settings.movingAveragelongTermDays,
        settings.movingAverageShortTermDays,
      ),
    movingAverageVolumeCompensated: (dataEntries, date) =>
      getMovingAverageVolumeCompensatedEstimate(
        dataEntries,
        date,
        settings.movingAveragelongTermDays,
        settings.movingAverageShortTermDays,
      ),
    meanReversion: (dataEntries, date) =>
      getMeanReversionEstimate(
        dataEntries,
        date,
        settings.meanReversionScopeDays,
      ),
    meanReversionVolumeCompensated: (dataEntries, date) =>
      getMeanReversionVolumeCompensatedEstimate(
        dataEntries,
        date,
        settings.meanReversionScopeDays,
      ),
  },
);

const finalTradeResult = tradeResults[tradeResults.length - 1];

const algorithmNames = Object.keys(finalTradeResult.results);

console.log('Trading results:');
for (const algorithmName of algorithmNames) {
  console.log(
    `  ${algorithmName}: ${(
      finalTradeResult.results[algorithmName].valuationDifference * 100
    ).toFixed(2)}%`,
  );
}
console.log();

storeResults(settings.startDate, settings.endDate, tradeResults);

console.table(
  tradeResults.map((tradeResult) => ({
    date: tradeResult.date,
    closePrice: tradeResult.closePrice,
    volume: tradeResult.volume,
    ...Object.entries(tradeResult.results).reduce(
      (acc, [algorithm, result]) => ({
        ...acc,
        [`${algorithm}-estimate`]: result.estimate,
        [`${algorithm}-assets`]: result.assets,
        [`${algorithm}-valuation`]: result.valuation,
        [`${algorithm}-valuationDifference`]: `${(
          result.valuationDifference * 100
        ).toFixed(2)}%`,
      }),
      {},
    ),
  })),
);
