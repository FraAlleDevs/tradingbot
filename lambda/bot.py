import os
import json
import boto3
import ccxt
import time
import uuid
import pandas as pd
from decimal import Decimal

secrets_client = boto3.client("secretsmanager")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["DYNAMO_TABLE"])

def get_secret(secret_name):
    response = secrets_client.get_secret_value(SecretId=secret_name)
    return response["SecretString"]

def lambda_handler(event, context):
    api_key = get_secret(os.environ["BINANCE_API_KEY_SECRET"])
    api_secret = get_secret(os.environ["BINANCE_API_SECRET_SECRET"])

    exchange = ccxt.binance({
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
        "options": {
            "defaultType": "spot"
        }
    })
    exchange.set_sandbox_mode(True)

    symbol = "BTC/USDT"
    timeframe = "1h"
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=50)

    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["sma20"] = df["close"].rolling(window=20).mean()

    last = df.iloc[-1]
    price = last["close"]
    sma = last["sma20"]
    signal = None

    if price > sma:
        signal = "BUY"
    elif price < sma:
        signal = "SELL"

    if signal:
        trade = {
            "trade_id": str(uuid.uuid4()),
            "symbol": symbol,
            "signal": signal,
            "price": Decimal(str(price)),
            "timestamp": int(time.time())
        }
        table.put_item(Item=trade)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": f"{signal} signal executed", "trade": trade})
        }

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "No signal"})
    }
