CREATE TABLE IF NOT EXISTS btc_historical (
  timestamp DOUBLE PRECISION NOT NULL,
  open REAL NOT NULL,
  high REAL NOT NULL,
  low REAL NOT NULL,
  close REAL NOT NULL,
  volume REAL NOT NULL,
  PRIMARY KEY(timestamp)
);

CREATE TABLE IF NOT EXISTS report_card {
  id SMALLSERIAL NOT NULL GENERATED ALWAYS AS IDENTITY,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  algorithm_version VARCHAR(50) NOT NULL,
  start_date TIMESTAMP NOT NULL,
  end_date TIMESTAMP NOT NULL,
  performance REAL NOT NULL,
  PRIMARY KEY(id),
};

CREATE TABLE IF NOT EXISTS bot_executions {
  id BIGSERIAL GENERATED ALWAYS AS IDENTITY,
  report_card_id SMALLSERIAL,
  symbol VARCHAR(10) NOT NULL DEFAULT 'BTC/USDT',
  signal VARCHAR(5) NOT NULL,
  confidence REAL NOT NULL,
  quantity REAL NOT NULL,
  price REAL NOT NULL,
  fees REAL NOT NULL,
  execution_time TIMESTAMP NOT NULL,
  execution_unix DOUBLE PRECISION NOT NULL,
  status VARCHAR(20),
  PRIMARY KEY(id),
  CONSTRAINT fk_report FOREIGN KEY (report_card_id) REFERENCES report_card(id),
  CONSTRAINT chk_signal CHECK (signal IN ('BUY', 'SELL', 'HOLD')),
  CONSTRAINT chk_status CHECK (status IN ('SUCCESS', 'ERROR', 'SKIPPED')),
};



COPY btc_historical FROM '/docker-entrypoint-initdb.d/btcusd_1-min_data.csv' DELIMITER ',' CSV HEADER;
-- this is how you comment in sql file. 
