# DynamoDB table for storing trade signals
resource "aws_dynamodb_table" "trades" {
  name         = "crypto_trades"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "trade_id"

  tags = {
    Type = "TradeSignal"
  }

  attribute {
    name = "trade_id"
    type = "S"
  }

  attribute {
    name = "symbol"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  global_secondary_index {
    name            = "SymbolTimeIndex"
    hash_key        = "symbol"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  # Enable server-side encryption
  server_side_encryption {
    enabled = true
  }
}