import { getGuessForMomentum } from './algorithm.js';
import { backtest } from './backtest.js';

const longTermDays = 0.1;
const shortTermDays = 0.025;
const tradeDollarAmount = 100;
const startDate = new Date('2022-01-01');
const endDate = new Date('2022-02-01');

console.log('Algorithm: Momentum trading');
console.log('Start date: ' + startDate.toISOString().split('T')[0]);
console.log('End date: ' + endDate.toISOString().split('T')[0]);
console.log('Long term average length: ' + longTermDays + ' days');
console.log('Short term average length: ' + shortTermDays + ' days');
console.log('Traded amount on every signal: ' + tradeDollarAmount + ' $');
console.log();

const tradeResults = await backtest(
  startDate,
  endDate,
  tradeDollarAmount,
  (dataEntries, date) =>
    getGuessForMomentum(dataEntries, date, longTermDays, shortTermDays),
);

console.table(tradeResults);
