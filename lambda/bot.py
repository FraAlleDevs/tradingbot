import os
import json
import boto3
import ccxt
import time
import uuid
import pandas as pd
from decimal import Decimal
import sys

# Check if running locally (either set in env or detected when running as script)
IS_LOCAL = os.environ.get('IS_LOCAL', 'false').lower() == 'true'

# Auto-detect local mode when running as script
if __name__ == "__main__":
    os.environ['IS_LOCAL'] = 'true'
    IS_LOCAL = True

# Load dotenv only in local mode
if IS_LOCAL:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Running in local development mode")
    except ImportError:
        print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

# Initialize AWS services based on environment
if IS_LOCAL:
    # Use local AWS configuration
    session = boto3.Session(region_name=os.environ.get("AWS_REGION", "eu-central-1"))
    secrets_client = session.client("secretsmanager") if "BINANCE_API_KEY_SECRET" in os.environ else None
    dynamodb = session.resource("dynamodb")
    table_name = os.environ.get("DYNAMO_TABLE")
    table = dynamodb.Table(table_name) if table_name else None
else:
    # Use Lambda environment AWS configuration
    secrets_client = boto3.client("secretsmanager")
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["DYNAMO_TABLE"])

def get_credentials():
    """Get API credentials from environment or Secrets Manager"""
    if IS_LOCAL:
        # Use direct environment variables in local mode
        api_key = os.environ.get("BINANCE_API_KEY")
        api_secret = os.environ.get("BINANCE_API_SECRET")
        
        # Fall back to Secrets Manager if specified and credentials not in env
        if not api_key and "BINANCE_API_KEY_SECRET" in os.environ:
            api_key = get_secret(os.environ["BINANCE_API_KEY_SECRET"])
        if not api_secret and "BINANCE_API_SECRET_SECRET" in os.environ:
            api_secret = get_secret(os.environ["BINANCE_API_SECRET_SECRET"])
    else:
        # Use Secrets Manager in Lambda environment
        api_key = get_secret(os.environ["BINANCE_API_KEY_SECRET"])
        api_secret = get_secret(os.environ["BINANCE_API_SECRET_SECRET"])
    
    return api_key, api_secret

def get_secret(secret_name):
    """Retrieve a secret from AWS Secrets Manager"""
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return response["SecretString"]
    except Exception as e:
        print(f"Error retrieving secret {secret_name}: {str(e)}")
        return None

def run_trading_bot():
    """Main trading bot logic"""
    try:
        # Get API credentials
        api_key, api_secret = get_credentials()
        
        if not api_key or not api_secret:
            error_msg = "Error: Binance API credentials not found"
            print(error_msg)
            return {"statusCode": 400, "body": json.dumps({"error": error_msg})}
        
        # Initialize exchange
        exchange = ccxt.binance({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {
                "defaultType": "spot"
            }
        })
        exchange.set_sandbox_mode(True)
        
        if IS_LOCAL:
            print("Connected to Binance sandbox mode")
        
        # Define trading parameters
        symbol = "BTC/USDT"
        timeframe = "1h"
        
        # Fetch OHLCV data
        if IS_LOCAL:
            print(f"Fetching {timeframe} data for {symbol}...")
        
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=50)
        
        if not ohlcv or len(ohlcv) < 20:
            error_msg = "Error: Not enough data points for SMA calculation"
            print(error_msg)
            return {"statusCode": 400, "body": json.dumps({"error": error_msg})}
        
        # Create dataframe and calculate SMA20
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["sma20"] = df["close"].rolling(window=20).mean()
        
        # Get last data point for analysis
        last = df.iloc[-1]
        price = last["close"]
        sma = last["sma20"]
        
        if IS_LOCAL:
            print(f"Current price: {price}")
            print(f"SMA20: {sma}")
        
        # Generate trading signal
        signal = None
        if price > sma:
            signal = "BUY"
        elif price < sma:
            signal = "SELL"
        
        if signal:
            if IS_LOCAL:
                print(f"Generated {signal} signal")
            
            # Create trade record
            trade = {
                "trade_id": str(uuid.uuid4()),
                "symbol": symbol,
                "signal": signal,
                "price": Decimal(str(price)),
                "timestamp": int(time.time())
            }
            
            # Save to DynamoDB if available
            if table:
                try:
                    table.put_item(Item=trade)
                    if IS_LOCAL:
                        print(f"Trade recorded in DynamoDB table: {table_name}")
                except Exception as e:
                    error_msg = f"Error saving to DynamoDB: {str(e)}"
                    print(error_msg)
                    return {"statusCode": 500, "body": json.dumps({"error": error_msg})}
            
            # Convert Decimal to float for JSON serialization
            trade_response = {k: float(v) if isinstance(v, Decimal) else v for k, v in trade.items()}
            return {
                "statusCode": 200,
                "body": json.dumps({"message": f"{signal} signal executed", "trade": trade_response})
            }
        else:
            if IS_LOCAL:
                print("No signal generated")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "No signal"})
            }
    
    except Exception as e:
        error_msg = f"Error running trading bot: {str(e)}"
        print(error_msg)
        return {"statusCode": 500, "body": json.dumps({"error": error_msg})}

def lambda_handler(event, context):
    """AWS Lambda entrypoint"""
    return run_trading_bot()

# Allow running as a script locally
if __name__ == "__main__":
    print("Starting trading bot...")
    result = run_trading_bot()
    print(json.dumps(json.loads(result["body"]), indent=2))