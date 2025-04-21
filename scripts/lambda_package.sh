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

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to get AWS account ID. Check your AWS credentials.${NC}"
    exit 1
fi

# Set the S3 bucket name
S3_BUCKET="crypto-trading-lambda-artifacts-${ACCOUNT_ID}"

# Check if the S3 bucket exists
echo "Checking if S3 bucket exists..."
if ! aws s3 ls "s3://${S3_BUCKET}" &>/dev/null; then
    echo -e "${YELLOW}S3 bucket does not exist. Creating bucket ${S3_BUCKET}...${NC}"
    
    # Create the bucket
    if ! aws s3 mb "s3://${S3_BUCKET}" --region $(aws configure get region); then
        echo -e "${RED}Error: Failed to create S3 bucket.${NC}"
        echo "Please create the bucket manually or check your permissions."
        exit 1
    fi
    
    # Enable versioning on the bucket
    aws s3api put-bucket-versioning --bucket "${S3_BUCKET}" --versioning-configuration Status=Enabled
    
    # Block public access
    aws s3api put-public-access-block --bucket "${S3_BUCKET}" \
        --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    
    echo -e "${GREEN}S3 bucket created successfully!${NC}"
fi

# Upload the package
echo "Uploading package to S3..."
if aws s3 cp lambda_function.zip "s3://${S3_BUCKET}/lambda_function.zip"; then
    echo -e "${GREEN}Package uploaded to S3 successfully!${NC}"
    echo "S3 location: s3://${S3_BUCKET}/lambda_function.zip"
else
    echo -e "${RED}Error: Failed to upload package to S3.${NC}"
    echo "Check your AWS permissions and try again."
    exit 1
fi

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Deploy this package to AWS Lambda using Terraform"
echo "2. Ensure environment variables are set correctly in your Lambda configuration"
echo "3. Test the Lambda function to verify it works as expected"