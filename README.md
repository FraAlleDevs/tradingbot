# AWS Crypto Trading Bot (SMA20)

This project implements a simple trading bot on AWS that uses an SMA20 strategy. It runs in AWS Lambda, stores trades in DynamoDB and can be triggered via an HTTP API (API Gateway).
The project should be as AWS native as possible. Everything that has to do with infrastructure should be handled via Terraform.
The idea is to use AI to support me to implement this project. Since AI tends to over perform and to reach fast a point where the AI don't understand anymore the full context of the project,
and so don't know how to fix anymore upcoming problems, and I want that we work in really small iteration. First make small code and configurations work and then extend it with more features.
We want to alawys work in a best practice approach, cost efficient, secure, scalable, maintainable and easy to understand, and always in a way that other people can join the project.
The AI should alway keep track or their applied changes with something like a changelog, as well as updateing a own AI README file and the project README file with project related information and changes.

## Used AWS Services for the MVP

- AWS Lambda
- AWS API Gateway
- AWS DynamoDB
- AWS Secrets Manager
- AWS CloudWatch
- AWS IAM
- AWS S3

## Features

- Binance Spot Testnet integration
- SMA20 buy/sell logic
- Secure access via Secrets Manager
- Terraform Deployment
- Python Lambda function

## Prerequisites

- AWS CLI configured
- Terraform installed
- Python 3.11

## Frontend (planned)

A dashboard to visualize the trades and configure the strategies (React + Tailwind).
