import { getMeanReversionEstimate } from './algorithms/meanReversion.js';
import { getMovingAverageEstimate } from './algorithms/movingAverage.js';
import { backtest } from './backtest.js';

const startDate = new Date('2020-01-01');
const endDate = new Date('2022-01-01');
const marginDays = 2;
const movingAveragelongTermDays = 0.1;
const movingAverageShortTermDays = 0.025;
const meanReversionScopeDays = 1;
const tradeDollarMaxAmount = 100_000;

console.log('Algorithm: Moving average');
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
    meanReversion: (dataEntries, date) =>
      getMeanReversionEstimate(dataEntries, date, meanReversionScopeDays),
  },
);

const finalTradeResult = tradeResults[tradeResults.length - 1];

console.log('Trading results:');
Object.keys(finalTradeResult).forEach((key) => {
  const [name, field] = key.split('-');

  if (field === 'valuationDifference') {
    console.log(`  ${name}: ${finalTradeResult[key]}`);
  }
});
console.log();

console.table(tradeResults);
