# Data sources for use across Terraform configuration

# Get current AWS account ID
data "aws_caller_identity" "current" {}