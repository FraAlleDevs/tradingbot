CREATE TABLE IF NOT EXISTS btc_historical (
  timestamp DOUBLE PRECISION NOT NULL,
  open REAL NOT NULL,
  high REAL NOT NULL,
  low REAL NOT NULL,
  close REAL NOT NULL,
  volume REAL NOT NULL,
  PRIMARY KEY(timestamp)
);

CREATE TABLE IF NOT EXISTS report_card (
  id SMALLSERIAL NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  algorithm_version VARCHAR(50) NOT NULL,
  start_date TIMESTAMP NOT NULL,
  end_date TIMESTAMP NOT NULL,
  performance REAL NOT NULL,
  PRIMARY KEY(id)
);

CREATE TABLE IF NOT EXISTS bot_executions (
  id BIGSERIAL NOT NULL,
  report_card_id SMALLINT,
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
  CONSTRAINT chk_status CHECK (status IN ('SUCCESS', 'ERROR', 'SKIPPED'))
);

COPY btc_historical FROM '/docker-entrypoint-initdb.d/btcusd_1-min_data.csv' DELIMITER ',' CSV HEADER;

-- Drop table if exists (for clean setup)
DROP TABLE IF EXISTS ohlcv_data CASCADE;

-- Main OHLCV table with all Binance API fields
CREATE TABLE ohlcv_data (
    -- Primary identifiers
    symbol VARCHAR(20) NOT NULL,                    -- e.g., 'BTCUSDT', 'ETHUSDT'
    timeframe VARCHAR(10) NOT NULL,                 -- e.g., '1m', '5m', '15m', '1h', '1d'
    open_time BIGINT NOT NULL,                      -- Kline open time (timestamp in ms)
    
    -- OHLCV core data (using DECIMAL for precision)
    open_price DECIMAL(20, 8) NOT NULL,            -- Open price
    high_price DECIMAL(20, 8) NOT NULL,            -- High price  
    low_price DECIMAL(20, 8) NOT NULL,             -- Low price
    close_price DECIMAL(20, 8) NOT NULL,           -- Close price
    volume DECIMAL(20, 8) NOT NULL,                -- Volume (base asset)
    
    -- Additional Binance fields
    close_time BIGINT NOT NULL,                     -- Kline close time (timestamp in ms)
    quote_volume DECIMAL(25, 8) NOT NULL,          -- Quote asset volume (USDT volume)
    trades_count INTEGER NOT NULL,                 -- Number of trades
    taker_buy_base_volume DECIMAL(20, 8) NOT NULL, -- Taker buy base asset volume
    taker_buy_quote_volume DECIMAL(25, 8) NOT NULL,-- Taker buy quote asset volume
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Primary key (composite)
    PRIMARY KEY (symbol, timeframe, open_time),
    
    -- Constraints
    CONSTRAINT chk_timeframe CHECK (timeframe IN ('1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M')),
    CONSTRAINT chk_prices_positive CHECK (
        open_price > 0 AND 
        high_price > 0 AND 
        low_price > 0 AND 
        close_price > 0 AND
        volume >= 0
    ),
    CONSTRAINT chk_high_low CHECK (high_price >= low_price),
    CONSTRAINT chk_ohlc_logic CHECK (
        high_price >= open_price AND 
        high_price >= close_price AND
        low_price <= open_price AND 
        low_price <= close_price
    )
);