#!/bin/bash
# lambda_package.sh - Script to package the trading bot Lambda function
# Now with Docker support for Lambda-compatible binary dependencies

# Set up colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Exit on any error
set -e

# Parse command line arguments
USE_DOCKER=true
CREATE_LAYER=false
FORCE_LOCAL=false

# Process command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --no-docker)
      USE_DOCKER=false
      shift
      ;;
    --layer)
      CREATE_LAYER=true
      shift
      ;;
    --force-local)
      FORCE_LOCAL=true
      shift
      ;;
    --help)
      echo "Usage: ./lambda_package.sh [OPTIONS]"
      echo "Package the Lambda function for deployment"
      echo ""
      echo "Options:"
      echo "  --no-docker    Build without Docker (not recommended)"
      echo "  --layer        Create a Lambda Layer for dependencies instead of a full package"
      echo "  --force-local  Force local build even if Docker is available"
      echo "  --help         Display this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run './lambda_package.sh --help' for usage information"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AWS Lambda Package Builder for Trading Bot ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"

# Check for Docker availability if we're using Docker
if $USE_DOCKER && ! $FORCE_LOCAL; then
  if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Warning: Docker not found. Using local build instead.${NC}"
    echo "Install Docker for better Lambda compatibility or use --no-docker flag to silence this warning."
    USE_DOCKER=false
  fi
fi

# Get S3 bucket name from Terraform outputs
echo "Checking for S3 bucket name from Terraform..."
cd terraform
S3_BUCKET=$(terraform output -raw lambda_bucket_name 2>/dev/null)
cd ..

if [ -z "$S3_BUCKET" ]; then
  echo -e "${YELLOW}Warning: Could not retrieve S3 bucket name from Terraform.${NC}"
  echo "Will proceed with packaging only. You'll need to manually deploy to S3."
  echo "Make sure you've applied the Terraform configuration for the S3 bucket."
fi

