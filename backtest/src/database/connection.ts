import { Client } from 'pg';

export const database = new Client({
  user: 'root',
  password: 'mypassword1234',
  host: 'localhost',
  port: 5432,
  database: 'bitcoin_db',
});
