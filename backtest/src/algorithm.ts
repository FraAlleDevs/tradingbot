import { getDataFilterFromDateToDate, getDateAfterDays } from './dateUtils.js';
import { PriceData, Signal } from './types.js';

function getAverage(dataEntries: PriceData[]) {
  const closeValues = dataEntries.map(({ close }) => close);

  const averageClose =
    closeValues.reduce((acc, cur) => acc + cur, 0) / closeValues.length;

  return averageClose;
}

function getDataFromDateToDate(
  dataEntries: PriceData[],
  fromDate: Date,
  toDate: Date,
) {
  return dataEntries.filter(getDataFilterFromDateToDate(fromDate, toDate));
}

export function getGuessForMomentum(
  dataEntries: PriceData[],
  date: Date,
  longTermDays: number,
  shortTermDays: number,
): Signal {
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
    return 'buy';
  } else {
    return 'sell';
  }
}
