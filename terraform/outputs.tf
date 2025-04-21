# Output the table name for reference
output "dynamodb_table_name" {
  description = "The name of the DynamoDB table"
  value       = aws_dynamodb_table.trades.name
}

output "binance_api_key_secret_name" {
  value       = aws_secretsmanager_secret.binance_api_key.name
  description = "Name of the secret storing the Binance API key"
}

output "binance_api_secret_secret_name" {
  value       = aws_secretsmanager_secret.binance_api_secret.name
  description = "Name of the secret storing the Binance API secret"
}