import { getDataFilterFromDateToDate, getDateAfterDays } from './dateUtils.js';
import { PriceData } from './types.js';

function getEntryAtDate(dataEntries: PriceData[], startDate: Date) {
  return dataEntries.filter(
    getDataFilterFromDateToDate(startDate, getDateAfterDays(startDate, 1)),
  )[0];
}

export function getPriceComparisons(dataEntries: PriceData[], startDate: Date) {
  const entryAtBet = getEntryAtDate(dataEntries, startDate);

  const daysOffsets = [1, 2, 3, 4, 5, 10, 15, 20, 25, 50, 100];

  const dateEntries = daysOffsets.map((daysOffset) => {
    const entry = getEntryAtDate(
      dataEntries,
      getDateAfterDays(startDate, daysOffset),
    );

    const priceDifference = entry.close - entryAtBet.close;

    const priceDifferencePercent = (priceDifference / entryAtBet.close) * 100;

    return {
      daysOffset,
      entry,
      priceDifference,
      priceDifferencePercent,
    };
  });

  return dateEntries;
}
