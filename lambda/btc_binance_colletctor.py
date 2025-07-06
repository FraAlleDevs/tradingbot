#!/usr/bin/env python3
"""
Full Binance Data Collector
Uses direct API calls to get complete klines data including quote_volume, trades_count, etc.
"""

import logging
import os
from datetime import datetime
from decimal import Decimal

import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FullBinanceCollector:
    def __init__(self):
        # Use testnet for sandbox mode
        self.base_url = "https://testnet.binance.vision" if os.getenv('BINANCE_SANDBOX', 'true').lower() == 'true' else "https://api.binance.com"
        
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT')),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        self.symbol = os.getenv('SYMBOL', 'BTCUSDT')
        logger.info(f"Initialized collector for {self.symbol} using {self.base_url}")
    
    def get_db_connection(self):
        return psycopg2.connect(**self.db_config)
    
    def fetch_full_klines(self, symbol, interval='1m', limit=2):
        """
        Fetch complete klines data directly from Binance API
        Returns all 12 fields including quote_volume, trades_count, etc.
        """
        try:
            url = f"{self.base_url}/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            klines = response.json()
            
            if not klines or len(klines) < 2:
                logger.warning(f"Insufficient data received for {symbol}")
                return None
            
            # Return the second-to-last kline (last complete one)
            return klines[-2]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {symbol}: {e}")
            return None
    
    def convert_kline_to_record(self, kline, symbol, timeframe):
        """
        Convert full Binance kline (12 values) to database record
        """
        try:
            # Full Binance kline format:
            # [open_time, open, high, low, close, volume, close_time, quote_volume, 
            #  trades_count, taker_buy_base_volume, taker_buy_quote_volume, unused]
            
            record = (
                symbol,                          # symbol
                timeframe,                       # timeframe
                int(kline[0]),                  # open_time
                Decimal(str(kline[1])),         # open_price
                Decimal(str(kline[2])),         # high_price
                Decimal(str(kline[3])),         # low_price
                Decimal(str(kline[4])),         # close_price
                Decimal(str(kline[5])),         # volume (base asset)
                int(kline[6]),                  # close_time
                Decimal(str(kline[7])),         # quote_volume (USDT volume)
                int(kline[8]),                  # trades_count
                Decimal(str(kline[9])),         # taker_buy_base_volume
                Decimal(str(kline[10])),        # taker_buy_quote_volume
            )
            
            return record
            
        except (ValueError, TypeError, IndexError) as e:
            logger.error(f"Error converting kline data for {symbol}: {e}")
            return None
    
    def store_kline_data(self, record):
        """Store single kline record in database"""
        insert_query = """
        INSERT INTO ohlcv_data (
            symbol, timeframe, open_time, open_price, high_price, 
            low_price, close_price, volume, close_time, quote_volume,
            trades_count, taker_buy_base_volume, taker_buy_quote_volume
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol, timeframe, open_time) 
        DO UPDATE SET
            open_price = EXCLUDED.open_price,
            high_price = EXCLUDED.high_price,
            low_price = EXCLUDED.low_price,
            close_price = EXCLUDED.close_price,
            volume = EXCLUDED.volume,
            close_time = EXCLUDED.close_time,
            quote_volume = EXCLUDED.quote_volume,
            trades_count = EXCLUDED.trades_count,
            taker_buy_base_volume = EXCLUDED.taker_buy_base_volume,
            taker_buy_quote_volume = EXCLUDED.taker_buy_quote_volume,
            updated_at = NOW()
        """
        
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(insert_query, record)
                    conn.commit()
                    
                    # Log the stored data with full details
                    timestamp = datetime.fromtimestamp(record[2] / 1000)  # open_time
                    logger.info(f"Stored: {timestamp} - Close: ${record[6]}, Volume: {record[7]} BTC, "
                              f"Quote Volume: ${record[9]:,.2f} USDT, Trades: {record[10]}")
                    return True
                    
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error storing data: {e}")
            return False
    
    def collect_btc_data(self):
        """Collect complete BTC/USDT data with all fields"""
        logger.info("Fetching complete BTC/USDT kline data...")
        
        # Fetch full klines data
        kline = self.fetch_full_klines(self.symbol, '1m', 2)
        
        if kline:
            # Convert to database record
            record = self.convert_kline_to_record(kline, self.symbol, '1m')
            
            if record:
                success = self.store_kline_data(record)
                if success:
                    logger.info("BTC data collection completed successfully")
                    return True
                else:
                    logger.error("Failed to store BTC data")
                    return False
            else:
                logger.error("Failed to convert kline data")
                return False
        else:
            logger.error("Failed to fetch BTC kline data")
            return False
    
def main():
    """Main function for cron execution - collects only 1-minute data"""
    try:
        collector = FullBinanceCollector()
        
        # Collect only 1-minute data
        success = collector.collect_btc_data()
        
        if success:
            logger.info("1-minute data collection completed successfully")
            exit(0)
        else:
            logger.error("1-minute data collection failed")
            exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main()