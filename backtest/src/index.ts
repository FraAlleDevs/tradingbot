import { getMeanReversionEstimate } from './algorithms/meanReversion.js';
import { getMeanReversionVolumeCompensatedEstimate } from './algorithms/meanReversionVolumeCompensated.js';
import { getMovingAverageEstimate } from './algorithms/movingAverage.js';
import { getMovingAverageVolumeCompensatedEstimate } from './algorithms/movingAverageVolumeCompensated.js';
import { backtest } from './backtest.js';
import { storeResults } from './database/resultWriter.js';
//TODO: Make it environment variables
const startDate = new Date('2020-01-01');
const endDate = new Date('2020-01-02');
const marginDays = 2;
const movingAveragelongTermDays = 0.1;
const movingAverageShortTermDays = 0.025;
const meanReversionScopeDays = 1;
const tradeDollarMaxAmount = 100_000;

console.log('Start date: ' + startDate.toISOString().split('T')[0]);
console.log('End date: ' + endDate.toISOString().split('T')[0]);
console.log(
  'Moving average long term average length: ' +
    movingAveragelongTermDays +
    ' days',
);
console.log(
  'Moving average short term average length: ' +
    movingAverageShortTermDays +
    ' days',
);
console.log('Mean reversion scope length: ' + meanReversionScopeDays + ' days');
console.log(
  'Maximum traded amount on every signal: ' + tradeDollarMaxAmount + ' $',
);
console.log();

const tradeResults = await backtest(
  startDate,
  endDate,
  marginDays,
  tradeDollarMaxAmount,
  {
    hold: (dataEntries, date) => ({ signal: 'hold', confidence: 1 }),
    movingAverage: (dataEntries, date) =>
      getMovingAverageEstimate(
        dataEntries,
        date,
        movingAveragelongTermDays,
        movingAverageShortTermDays,
      ),
    movingAverageVolumeCompensated: (dataEntries, date) =>
      getMovingAverageVolumeCompensatedEstimate(
        dataEntries,
        date,
        movingAveragelongTermDays,
        movingAverageShortTermDays,
      ),
    meanReversion: (dataEntries, date) =>
      getMeanReversionEstimate(dataEntries, date, meanReversionScopeDays),
    meanReversionVolumeCompensated: (dataEntries, date) =>
      getMeanReversionVolumeCompensatedEstimate(
        dataEntries,
        date,
        meanReversionScopeDays,
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

storeResults(startDate, endDate, tradeResults);

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
