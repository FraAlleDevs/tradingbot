# AWS Crypto Trading Bot (SMA20)

This project implements a simple trading bot on AWS that uses an SMA20 strategy. It runs in AWS Lambda, stores trades in DynamoDB and can be triggered via an HTTP API (API Gateway).
The project is designed to be AWS-native with all infrastructure managed through Terraform.

## Features

- Binance Spot Testnet integration
- SMA20 buy/sell trading logic
- Secure API key storage via Secrets Manager
- Trade history in DynamoDB
- Scheduled execution via CloudWatch Events
- Configurable deployment via Terraform
- Local development support

## Used AWS Services

- AWS Lambda - Runs the trading bot code
- AWS API Gateway - Provides HTTP endpoint to trigger bot
- AWS DynamoDB - Stores trading signals and history
- AWS Secrets Manager - Securely stores Binance API credentials
- AWS CloudWatch - Monitors and logs bot execution
- AWS IAM - Manages permissions
- AWS S3 - Stores Lambda deployment packages

## Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform v1.0.0+
- Python 3.11
- Binance account with API keys

## Deployment Instructions

The deployment must be done in multiple phases to handle dependencies correctly:

### 1. Local Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/aws-crypto-trading-bot.git
cd aws-crypto-trading-bot

# Set up Python virtual environment
python -m venv venv
source venv/bin/activate
pip install -r lambda/requirements.txt

# Create and configure your .env file for local testing
cp .env.example .env
# Edit .env with your Binance API credentials
```

### 2. Initial Deployment

```bash
# Phase 1: Create only the S3 bucket first
cd terraform
terraform init
terraform apply -target=aws_s3_bucket.lambda_bucket -target=aws_s3_bucket_public_access_block.lambda_bucket

# Package and upload the Lambda function
cd ..
./scripts/lambda_package.sh

# Phase 2: Create everything else
cd terraform
terraform apply
```

### 3. Testing

To test the bot locally:

```bash
source venv/bin/activate
python lambda/bot.py
```

To trigger the deployed Lambda function:

```bash
aws lambda invoke \
  --function-name crypto_trading_bot \
  --payload '{}' \
  response.json
```

## Architecture

The bot follows a serverless architecture pattern:

1. Lambda function runs on schedule or via API Gateway
2. Bot fetches price data from Binance
3. SMA20 algorithm generates buy/sell signals
4. Signals are stored in DynamoDB
5. CloudWatch monitors execution and logs results

## Frontend (Planned)

A dashboard to visualize the trades and configure the strategies (React + Tailwind CSS).

## Project Management

This project follows an iterative development approach:

- CHANGELOG.md tracks all changes
- CLAUDE.md contains build commands and style guidelines
- Security best practices enforced throughout
