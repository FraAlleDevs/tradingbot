provider "aws" {
  region = var.aws_region
 
  default_tags {
    tags = {
      Project     = "TradingBot"
      Environment = "Dev"
      Owner       = "Anthony Sherrill"
      Stage       = "Prototype"
      ManagedBy   = "Terraform"
    }
  }
}
