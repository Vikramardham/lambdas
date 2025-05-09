# Setting Up the LLM Utilities API Project

This document provides detailed instructions for setting up and running the LLM Utilities API project locally.

## Prerequisites

- Python 3.10 or higher
- `uv` for Python package management
- PowerShell (Windows) or Bash (Linux/Mac)
- AWS account (for deployment)
- Terraform (for deployment)

## Initial Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create a virtual environment:
   ```bash
   uv venv
   uv venv activate
   ```

3. Install dependencies:
   ```bash
   uv add -r requirements.txt
   ```

4. Create a `.env` file with your API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## Running Locally

1. Start the FastAPI development server:
   ```bash
   uvicorn src.lambda_functions.document_processor.app:app --reload --host 0.0.0.0 --port 8000
   ```
   
   Alternatively, you can use the provided script:
   ```bash
   ./scripts/run_local_server.ps1  # Windows
   ```

2. Access the API documentation at http://localhost:8000/docs

## Running Tests

Run the test suite:
```bash
pytest
```

## Building Lambda Deployment Package

To build the deployment package for AWS Lambda:

```bash
./scripts/build_lambda_package.ps1  # Windows
```

This will create a zip file in the `deployment` directory that can be deployed to AWS Lambda.

## Deploying to AWS

### Configuring Multiple AWS Accounts

If you have multiple AWS accounts, you can set up named profiles in AWS CLI:

1. Install AWS CLI if not already installed:
   ```bash
   pip install awscli
   ```

2. Create named profiles for each account:
   ```bash
   aws configure --profile account1
   aws configure --profile account2
   ```

3. When prompted, enter your AWS credentials for each account:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region (e.g., us-east-1)
   - Default output format (json is recommended)

4. Verify your profiles:
   ```bash
   aws sts get-caller-identity --profile account1
   ```

### Deploying with Terraform

1. Use the deployment script to deploy to a specific AWS account:
   ```bash
   ./scripts/deploy_to_aws.ps1 -AwsProfile account1 -AwsRegion us-east-1 -Environment dev
   ```

   Parameters:
   - `-AwsProfile`: AWS CLI profile to use (default: "default")
   - `-AwsRegion`: AWS region to deploy to (default: "us-east-1")
   - `-Environment`: Deployment environment (default: "dev")
   - `-BuildPackage`: Whether to build the Lambda package (default: true)

2. Alternatively, you can manually use Terraform:
   ```bash
   cd terraform
   terraform init
   terraform plan -var="aws_profile=account1" -var="aws_region=us-east-1"
   terraform apply
   ```

3. Store your API keys in AWS Secrets Manager:
   - Go to the AWS Secrets Manager console
   - Select the secret created by Terraform (`llm-utilities/api-keys` by default)
   - Create a new secret version with the following format:
     ```json
     {
       "OPENAI_API_KEY": "your_openai_api_key",
       "ANTHROPIC_API_KEY": "your_anthropic_api_key",
       "COHERE_API_KEY": "your_cohere_api_key",
       "GEMINI_API_KEY": "your_gemini_api_key"
     }
     ```

## Example API Usage

Here's an example of how to use the document processing API:

```python
import requests
import json
import base64

# Load an image
with open("example.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

# API request
response = requests.post(
    "http://localhost:8000/process",
    json={
        "document_data": image_data,
        "document_type": "image",
        "instructions": "Extract all text and identify main objects in the image."
    }
)

# Print the result
print(json.dumps(response.json(), indent=2))
``` 