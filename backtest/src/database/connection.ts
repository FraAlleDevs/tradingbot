import { Client } from 'pg';

// TODO: adjust db config
const client = new Client({
  user: 'database-user',
  password: 'secretpassword!!',
  host: 'my.database-server.com',
  port: 5334,
  database: 'database-name',
});

await client.connect();

// TODO: adjust query
const res = await client.query('SELECT * from YOUR_MUM');

console.log(res.rows); // Hello world!

await client.end();
