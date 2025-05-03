import { getDataFilterFromDateToDate } from '../dateUtils.js';
import { PriceData } from '../types.js';

/** Calculates the average close price for the given range */
export function getAverage(dataEntries: PriceData[]) {
  const closeValues = dataEntries.map(({ close }) => close);

  const averageClose =
    closeValues.reduce((acc, cur) => acc + cur, 0) / closeValues.length;

  return averageClose;
}

/** Filters data entries based on the date */
export function getDataFromDateToDate(
  dataEntries: PriceData[],
  fromDate: Date,
  toDate: Date,
) {
  return dataEntries.filter(getDataFilterFromDateToDate(fromDate, toDate));
}
