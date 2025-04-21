#!/bin/bash
# lambda_package.sh - Script to package the trading bot Lambda function

# Set up colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Exit on any error
set -e

echo -e "${YELLOW}Starting Lambda packaging process...${NC}"

# Create a clean deployment directory
echo "Creating deployment directory..."
rm -rf deployment
mkdir -p deployment

# Copy the bot code
echo "Copying bot.py to deployment directory..."
cp lambda/bot.py deployment/

# Install dependencies in the deployment directory
echo "Installing dependencies..."
pip install -r lambda/requirements.txt -t deployment/

# Create the zip file
echo "Creating zip archive..."
cd deployment
zip -r ../lambda_function.zip .
cd ..

# Check if zip was created successfully
if [ -f "lambda_function.zip" ]; then
    size=$(du -h lambda_function.zip | cut -f1)
    echo -e "${GREEN}Package created successfully!${NC}"
    echo "Package size: $size"
    echo "Location: $(pwd)/lambda_function.zip"
    
    # Warn if package is approaching Lambda limits
    if [[ $(du -m lambda_function.zip | cut -f1) -gt 200 ]]; then
        echo -e "${YELLOW}Warning: Package is approaching the Lambda size limit (250MB).${NC}"
        echo "Consider using Lambda Layers for dependencies if needed."
    fi
else
    echo -e "${RED}Error: Failed to create Lambda package${NC}"
    exit 1
fi

# Get S3 bucket name from Terraform outputs
echo "Getting S3 bucket name from Terraform..."
cd terraform
S3_BUCKET=$(terraform output -raw lambda_bucket_name)
cd ..

if [ -z "$S3_BUCKET" ]; then
    echo -e "${RED}Error: Could not retrieve S3 bucket name from Terraform.${NC}"
    echo "Make sure you've applied the Terraform configuration for the S3 bucket."
    exit 1
fi

# Upload the package
echo "Uploading package to S3 bucket: $S3_BUCKET..."
if aws s3 cp lambda_function.zip "s3://${S3_BUCKET}/lambda_function.zip"; then
    echo -e "${GREEN}Package uploaded to S3 successfully!${NC}"
    echo "S3 location: s3://${S3_BUCKET}/lambda_function.zip"
else
    echo -e "${RED}Error: Failed to upload package to S3.${NC}"
    echo "Check your AWS permissions and try again."
    exit 1
fi

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Deploy the Lambda function using: terraform apply"
echo "2. Check CloudWatch logs to verify the function works correctly"