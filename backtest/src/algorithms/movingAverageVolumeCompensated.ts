import { getDataFilterFromDateToDate, getDateAfterDays } from '../dateUtils.js';
import { Estimate, PriceData, Signal } from '../types.js';
import {
  getAveragePrice,
  getAverageVolume,
  getDataFromDateToDate,
} from './utils.js';

/** ### Moving Average Crossover
 * - How it works: Track two moving averages (say, 50-day and 200-day). When the short-term crosses above the long-term, that's a buy signal (and vice versa).
 * - Why it’s used: Easy to implement, works well in trending markets.
 * - Tools: Just need historical price data.
 */
export function getMovingAverageVolumeCompensatedEstimate(
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

  const longTermAveragePrice = getAveragePrice(longTermDataEntries);

  const shortTermAveragePrice = getAveragePrice(shortTermDataEntries);

  const longTermAverageVolume = getAverageVolume(longTermDataEntries);

  const shortTermAverageVolume = getAverageVolume(shortTermDataEntries);

  // If the volume is up by more than 100%, it's considered a spike.
  const isVolumeSpike =
    shortTermAverageVolume - longTermAverageVolume > longTermAverageVolume * 1;

  const signal: Signal = isVolumeSpike
    ? shortTermAveragePrice > longTermAveragePrice
      ? 'buy'
      : 'sell'
    : 'hold';

  // If the price changes more than 5%, it's a strong change
  const confidence = Math.min(
    1,
    (Math.abs(shortTermAveragePrice - longTermAveragePrice) /
      longTermAveragePrice) *
      (1 / 0.05),
  );

  return { signal, confidence };
}
