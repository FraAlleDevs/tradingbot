import { TradeResult } from '../backtest.js';
import { Signal } from '../types.js';
import { database } from './connection.js';
import { DbTypes } from './types.js';

function toDbTimestamp(date: Date) {
  return (
    date.toISOString().split('T')[0] +
    ' ' +
    date.getHours().toString().padStart(2, '0') +
    ':' +
    date.getMinutes().toString().padStart(2, '0')
  );
}

async function writeReportCard(reportCard: DbTypes['report_card']) {
  const response = await database.query(
    `INSERT INTO report_card (
            algorithm_version,
            start_date,
            end_date,
            performance
          ) 
          VALUES ($1, $2, $3, $4) RETURNING id`,
    [
      reportCard.algorithm_version,
      reportCard.start_date,
      reportCard.end_date,
      reportCard.performance,
    ],
  );

  return response.rows[0] as Required<DbTypes['report_card']>;
}

async function writeResults(results: DbTypes['bot_executions'][]) {
  const responses = await Promise.allSettled(
    results.map((result) =>
      database.query(
        `INSERT INTO bot_executions (
            report_card_id, 
            symbol, 
            signal, 
            confidence, 
            quantity, 
            price, 
            fees, 
            execution_time, 
            execution_unix, 
            status
          ) 
          VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
        [
          result.report_card_id,
          result.symbol,
          result.signal,
          result.confidence,
          result.quantity,
          result.price,
          result.fees,
          result.execution_time,
          result.execution_unix,
          result.status,
        ],
      ),
    ),
  );

  const fulfilledRequests = responses.filter(
    (res) => res.status === 'fulfilled',
  );

  console.log('Requests: ' + responses.length);
  console.log('  Fulfilled: ' + fulfilledRequests.length);
  console.log('  Failed: ' + (responses.length - fulfilledRequests.length));
  console.log();
}

export async function storeResults(
  fromDate: Date,
  toDate: Date,
  tradeResults: TradeResult<string>[],
) {
  console.log('Storing trade results...');
  console.log();

  const finalTradeResult = tradeResults[tradeResults.length - 1];

  const algorithmNames = Object.keys(finalTradeResult.results);

  for (const algorithmName of algorithmNames) {
    console.log(`Storing ${algorithmName}`);
    console.log(`  report_card...`);

    const report = await writeReportCard({
      algorithm_version: algorithmName,
      start_date: toDbTimestamp(fromDate),
      end_date: toDbTimestamp(toDate),
      performance:
        finalTradeResult.results[algorithmName].valuationDifference * 100,
    });

    console.log(`  report_card id: ${report.id}`);

    console.log(`  bot_executions...`);

    const results = tradeResults.map(
      (tradeResult): DbTypes['bot_executions'] => ({
        report_card_id: report.id,
        symbol: 'BTC/USDT',
        signal: tradeResult.results[
          algorithmName
        ].estimate.signal.toUpperCase() as Uppercase<Signal>,
        confidence: tradeResult.results[algorithmName].estimate.confidence,
        quantity: 0,
        price: 0,
        fees: 0,
        /** Date of execution */
        execution_time: toDbTimestamp(new Date()),
        execution_unix: 0,
        status: 'SUCCESS',
      }),
    );

    await writeResults(results);

    console.log();
  }
}
