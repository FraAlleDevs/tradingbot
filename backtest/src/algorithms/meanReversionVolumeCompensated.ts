import { getDateAfterDays } from '../dateUtils.js';
import { Estimate, PriceData, Signal } from '../types.js';
import {
  getAveragePrice,
  getAverageVolume,
  getDataFromDateToDate,
} from './utils.js';

/** ### Mean Reversion
 * - How it works: Assumes prices tend to return to a historical average.
 * - Example: If price dips significantly below a 20-day average, buy expecting a bounce back.
 * - Risk: Doesn’t work well in strong trends.
 */
export function getMeanReversionVolumeCompensatedEstimate(
  dataEntries: PriceData[],
  date: Date,
  scopeDays: number,
): Estimate {
  const scopeStartDate = getDateAfterDays(date, -scopeDays);

  const scopeDataEntries = getDataFromDateToDate(
    dataEntries,
    scopeStartDate,
    date,
  );

  const scopeAveragePrice = getAveragePrice(scopeDataEntries);

  const scopeAverageVolume = getAverageVolume(scopeDataEntries);

  const lastEntry = scopeDataEntries[scopeDataEntries.length - 1];

  const lastPrice = lastEntry.close;

  const lastVolume = lastEntry.close;

  // If the volume is up by more than 10%, it's considered a spike.
  const isVolumeSpike =
    lastVolume - scopeAverageVolume > scopeAverageVolume * 0.1;

  const signal: Signal = isVolumeSpike
    ? 'hold'
    : lastPrice < scopeAveragePrice
    ? 'buy'
    : 'sell';

  // If the price changes more than 5%, it's a strong change
  const confidence = Math.min(
    1,
    (Math.abs(lastPrice - scopeAveragePrice) / scopeAveragePrice) * (1 / 0.05),
  );

  return { signal, confidence };
}
