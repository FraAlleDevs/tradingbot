import { getDataFilterFromDateToDate, getDateAfterDays } from './dateUtils.js';
import { Estimate, PriceData } from './types.js';

/** Calculates the average close price for the given range */
function getAverage(dataEntries: PriceData[]) {
  const closeValues = dataEntries.map(({ close }) => close);

  const averageClose =
    closeValues.reduce((acc, cur) => acc + cur, 0) / closeValues.length;

  return averageClose;
}

/** Filters data entries based on the date */
function getDataFromDateToDate(
  dataEntries: PriceData[],
  fromDate: Date,
  toDate: Date,
) {
  return dataEntries.filter(getDataFilterFromDateToDate(fromDate, toDate));
}

/** Simple momentum trading algorithm */
export function getSimpleMomentumEstimate(
  dataEntries: PriceData[],
  date: Date,
  longTermDays: number,
  shortTermDays: number,
): Estimate {
  const longTermStartDate = getDateAfterDays(date, -longTermDays);

  const shortTermStartDate = getDateAfterDays(date, -shortTermDays);

  const longTermDataEntries = getDataFromDateToDate(
    dataEntries,
    longTermStartDate,
    date,
  );

  const shortTermDataEntries = getDataFromDateToDate(
    dataEntries,
    shortTermStartDate,
    date,
  );

  const longTermAverage = getAverage(longTermDataEntries);

  const shortTermAverage = getAverage(shortTermDataEntries);

  if (shortTermAverage > longTermAverage) {
    return { signal: 'buy', confidence: 1 };
  } else {
    return { signal: 'sell', confidence: 1 };
  }
}
