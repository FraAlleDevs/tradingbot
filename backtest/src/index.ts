import { getGuessForMomentum } from './algorithm.js';
import { getPriceComparisons } from './priceComparator.js';
import { getLocalData } from './csvParser.js';
import { backtest } from './backtest.js';

// const targetDate = new Date('2022-02-01');

// const localData = await getLocalData(targetDate);

// const momentumGuess = getGuessForMomentum(localData, targetDate);

// console.log('The momentum algorithm says: ' + momentumGuess);

// const comparisons = getPriceComparisons(localData, targetDate);

// console.table(comparisons);

const longTermDays = 0.1;
const shortTermDays = 0.025;
const tradeDollarAmount = 100;
const startDate = new Date('2022-01-01');
const endDate = new Date('2022-02-01');

const tradeResults = await backtest(
  startDate,
  endDate,
  tradeDollarAmount,
  (dataEntries, date) =>
    getGuessForMomentum(dataEntries, date, longTermDays, shortTermDays),
);

console.table(tradeResults);
