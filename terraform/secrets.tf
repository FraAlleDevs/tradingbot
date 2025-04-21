# AWS Secrets Manager configuration for Binance API credentials
# These secrets will store the API keys needed for the trading bot 
# to authenticate with Binance's API

# Secret for the Binance API Key
resource "aws_secretsmanager_secret" "binance_api_key" {
  name        = "binance/api_key"
  description = "Binance API Key for trading bot"
  
  # Recovery window in days (7-30 days, or 0 for no recovery)
  recovery_window_in_days = 7
  
  tags = {
    Type        = "APICredential"
  }
}

# Secret for the Binance API Secret
resource "aws_secretsmanager_secret" "binance_api_secret" {
  name        = "binance/api_secret"
  description = "Binance API Secret for trading bot"
  
  # Recovery window in days (7-30 days, or 0 for no recovery)
  recovery_window_in_days = 7
  
  tags = {
    Type        = "APICredential"
  }
}
