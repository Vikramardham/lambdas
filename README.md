# LLM Utilities API

This repository contains serverless LLM utilities deployed on AWS Lambda, accessible through an API. The utilities process various document types (images, PDFs, JSON) and return structured JSON responses using LLM capabilities.

## Features

- Document processor Lambda function that handles images, PDFs, and JSON
- Integration with LLMs via Instructor and LiteLLM
- Secure credential management
- Configurable LLM providers
- API Gateway integration
- Container-based deployment for reliable dependency management

## Project Structure

```
.
├── src/
│   ├── lambda_functions/        # AWS Lambda function implementations
│   │   └── document_processor/  # Document processing function
│   ├── utils/                   # Shared utility modules
│   └── config/                  # Configuration modules
├── tests/                       # Test suite
├── docs/                        # Documentation
├── scripts/                     # Deployment and utility scripts
├── terraform/                   # Terraform deployment configuration
├── Dockerfile                   # Container definition for Lambda
├── .env.example                 # Example environment variables
├── requirements.txt             # Python dependencies
└── README.md                    # This README file
```

## Setup

1. Create a Python virtual environment:
```bash
uv venv
uv venv activate
```

2. Install dependencies:
```bash
uv add -r requirements.txt
```

3. Create a `.env` file based on `.env.example` with your API keys.

## Development

To run tests:
```bash
pytest
```

To run the API locally:
```bash
./scripts/run_local_server.ps1
```

## Deployment

### Prerequisites

- AWS account with appropriate permissions
- AWS CLI configured with credentials
- Docker Desktop installed and running
- Terraform installed (for infrastructure deployment)

### Deployment Steps

Use the consolidated deployment script to handle the entire deployment process:

```powershell
# Full deployment (ECR repo, Docker image, Terraform)
./scripts/deploy.ps1 -AwsProfile your-profile-name

# Skip certain steps if needed
./scripts/deploy.ps1 -AwsProfile your-profile-name -SkipEcr -SkipImageBuild
```

After deployment, set your API keys in AWS Secrets Manager:

```powershell
aws secretsmanager put-secret-value --profile your-profile-name --secret-id llm-utilities/api-keys --secret-string '{"OPENAI_API_KEY":"your-key","ANTHROPIC_API_KEY":"your-key","COHERE_API_KEY":"your-key","GEMINI_API_KEY":"your-key"}'
```

### Lambda Troubleshooting Tools

When troubleshooting Lambda function issues, use the environment analyzer:

```powershell
./scripts/analyze_lambda_env.ps1 -AwsProfile your-profile-name -FunctionName document-processor
```

This script will analyze the Lambda environment and provide detailed information about imports, Python versions, and installed packages.

### Using the Document Processing API

The deployed API provides document processing capabilities via a simple REST interface.

### Getting the API Endpoint

After deployment, you can get the API endpoint using the provided script:

```powershell
./scripts/get_api_endpoint.ps1 -AwsProfile your-profile-name
```

This will display the API endpoint URL and example commands for testing.

### Testing the Lambda Function

You can test the Lambda function directly using the consolidated test script:

```powershell
# Test with a simple direct invocation (easiest method)
./scripts/test_lambda.ps1 -AwsProfile your-profile-name -EventType direct

# Test with an API Gateway event format
./scripts/test_lambda.ps1 -AwsProfile your-profile-name -EventType api-gateway

# Test with a custom event file
./scripts/test_lambda.ps1 -AwsProfile your-profile-name -CustomEventFile path/to/your/event.json
```

These tests use the event files in the `examples` directory.

### Testing with Example Scripts

The repository includes example scripts for testing the API with different document types:

```powershell
# Get the API endpoint
$apiEndpoint = ./scripts/get_api_endpoint.ps1 -AwsProfile your-profile-name

# Test JSON document processing
python examples/test_document_processor.py --api-url $apiEndpoint --test-type json

# Test image document processing (requires sample_receipt.jpg in examples directory)
python examples/test_document_processor.py --api-url $apiEndpoint --test-type image

# Test PDF document processing (requires sample_invoice.pdf in examples directory)
python examples/test_document_processor.py --api-url $apiEndpoint --test-type pdf
```

### API Request Format

The API accepts POST requests to the `/process` endpoint with the following JSON payload:

```json
{
  "document_data": "string",  // Base64-encoded document data or JSON string
  "document_type": "json|image|pdf",  // Optional, will auto-detect if not provided
  "llm_provider": "openai|anthropic|cohere|gemini",  // Optional, uses default if not specified
  "instructions": "string"  // Processing instructions for the LLM
}
```

### API Response Format

The API returns a JSON response with the following structure:

```json
{
  "request_id": "string",
  "success": true,
  "result": {
    "summary": {
      "title": "string",
      "content": "string"
    },
    "text_annotations": [
      {
        "type": "string",
        "content": "string"
      }
    ],
    "entity_annotations": [
      {
        "entity_type": "string",
        "name": "string",
        "value": "string"
      }
    ]
  }
}
```

In case of error:

```json
{
  "request_id": "string",
  "success": false,
  "error_message": "string"
}
``` 