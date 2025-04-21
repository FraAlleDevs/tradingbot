# S3 bucket for Lambda deployment packages
resource "aws_s3_bucket" "lambda_bucket" {
  bucket = "crypto-trading-lambda-artifacts-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Project     = "TradingBot"
    Environment = "Dev"
    ManagedBy   = "Terraform"
  }
}

# Block public access to the bucket
resource "aws_s3_bucket_public_access_block" "lambda_bucket" {
  bucket = aws_s3_bucket.lambda_bucket.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Output the bucket name for reference by deployment scripts
output "lambda_bucket_name" {
  value = aws_s3_bucket.lambda_bucket.id
  description = "Name of the S3 bucket for Lambda artifacts"
}