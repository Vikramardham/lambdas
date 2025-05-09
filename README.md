# AWS Lambda Python Demo

This repository contains a **demo AWS Lambda function written in Python** and a streamlined workflow for deploying it as a Lambda function on AWS using Docker and Terraform.

## What This Repo Does

- **Demo Lambda Function:**
  - A Python-based Lambda function (using FastAPI and Mangum) that can be used as a template for serverless APIs or LLM-powered utilities.
  - Example endpoint: `/process` for document or data processing.

- **Deployment Workflow:**
  - **Dockerfile**: Containerizes the Lambda function for consistent, dependency-free deployment.
  - **Terraform**: Infrastructure as code to provision the Lambda function, API Gateway, and required AWS resources.
  - **Bash Deployment Script**: One command to build, push, and deploy the Lambda, and to set up required secrets in AWS Secrets Manager.

- **Local Testing:**
  - Includes a `lambda_entry.py` script to simulate Lambda invocation locally for rapid development and debugging.

## How to Use

1. **Prepare your environment:**
   - Install [Docker](https://www.docker.com/), [Terraform](https://www.terraform.io/), and [AWS CLI](https://aws.amazon.com/cli/).
   - Set up your AWS credentials/profile.

2. **Set your API keys as environment variables:**
   - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `COHERE_API_KEY`, `GEMINI_API_KEY` (as needed)

3. **Deploy with one command:**
   ```bash
   ./scripts/deploy_and_secrets.sh <aws_profile> <aws_region>
   ```
   - This will build and push the Docker image, set up secrets, and deploy the Lambda/API Gateway using Terraform.

4. **Get your API endpoint:**
   - After deployment, use the output or your AWS Console to find the API Gateway endpoint.

5. **Test locally:**
   - Run `python lambda_entry.py` to simulate Lambda invocation with a sample event.

6. **Test remotely:**
   - Use `curl` or Postman to send a POST request to your API endpoint:
     ```bash
     curl -X POST '<your-api-endpoint>/process' \
       -H 'Content-Type: application/json' \
       -d '{"document_data": "{\"test\": \"data\"}", "document_type": "json", "instructions": "Summarize the test data"}'
     ```

## Project Structure

```
.
├── src/                  # Lambda function source code
├── scripts/              # Deployment and utility scripts
├── terraform/            # Terraform IaC for AWS resources
├── Dockerfile            # Container definition for Lambda
├── requirements.txt      # Python dependencies
├── lambda_entry.py       # Local Lambda test harness
└── README.md             # This file
```

## Notes
- **No secrets or sensitive data should be committed to this repo.**
- The repo is intended as a template/demo for serverless Python Lambda deployments.
- Unnecessary files and scripts have been removed for clarity and security.

## License
MIT 