# Function to build using Docker (Lambda-compatible environment)
build_with_docker() {
  echo -e "${YELLOW}Building with Docker for Lambda compatibility...${NC}"
  
  # Check if an amazonlinux:2 image is already pulled
  if ! docker image inspect amazonlinux:2 &> /dev/null; then
    echo "Pulling amazonlinux:2 Docker image..."
    docker pull amazonlinux:2
  fi
  
  if $CREATE_LAYER; then
    echo "Creating Lambda Layer for dependencies..."
    
    # Create a Lambda Layer using Docker
    docker run --rm -v "$(pwd):/var/task" -w /var/task amazonlinux:2 bash -c "
      echo 'Installing build tools...'
      yum install -y python3.11 python3.11-devel gcc gcc-c++ make zip git
      
      echo 'Creating Layer directory structure...'
      mkdir -p python/lib/python3.11/site-packages
      
      echo 'Installing dependencies into Layer directory...'
      pip3.11 install -r lambda/requirements.txt -t python/lib/python3.11/site-packages
      
      echo 'Creating Layer zip file...'
      zip -r tradingbot-layer.zip python
    "
    
    # Check if layer zip was created successfully
    if [ -f "tradingbot-layer.zip" ]; then
      size=$(du -h tradingbot-layer.zip | cut -f1)
      echo -e "${GREEN}Layer package created successfully!${NC}"
      echo "Layer package size: $size"
      echo "Location: $(pwd)/tradingbot-layer.zip"
      
      # Upload layer to S3 if bucket name is available
      if [ -n "$S3_BUCKET" ]; then
        echo "Uploading Layer to S3 bucket: $S3_BUCKET..."
        aws s3 cp tradingbot-layer.zip "s3://${S3_BUCKET}/layers/tradingbot-layer.zip"
        echo -e "${GREEN}Layer uploaded to S3 successfully!${NC}"
        echo "S3 location: s3://${S3_BUCKET}/layers/tradingbot-layer.zip"
        
        # Publish the layer
        echo "Publishing Lambda Layer..."
        LAYER_VERSION=$(aws lambda publish-layer-version \
          --layer-name crypto-trading-dependencies \
          --description "Dependencies for the crypto trading bot" \
          --content S3Bucket=${S3_BUCKET},S3Key=layers/tradingbot-layer.zip \
          --compatible-runtimes python3.11 \
          --query 'LayerVersionArn' \
          --output text)
        
        echo -e "${GREEN}Layer published successfully!${NC}"
        echo "Layer ARN: $LAYER_VERSION"
        
        # Create a minimal Lambda package with just the code
        echo "Creating minimal Lambda package with just the bot code..."
        rm -rf deployment
        mkdir -p deployment
        cp lambda/bot.py deployment/
        cd deployment
        zip -r ../lambda_function.zip .
        cd ..
        
        if [ -f "lambda_function.zip" ]; then
          echo "Uploading minimal Lambda package to S3..."
          aws s3 cp lambda_function.zip "s3://${S3_BUCKET}/lambda_function.zip"
          
          echo -e "${GREEN}Minimal Lambda package uploaded to S3 successfully!${NC}"
          echo "S3 location: s3://${S3_BUCKET}/lambda_function.zip"
          
          echo -e "${YELLOW}Next step: Update Lambda function configuration to use the new layer${NC}"
          echo "Run: aws lambda update-function-configuration \\"
          echo "       --function-name crypto_trading_bot \\"
          echo "       --layers $LAYER_VERSION"
        fi
      else
        echo -e "${YELLOW}No S3 bucket information available. Manual upload required.${NC}"
      fi
    else
      echo -e "${RED}Error: Failed to create Lambda Layer package${NC}"
      exit 1
    fi
  else
    # Create a full Lambda package with Docker
    echo "Creating full Lambda package..."
    
    docker run --rm -v "$(pwd):/var/task" -w /var/task amazonlinux:2 bash -c "
      echo 'Installing build tools...'
      yum install -y python3.11 python3.11-devel gcc gcc-c++ make zip git
      
      echo 'Creating deployment directory...'
      rm -rf deployment
      mkdir -p deployment
      
      echo 'Copying bot code...'
      cp lambda/bot.py deployment/
      
      echo 'Installing dependencies...'
      pip3.11 install -r lambda/requirements.txt -t deployment/
      
      echo 'Creating zip archive...'
      cd deployment
      zip -r ../lambda_function.zip .
    "
    
    # Check if zip was created successfully
    if [ -f "lambda_function.zip" ]; then
      size=$(du -h lambda_function.zip | cut -f1)
      echo -e "${GREEN}Package created successfully!${NC}"
      echo "Package size: $size"
      echo "Location: $(pwd)/lambda_function.zip"
      
      # Warn if package is approaching Lambda limits
      if [[ $(du -m lambda_function.zip | cut -f1) -gt 200 ]]; then
        echo -e "${YELLOW}Warning: Package is approaching the Lambda size limit (250MB).${NC}"
        echo "Consider using --layer option to create a Lambda Layer for dependencies."
      fi
      
      # Upload the package to S3 if bucket name is available
      if [ -n "$S3_BUCKET" ]; then
        echo "Uploading package to S3 bucket: $S3_BUCKET..."
        aws s3 cp lambda_function.zip "s3://${S3_BUCKET}/lambda_function.zip"
        echo -e "${GREEN}Package uploaded to S3 successfully!${NC}"
        echo "S3 location: s3://${S3_BUCKET}/lambda_function.zip"
        
        echo -e "${YELLOW}Next step: Update Lambda function code${NC}"
        echo "Run: aws lambda update-function-code \\"
        echo "       --function-name crypto_trading_bot \\"
        echo "       --s3-bucket ${S3_BUCKET} \\"
        echo "       --s3-key lambda_function.zip"
      else
        echo -e "${YELLOW}No S3 bucket information available. Manual upload required.${NC}"
      fi
    else
      echo -e "${RED}Error: Failed to create Lambda package${NC}"
      exit 1
    fi
  fi
}

