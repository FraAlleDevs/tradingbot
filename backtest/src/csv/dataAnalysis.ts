import fs from 'node:fs';
import { getLocalRangeData } from './csvParser.js';
import {
  getDataFilterFromDateToDate,
  getDateAfterDays,
} from '../utils/dateUtils.js';

function toISODate(year: number, month: number, day: number) {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(
    2,
    '0',
  )}`;
}

function getDaysCountInMonth(year: number, month: number) {
  const date = new Date(toISODate(year, month, 1));

  let days = 0;

  while (date.getMonth() + 1 === month) {
    days++;

    date.setDate(date.getDate() + 1);
  }

  return days;
}

async function createDailyAnalysis(year: number) {
  const startDate = new Date(`${year}-01-01`);
  const endDate = new Date(`${year + 1}-01-01`);

  const months = new Array(12).fill(undefined).map((_, i) => i + 1);

  const days = months.flatMap((month) =>
    new Array(getDaysCountInMonth(year, month))
      .fill(undefined)
      .map((_, i) => ({ month, day: i + 1 })),
  );

  const localData = await getLocalRangeData(startDate, endDate, 0);

  console.log('Grouping data daily...');

  const dailyDataEntries = days.map(({ month, day }, i) => ({
    month,
    day,
    data: localData.filter(
      getDataFilterFromDateToDate(
        new Date(toISODate(year, month, day)),
        days[i + 1]
          ? new Date(toISODate(year, days[i + 1].month, days[i + 1].day))
          : getDateAfterDays(new Date(toISODate(year, month, day)), 1),
      ),
    ),
  }));

  console.log('Daily data grouped');
  console.log();

  console.log();

  console.log('Calculating daily data...');

  const dailyData = dailyDataEntries.map(({ month, day, data }) => ({
    timestamp: new Date(toISODate(year, month, day)).getTime(),
    year,
    month,
    day,
    data: data.length
      ? {
          open: data[0].open,
          close: data[data.length - 1].close,
          high: data.reduce(
            (acc, entry) => Math.max(acc, entry.high),
            data[0].high,
          ),
          low: data.reduce(
            (acc, entry) => Math.min(acc, entry.low),
            data[0].low,
          ),
          volume: data.reduce((acc, entry) => acc + entry.volume, 0),
        }
      : undefined,
  }));

  console.log('Daily data calculated');
  console.log();

  return dailyData;
}

async function createMonthlyAnalysis(year: number) {
  const startDate = new Date(`${year}-01-01`);
  const endDate = new Date(`${year + 1}-01-01`);

  const months = new Array(12).fill(undefined).map((_, i) => i + 1);

  const localData = await getLocalRangeData(startDate, endDate, 0);

  console.log('Grouping data monthly...');

  const monthlyDataEntries = months.map((month) => ({
    month,
    data: localData.filter(
      getDataFilterFromDateToDate(
        new Date(toISODate(year, month, 1)),
        new Date(toISODate(year, (month % 12) + 1, 1)),
      ),
    ),
  }));

  console.log('Monthly data grouped');
  console.log();

  console.log();

  console.log('Calculating monthly data...');

  const monthlyData = monthlyDataEntries.map(({ month, data }) => ({
    timestamp: new Date(toISODate(year, month, 1)).getTime(),
    year,
    month,
    data: data.length
      ? {
          open: data[0].open,
          close: data[data.length - 1].close,
          high: data.reduce(
            (acc, entry) => Math.max(acc, entry.high),
            data[0].high,
          ),
          low: data.reduce(
            (acc, entry) => Math.min(acc, entry.low),
            data[0].low,
          ),
          volume: data.reduce((acc, entry) => acc + entry.volume, 0),
        }
      : undefined,
  }));

  console.log('Monthly data calculated');
  console.log();

  return monthlyData;
}

async function createAndStoreDailyAnalysis() {
  console.log('DAILY ANALYSIS');
  console.log();

  for (const year of [
    2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023,
    2024, 2025,
  ]) {
    console.log('Year: ', year);
    console.log();

    const analysis = await createDailyAnalysis(year);

    const lines = analysis
      .filter(({ data }) => !!data)
      .map(
        ({ timestamp, data }) =>
          `${timestamp / 1_000}.0,${data?.open},${data?.high},${data?.low},${
            data?.close
          },${data?.volume}`,
      );

    const content = 'Timestamp,Open,High,Low,Close,Volume\n' + lines.join('\n');

    fs.writeFileSync(`./data/daily/${year}-daily.csv`, content, { flag: 'w' });
  }
}

async function createAndStoreMonthlyAnalysis() {
  console.log('MONTHLY ANALYSIS');
  console.log();

  for (const year of [
    2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023,
    2024, 2025,
  ]) {
    console.log('Year: ', year);
    console.log();

    const analysis = await createMonthlyAnalysis(year);

    const lines = analysis
      .filter(({ data }) => !!data)
      .map(
        ({ timestamp, data }) =>
          `${timestamp / 1_000}.0,${data?.open},${data?.high},${data?.low},${
            data?.close
          },${data?.volume}`,
      );

    const content = 'Timestamp,Open,High,Low,Close,Volume\n' + lines.join('\n');

    fs.writeFileSync(`./data/monthly/${year}-monthly.csv`, content, {
      flag: 'w',
    });
  }
}

await createAndStoreDailyAnalysis();

await createAndStoreMonthlyAnalysis();
