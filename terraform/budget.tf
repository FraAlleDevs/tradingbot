# Configure AWS Budgets for cost management
# Set up monthly budget with alerts at different thresholds

resource "aws_budgets_budget" "crypto_trading_monthly" {
  name              = "crypto-trading-monthly-budget"
  budget_type       = "COST"
  limit_amount      = "30"
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = "2025-01-01_00:00"  # Starting from beginning of year
  
  # Budget notification at 50% threshold
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 50
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["budget-tradingbot-dev@sherrill.de"]
  }
  
  # Budget notification at 80% threshold
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["budget-tradingbot-dev@sherrill.de"]
  }
  
  # Budget notification at 100% threshold
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["budget-tradingbot-dev@sherrill.de"]
  }
  
  # Forecasted spend notification
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 90
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = ["budget-tradingbot-dev@sherrill.de"]
  }

  # Cost filters
  cost_filter {
    name = "TagKeyValue"
    values = ["Project$TradingBot"]
  }
}