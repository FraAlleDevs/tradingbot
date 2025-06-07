import { getDateAfterDays } from '../utils/dateUtils.js';
import { PriceData } from '../utils/types.js';
import { database } from './connection.js';
import { DbTypes } from './types.js';

async function getDataEntries(fromDate: Date, toDate: Date) {
  const fromTimestamp = fromDate.getTime() / 1_000;

  const toTimestamp = toDate.getTime() / 1_000;

  const response = await database.query(
    'SELECT * from btc_historical WHERE $1 <= timestamp AND timestamp <= $2',
    [fromTimestamp, toTimestamp],
  );

  return response.rows.map(
    (row: DbTypes['btc_historical']): PriceData => ({
      ...row,
      timestamp: row.timestamp * 1_000,
    }),
  );
}

export async function getLocalRangeData(
  startDate: Date,
  endDate: Date,
  marginDays: number,
) {
  console.log('Fetching data from the database...');

  const timeStart = new Date();

  const localData = await getDataEntries(
    getDateAfterDays(startDate, -marginDays),
    getDateAfterDays(endDate, +marginDays),
  );

  const timeDbEnd = new Date();

  const dbParsingDurationMS = timeDbEnd.getTime() - timeStart.getTime();

  console.log(
    `Data received (${dbParsingDurationMS / 1_000} s): ${
      localData.length
    } rows`,
  );
  console.log();

  return localData;
}
