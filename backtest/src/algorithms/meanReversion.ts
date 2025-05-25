import { getDateAfterDays } from '../dateUtils.js';
import { Estimate, PriceData, Signal } from '../types.js';
import { getAveragePrice, getDataFromDateToDate } from './utils.js';

/** ### Mean Reversion
 * - How it works: Assumes prices tend to return to a historical average.
 * - Example: If price dips significantly below a 20-day average, buy expecting a bounce back.
 * - Risk: Doesn’t work well in strong trends.
 */
export function getMeanReversionEstimate(
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

  const lastEntry = scopeDataEntries[scopeDataEntries.length - 1];

  const lastPrice = lastEntry.close;

  const signal: Signal = lastPrice < scopeAveragePrice ? 'buy' : 'sell';

  // If the price changes more than 5%, it's a strong change
  const confidence = Math.min(
    1,
    (Math.abs(lastPrice - scopeAveragePrice) / scopeAveragePrice) * (1 / 0.05),
  );

  return { signal, confidence };
}
