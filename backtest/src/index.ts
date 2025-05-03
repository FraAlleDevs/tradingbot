import { getMovingAverageEstimate } from './algorithms/movingAverage.js';
import { backtest } from './backtest.js';

const startDate = new Date('2022-01-01');
const endDate = new Date('2022-02-01');
const marginDays = 2;
const longTermDays = 0.1;
const shortTermDays = 0.025;
const tradeDollarMaxAmount = 100_000;

console.log('Algorithm: Moving average');
console.log('Start date: ' + startDate.toISOString().split('T')[0]);
console.log('End date: ' + endDate.toISOString().split('T')[0]);
console.log('Long term average length: ' + longTermDays + ' days');
console.log('Short term average length: ' + shortTermDays + ' days');
console.log(
  'Maximum traded amount on every signal: ' + tradeDollarMaxAmount + ' $',
);
console.log();

const tradeResults = await backtest(
  startDate,
  endDate,
  marginDays,
  tradeDollarMaxAmount,
  (dataEntries, date) =>
    getMovingAverageEstimate(dataEntries, date, longTermDays, shortTermDays),
);

const finalTradeResult = tradeResults[tradeResults.length - 1];

console.log('Trading results:');
console.log(`  Bot: ${finalTradeResult.valuationDifference} %`);
console.log(`  Market: ${finalTradeResult.marketDifference} %`);
console.log();

console.table(tradeResults);
