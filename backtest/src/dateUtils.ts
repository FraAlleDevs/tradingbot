import { PriceData } from './types.js';

export function getDataFilterFromDateToDate(fromDate: Date, toDate: Date) {
  const fromDateTimestamp = fromDate.getTime();

  const toDateTimestamp = toDate.getTime();

  return (entry: PriceData) => {
    try {
      const timestamp = entry.timestamp;

      const isBetweenFromAndTo =
        fromDateTimestamp <= timestamp && timestamp <= toDateTimestamp;

      return isBetweenFromAndTo;
    } catch (error) {
      console.log('Error filtering by date', entry, fromDate, toDate);

      return false;
    }
  };
}

export function getDateAfterDays(referenceDate: Date, daysCount: number) {
  return new Date(referenceDate.getTime() + daysCount * 24 * 60 * 60 * 1_000);
}
