CREATE TABLE IF NOT EXISTS btc_historical (
  timestamp DOUBLE PRECISION NOT NULL,
  open REAL NOT NULL,
  high REAL NOT NULL,
  low REAL NOT NULL,
  close REAL NOT NULL,
  volume REAL NOT NULL,
  PRIMARY KEY(timestamp)
);

COPY btc_historical FROM '/docker-entrypoint-initdb.d/btcusd_1-min_data.csv' DELIMITER ',' CSV HEADER;
-- this is how you comment in sql file. 
