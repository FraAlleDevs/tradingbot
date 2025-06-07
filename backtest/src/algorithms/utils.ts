import { getDataFilterFromDateToDate } from '../utils/dateUtils.js';
import { PriceData } from '../utils/types.js';

/** Calculates the average close price for the given range */
export function getAveragePrice(dataEntries: PriceData[]) {
  const closeValues = dataEntries.map(({ close }) => close);

  const averageClose =
    closeValues.reduce((acc, cur) => acc + cur, 0) / closeValues.length;

  return averageClose;
}

/** Calculates the average volume for the given range */
export function getAverageVolume(dataEntries: PriceData[]) {
  const volumes = dataEntries.map(({ volume }) => volume);

  const averageVolume =
    volumes.reduce((acc, cur) => acc + cur, 0) / volumes.length;

  return averageVolume;
}

/** Filters data entries based on the date */
export function getDataFromDateToDate(
  dataEntries: PriceData[],
  fromDate: Date,
  toDate: Date,
) {
  return dataEntries.filter(getDataFilterFromDateToDate(fromDate, toDate));
}
