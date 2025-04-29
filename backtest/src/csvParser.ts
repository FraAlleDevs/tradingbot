import fs from 'fs';
import { parse } from 'csv-parse';
import { PriceData } from './types.js';
import { getDataFilterFromDateToDate, getDateAfterDays } from './dateUtils.js';

function getDataStream() {
  return fs
    .createReadStream('./data/data.csv')
    .pipe(parse({ delimiter: ',', from_line: 1 }));
}

function getDataEntriesStream() {
  return getDataStream()
    .map((row): PriceData | undefined => {
      try {
        return {
          timestamp: parseInt(row[0]),
          open: parseFloat(row[1]),
          high: parseFloat(row[2]),
          low: parseFloat(row[3]),
          close: parseFloat(row[4]),
          volume: parseFloat(row[5]),
        };
      } catch (error) {
        console.log('CSV row not processed', row, error);
      }
    })
    .filter((entry): entry is NonNullable<typeof entry> => !!entry);
}

function getDataEntriesStreamFromDateToDate(fromDate: Date, toDate: Date) {
  return getDataEntriesStream().filter((entry) =>
    getDataFilterFromDateToDate(fromDate, toDate)(entry as PriceData),
  );
}

async function getDataEntriesFromDateToDate(fromDate: Date, toDate: Date) {
  const data: PriceData[] = [];

  await new Promise<void>((resolve, reject) => {
    getDataEntriesStreamFromDateToDate(fromDate, toDate)
      .on('data', (entry) => data.push(entry))
      .on('end', () => resolve());
  });

  return data;
}

export async function getLocalData(targetDate: Date) {
  console.log('Parsing CSV...');

  const timeStart = new Date();

  const localData = await getDataEntriesFromDateToDate(
    getDateAfterDays(targetDate, -200),
    getDateAfterDays(targetDate, +200),
  );

  const timeCSVEnd = new Date();

  const csvParsingDurationMS = timeCSVEnd.getTime() - timeStart.getTime();

  console.log(
    `CSV parsed (${csvParsingDurationMS / 1_000} s): ${localData.length} rows`,
  );

  return localData;
}

export async function getLocalRangeData(startDate: Date, endDate: Date) {
  console.log('Parsing CSV...');

  const timeStart = new Date();

  const localData = await getDataEntriesFromDateToDate(
    getDateAfterDays(startDate, -200),
    getDateAfterDays(endDate, +200),
  );

  const timeCSVEnd = new Date();

  const csvParsingDurationMS = timeCSVEnd.getTime() - timeStart.getTime();

  console.log(
    `CSV parsed (${csvParsingDurationMS / 1_000} s): ${localData.length} rows`,
  );

  return localData;
}
