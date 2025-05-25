import { database } from './connection.js';
import { DbTypes } from './types.js';

async function writeResults(results: DbTypes['results'][]) {
  await database.connect();

  const responses = await Promise.allSettled(
    results.map((result) =>
      database.query(
        'INSERT INTO results (signal, confidence) VALUES ($1, $2)',
        [result.signal, result.confidence],
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

  await database.end();
}
