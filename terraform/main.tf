provider "aws" {
  region = var.aws_region
 
  default_tags {
    tags = {
      Project     = "TradingBot"
      Environment = "Dev"
      Owner       = "Anthony Sherrill"
      Type        = "Internal"
      Stage       = "Prototype"
      ManagedBy   = "Terraform"
    }
  }
}

resource "aws_secretsmanager_secret" "binance_api_key" {
  name = "binance_api_key"
}

resource "aws_secretsmanager_secret" "binance_api_secret" {
  name = "binance_api_secret"
}

resource "aws_dynamodb_table" "trades" {
  name         = "crypto_trades"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "trade_id"

  attribute {
    name = "trade_id"
    type = "S"
  }
}

resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Effect = "Allow",
        Sid    = ""
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "trading_bot" {
  function_name = "crypto_trading_bot"
  s3_bucket     = aws_s3_bucket.lambda_artifacts.id
  s3_key        = "lambda/lambda.zip"
  handler       = "bot.lambda_handler"
  runtime       = "python3.11"
  role          = aws_iam_role.lambda_exec_role.arn

  environment {
    variables = {
      DYNAMO_TABLE              = aws_dynamodb_table.trades.name
      BINANCE_API_KEY_SECRET    = aws_secretsmanager_secret.binance_api_key.name
      BINANCE_API_SECRET_SECRET = aws_secretsmanager_secret.binance_api_secret.name
    }
  }

  layers = [aws_lambda_layer_version.tradingbot_deps.arn]
}

resource "aws_apigatewayv2_api" "api" {
  name          = "trading-bot-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.trading_bot.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "lambda_route" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "POST /run-bot"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw_lambda" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trading_bot.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

resource "aws_s3_bucket" "lambda_artifacts" {
  bucket = "tradingbot-artifacts-dev"

  lifecycle {
    prevent_destroy = false
  }

  force_destroy = true
}

resource "aws_lambda_layer_version" "tradingbot_deps" {
  layer_name          = "tradingbot-deps"
  compatible_runtimes = ["python3.11"]
  s3_bucket           = aws_s3_bucket.lambda_artifacts.id
  s3_key              = "layers/tradingbot-layer.zip"
}