# Function to build locally (less compatible, may have issues with binary dependencies)
build_locally() {
  echo -e "${YELLOW}Building locally (warning: may have compatibility issues with Lambda)...${NC}"
  
  if $CREATE_LAYER; then
    echo "Creating Lambda Layer for dependencies..."
    
    # Create Layer directory structure
    mkdir -p python/lib/python3.11/site-packages
    
    # Install dependencies into Layer directory
    pip install -r lambda/requirements.txt -t python/lib/python3.11/site-packages
    
    # Create Layer zip file
    zip -r tradingbot-layer.zip python
    
    # Check if layer zip was created successfully
    if [ -f "tradingbot-layer.zip" ]; then
      size=$(du -h tradingbot-layer.zip | cut -f1)
      echo -e "${GREEN}Layer package created successfully!${NC}"
      echo "Layer package size: $size"
      echo "Location: $(pwd)/tradingbot-layer.zip"
      
      echo -e "${YELLOW}Warning: This layer was built locally and may have compatibility issues with Lambda.${NC}"
      echo "Binary dependencies like cryptography, numpy, and pandas may not work properly."
      
      # Upload layer to S3 if bucket name is available
      if [ -n "$S3_BUCKET" ]; then
        echo "Uploading Layer to S3 bucket: $S3_BUCKET..."
        aws s3 cp tradingbot-layer.zip "s3://${S3_BUCKET}/layers/tradingbot-layer.zip"
        echo -e "${GREEN}Layer uploaded to S3 successfully!${NC}"
        echo "S3 location: s3://${S3_BUCKET}/layers/tradingbot-layer.zip"
      else
        echo -e "${YELLOW}No S3 bucket information available. Manual upload required.${NC}"
      fi
    else
      echo -e "${RED}Error: Failed to create Lambda Layer package${NC}"
      exit 1
    fi
  else
    # Create a full Lambda package locally
    echo "Creating full Lambda package..."
    
    # Create a clean deployment directory
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
      
      echo -e "${YELLOW}Warning: This package was built locally and may have compatibility issues with Lambda.${NC}"
      echo "Binary dependencies like cryptography, numpy, and pandas may not work properly."
      
      # Warn if package is approaching Lambda limits
      if [[ $(du -m lambda_function.zip | cut -f1) -gt 200 ]]; then
        echo -e "${YELLOW}Warning: Package is approaching the Lambda size limit (250MB).${NC}"
        echo "Consider using --layer option to create a Lambda Layer for dependencies."
      fi
      
      # Upload the package to S3 if bucket name is available
      if [ -n "$S3_BUCKET" ]; then
        echo "Uploading package to S3 bucket: $S3_BUCKET..."
        aws s3 cp lambda_function.zip "s3://${S3_BUCKET}/lambda_function.zip"
        echo -e "${GREEN}Package uploaded to S3 successfully!${NC}"
        echo "S3 location: s3://${S3_BUCKET}/lambda_function.zip"
      else
        echo -e "${YELLOW}No S3 bucket information available. Manual upload required.${NC}"
      fi
    else
      echo -e "${RED}Error: Failed to create Lambda package${NC}"
      exit 1
    fi
  fi
}

# Main execution logic
if $USE_DOCKER && ! $FORCE_LOCAL; then
  build_with_docker
else
  build_locally
fi

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            Packaging Complete               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"

echo -e "${YELLOW}Next steps:${NC}"
if $CREATE_LAYER; then
  echo "1. Deploy the Lambda function with the new layer using Terraform or AWS CLI"
  echo "   aws lambda update-function-configuration \\"
  echo "     --function-name crypto_trading_bot \\"
  echo "     --layers <LAYER_ARN>"
else
  echo "1. Deploy the Lambda function using: terraform apply"
fi
echo "2. Check CloudWatch logs to verify the function works correctly"