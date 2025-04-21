# Lambda function definition and required permissions
# This sets up the trading bot Lambda with appropriate access to AWS services

# IAM role that the Lambda function will assume
resource "aws_iam_role" "lambda_role" {
  name = "trading_bot_lambda_role"

  # Trust relationship policy allowing Lambda to assume this role
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Basic Lambda execution policy - allows Lambda to write logs to CloudWatch
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom policy to allow Lambda to read from Secrets Manager
resource "aws_iam_policy" "secrets_access" {
  name        = "trading_bot_secrets_access"
  description = "Allow Lambda to read Binance API credentials from Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "secretsmanager:GetSecretValue"
      Resource = [
        aws_secretsmanager_secret.binance_api_key.arn,
        aws_secretsmanager_secret.binance_api_secret.arn
      ]
    }]
  })
}

# Attach the Secrets Manager access policy to the Lambda role
resource "aws_iam_role_policy_attachment" "lambda_secrets" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.secrets_access.arn
}

# Custom policy to allow Lambda to write to DynamoDB
resource "aws_iam_policy" "dynamodb_access" {
  name        = "trading_bot_dynamodb_access"
  description = "Allow Lambda to write trading signals to DynamoDB"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ]
      Resource = [
        aws_dynamodb_table.trades.arn,
        "${aws_dynamodb_table.trades.arn}/index/*"
      ]
    }]
  })
}

# Attach the DynamoDB access policy to the Lambda role
resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.dynamodb_access.arn
}

# The Lambda function definition
resource "aws_lambda_function" "trading_bot" {
  s3_bucket        = aws_s3_bucket.lambda_bucket.id
  s3_key           = "lambda_function.zip"
  function_name    = "crypto_trading_bot"
  role             = aws_iam_role.lambda_role.arn
  handler          = "bot.lambda_handler"
  runtime          = "python3.11"
  
  # Use S3 version if available (helps with deployments)
  s3_object_version = null
  
  # This is important for detecting changes
  source_code_hash = filebase64sha256("../lambda_function.zip")
  
  # Add the Lambda layer - using data source for account ID
  layers = ["arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:layer:tradingbot-dependencies:1"]
  
  # Other settings remain the same
  timeout     = 60
  memory_size = 256
  
  environment {
    variables = {
      DYNAMO_TABLE             = aws_dynamodb_table.trades.name
      BINANCE_API_KEY_SECRET   = aws_secretsmanager_secret.binance_api_key.name
      BINANCE_API_SECRET_SECRET = aws_secretsmanager_secret.binance_api_secret.name
    }
  }
}

# CloudWatch Log Group for Lambda with 14-day retention
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.trading_bot.function_name}"
  retention_in_days = 14
}

# EventBridge rule to schedule Lambda execution every hour
resource "aws_cloudwatch_event_rule" "hourly_execution" {
  name                = "hourly_trading_bot_execution"
  description         = "Trigger trading bot Lambda every hour"
  schedule_expression = "rate(1 hour)"
}

# Target to connect the EventBridge rule to the Lambda function
resource "aws_cloudwatch_event_target" "trigger_lambda" {
  rule      = aws_cloudwatch_event_rule.hourly_execution.name
  target_id = "TriggerTradingBot"
  arn       = aws_lambda_function.trading_bot.arn
}

# Permission allowing EventBridge to invoke the Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trading_bot.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.hourly_execution.arn
}

# S3 bucket for Lambda is defined in s3.tf