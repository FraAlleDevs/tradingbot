import { getDateAfterDays } from '../dateUtils.js';
import { Estimate, PriceData, Signal } from '../types.js';
import { getAverage, getDataFromDateToDate } from './utils.js';

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

  const scopeAverage = getAverage(scopeDataEntries);

  const lastEntry = scopeDataEntries[scopeDataEntries.length - 1];

  const lastPrice = lastEntry.close;

  const signal: Signal = lastPrice < scopeAverage ? 'buy' : 'sell';

  const confidence = Math.min(
    1,
    Math.abs(lastPrice - scopeAverage) / scopeAverage / 10,
  );

  return { signal, confidence };
}
