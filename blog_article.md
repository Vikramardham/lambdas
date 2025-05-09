# Integrating LLMs into Enterprise Infrastructure with AWS Lambda

In today's rapidly evolving AI landscape, integrating Large Language Models (LLMs) into existing enterprise infrastructure presents a significant challenge. Organizations face a dilemma: they need the cutting-edge capabilities of modern LLMs, but their existing systems may not easily accommodate the Python ecosystem where most LLM advancements occur.

This article explores a practical solution to this challenge: using AWS Lambda functions as a bridge between your existing infrastructure and Python-based LLM capabilities. We'll cover the technical details of building, deploying, and consuming a serverless LLM API that can process various document types while minimizing impact on your current systems.

## The Integration Challenge

Enterprise systems often run on established platforms like Java, .NET, or legacy systems that may not easily integrate with Python-based LLM libraries. However, Python has become the de facto standard for AI development due to:

1. **Rapid innovation**: Most cutting-edge LLM libraries appear first in Python
2. **Rich ecosystem**: Tools like LangChain, LlamaIndex, and instructor-embedding are Python-first
3. **Direct model access**: Python SDKs for OpenAI, Anthropic, and other providers are more mature
4. **Community support**: The AI community primarily shares solutions in Python

Rather than rewriting existing systems or waiting for LLM libraries to mature in other languages, AWS Lambda offers an elegant solution:

![LLM Lambda Architecture](https://mermaid.ink/img/pako:eNqNkk9rwzAMxb-K0E4dJPuXXXJoSw87lA2G2tMYwrZSG5rYwXYGpfS7z06zoWSF7WRL0k9683Rh0gqgHpfcbDQb1ZYXHnrIy4Kh4GWdjkk2oe46d4w36fHrJXBcRxNGIyIY1yDyBCZJkkzJpWVBXDPnQRvLZWVRPChHEr6xljK5cCiZ96iEcn3qSbfOaJpNkN-BJ3sxiOEi_b5B2Pt_yrxC6PAFVx2uScMhQ2tIOkEOEXQtRrlwxtA7l1h_5r90mfaywDUUZm9dURsU1JN2Y4w15A5ZGnlB4q0yRZPMfjCYZPEkDSSUzhrV0hLUgO44SXFCwDzXtpchY1HO47EYUW82m_mMumaF1uDG8ylnHr2BHNP9SdWCejgUVlU3aJm3qCKjPcXJBxXcr-AXvWfSag?type=png)

## Building a Serverless LLM Document Processor

Let's create a Python-based LLM service on AWS Lambda that can:

1. Process various document types (JSON, images, PDFs)
2. Apply LLM capabilities for analysis
3. Return structured responses
4. Offer a secure, scalable HTTP API endpoint

### Project Structure

Our project follows this structure:

```
.
├── src/
│   ├── lambda_functions/        # AWS Lambda function implementations
│   │   └── document_processor/  # Document processing function
│   ├── utils/                   # Shared utility modules
│   └── config/                  # Configuration modules
├── scripts/                     # Deployment and utility scripts
├── terraform/                   # Infrastructure as code
├── examples/                    # Example usage scripts
├── Dockerfile                   # Container definition for Lambda
└── lambda_entry.py              # Local Lambda testing script
```

### Setting Up the FastAPI App

We'll use FastAPI to create a web service that AWS Lambda can run. This approach gives us the best of both worlds:

1. Local development using standard web frameworks
2. Serverless deployment through AWS Lambda

Here's our main application file (`src/lambda_functions/document_processor/app.py`):

```python
"""
FastAPI app for local development and Lambda deployment.
"""

import json
import sys
import os

# Add parent directories to Python path for proper imports
current_dir = os.path.dirname(os.path.abspath(__file__))
lambda_functions_dir = os.path.dirname(os.path.dirname(current_dir))
src_dir = os.path.dirname(lambda_functions_dir)
root_dir = os.path.dirname(src_dir)

# Add directories to Python path if not already there
for directory in [current_dir, lambda_functions_dir, src_dir, root_dir]:
    if directory not in sys.path:
        sys.path.insert(0, directory)

# Import application components
try:
    from fastapi import FastAPI, HTTPException, Request
    from mangum import Mangum

    from src.lambda_functions.document_processor.models import (
        DocumentProcessRequest,
        DocumentProcessResponse
    )
    from src.lambda_functions.document_processor.processor import DocumentProcessor
    from src.lambda_functions.document_processor.handler import lambda_handler

    # Create FastAPI app
    app = FastAPI(
        title="Document Processor API",
        description="API for processing documents with LLM",
        version="0.1.0"
    )

    @app.get("/")
    async def root():
        return {"message": "Document Processor API is running"}

    @app.post("/process", response_model=DocumentProcessResponse)
    async def process_document(request: DocumentProcessRequest):
        """
        Process a document with LLM and return structured analysis.
        """
        processor = DocumentProcessor(request)
        response = processor.process()
        
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error_message)
        
        return response

    # Create a wrapper function that can handle multiple event types
    def universal_handler(event, context):
        """Wrapper handler that can process different event types."""
        try:
            # Check if the event is a direct invocation with document data
            if "document_data" in event and "instructions" in event:
                request = DocumentProcessRequest(**event)
                processor = DocumentProcessor(request)
                response = processor.process()
                return {
                    "statusCode": 200 if response.success else 500,
                    "body": json.dumps(response.dict())
                }
            
            # Check if this is API Gateway 1.0 format
            if "httpMethod" in event and "body" in event:
                return lambda_handler(event, context)
                
            # Default to Mangum for API Gateway v2
            mangum_handler = Mangum(app)
            return mangum_handler(event, context)
            
        except Exception as e:
            import traceback
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
            }

    # Use the universal handler
    handler = universal_handler
    
except ImportError as e:
    # Simple fallback handler if imports fail
    def handler(event, context):
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"Failed to initialize Lambda: {str(e)}"
            })
        }
```

This sets up a FastAPI application with a `/process` endpoint that accepts document data and returns structured LLM analysis.

### Document Processing Models

Let's define the data models to handle document processing requests and responses:

```python
# src/lambda_functions/document_processor/models.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union

class DocumentProcessRequest(BaseModel):
    """Request model for document processing."""
    document_data: str = Field(..., description="Document data (base64-encoded for binary formats)")
    document_type: Optional[str] = Field("json", description="Document type (json, image, pdf)")
    llm_provider: Optional[str] = Field("openai", description="LLM provider to use")
    instructions: str = Field(..., description="Processing instructions for the LLM")

class TextAnnotation(BaseModel):
    """Text annotation from document processing."""
    type: str
    content: str

class EntityAnnotation(BaseModel):
    """Entity annotation from document processing."""
    entity_type: str
    name: str
    value: Any

class DocumentSummary(BaseModel):
    """Document summary."""
    title: str
    content: str

class ProcessResult(BaseModel):
    """Result of document processing."""
    summary: DocumentSummary
    text_annotations: List[TextAnnotation] = []
    entity_annotations: List[EntityAnnotation] = []

class DocumentProcessResponse(BaseModel):
    """Response model for document processing."""
    request_id: str
    success: bool = True
    error_message: Optional[str] = None
    result: Optional[ProcessResult] = None
```

### The Document Processor

Now, let's create the processor that will use LLMs to analyze documents:

```python
# src/lambda_functions/document_processor/processor.py
import uuid
import json
import base64
from typing import Optional

from src.lambda_functions.document_processor.models import (
    DocumentProcessRequest,
    DocumentProcessResponse,
    ProcessResult,
    DocumentSummary,
    TextAnnotation,
    EntityAnnotation
)
from src.utils.llm_client import LLMClient

class DocumentProcessor:
    """Processes documents with LLM and returns structured analysis."""
    
    def __init__(self, request: DocumentProcessRequest):
        self.request = request
        self.request_id = str(uuid.uuid4())
        self.llm_client = LLMClient(provider=request.llm_provider)
    
    def process(self) -> DocumentProcessResponse:
        """Process the document and return a structured response."""
        try:
            # Decode document data based on type
            document = self._decode_document()
            
            # Process with LLM
            llm_response = self.llm_client.process_document(
                document=document,
                doc_type=self.request.document_type,
                instructions=self.request.instructions
            )
            
            # Parse LLM response into structured output
            result = self._parse_llm_response(llm_response)
            
            return DocumentProcessResponse(
                request_id=self.request_id,
                success=True,
                result=result
            )
        except Exception as e:
            return DocumentProcessResponse(
                request_id=self.request_id,
                success=False,
                error_message=str(e)
            )
    
    def _decode_document(self):
        """Decode document data based on type."""
        if self.request.document_type == "json":
            return json.loads(self.request.document_data)
        elif self.request.document_type in ["image", "pdf"]:
            return base64.b64decode(self.request.document_data)
        else:
            return self.request.document_data
            
    def _parse_llm_response(self, llm_response: dict) -> ProcessResult:
        """Parse LLM response into structured output."""
        # Example implementation - in a real app, you would parse 
        # the actual LLM response based on your schema
        return ProcessResult(
            summary=DocumentSummary(
                title=llm_response.get("title", "Document Analysis"),
                content=llm_response.get("summary", "")
            ),
            text_annotations=[
                TextAnnotation(type=item["type"], content=item["content"])
                for item in llm_response.get("annotations", [])
            ],
            entity_annotations=[
                EntityAnnotation(
                    entity_type=entity["type"],
                    name=entity["name"],
                    value=entity["value"]
                )
                for entity in llm_response.get("entities", [])
            ]
        )
```

### Containerizing the Lambda Function

Using Docker containers for Lambda deployment simplifies dependency management. Here's our `Dockerfile`:

```dockerfile
FROM public.ecr.aws/lambda/python:3.10

# Copy source code
COPY src/ ${LAMBDA_TASK_ROOT}/src/

# Copy requirements and test scripts
COPY requirements.txt lambda_entry.py ${LAMBDA_TASK_ROOT}/

# Install dependencies in the proper structure for Lambda
RUN pip install -r requirements.txt --target ${LAMBDA_TASK_ROOT}/

# Install specific dependencies that might be causing issues
RUN pip install \
    fastapi==0.100.0 \
    mangum==0.17.0 \
    pydantic==2.4.0 \
    pydantic-core==2.10.0 \
    starlette==0.27.0 \
    --target ${LAMBDA_TASK_ROOT}/

# Set the PYTHONPATH (for local testing)
ENV PYTHONPATH=${LAMBDA_TASK_ROOT}

# Set the handler
CMD [ "src.lambda_functions.document_processor.app.handler" ]
```

## Deploying the Solution

We'll use a comprehensive deployment script to handle the entire process:

```powershell
# scripts/deploy.ps1
param (
    [Parameter(Mandatory = $false)]
    [string]$AwsProfile = "default",
    
    [Parameter(Mandatory = $false)]
    [string]$AwsRegion = "us-east-1",
    
    [Parameter(Mandatory = $false)]
    [string]$RepositoryName = "document-processor",
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipImageBuild = $false,
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipEcr = $false,
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipTerraform = $false
)

# Function to display section headers
function Write-Header {
    param ([string]$Text)
    Write-Host "`n=== $Text ===`n" -ForegroundColor Cyan
}

# Set AWS profile and verify credentials
$env:AWS_PROFILE = $AwsProfile
$awsAccount = aws sts get-caller-identity --query "Account" --output text

# Create or verify ECR repository if not skipped
if (-not $SkipEcr) {
    Write-Header "Setting Up ECR Repository"
    # Check if repository exists, create if it doesn't
    # ... (repository creation logic)
}

# Build and push Docker image if not skipped
if (-not $SkipImageBuild) {
    Write-Header "Building Docker Image"
    docker build -t $RepositoryName . --no-cache
    
    # Tag with timestamp and 'latest'
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $imageUri = "${awsAccount}.dkr.ecr.${AwsRegion}.amazonaws.com/${RepositoryName}:${timestamp}"
    $latestImageUri = "${awsAccount}.dkr.ecr.${AwsRegion}.amazonaws.com/${RepositoryName}:latest"
    
    docker tag $RepositoryName $imageUri
    docker tag $RepositoryName $latestImageUri
    
    # Push to ECR
    docker push $imageUri
    docker push $latestImageUri
    
    # Create Terraform variables file
    $terraformVars = @"
# Auto-generated by deploy.ps1
container_image_uri = "$imageUri"
aws_profile = "$AwsProfile"
aws_region = "$AwsRegion"
api_stage = "dev"
"@
    
    Set-Content -Path "terraform/terraform.tfvars" -Value $terraformVars
}

# Deploy with Terraform if not skipped
if (-not $SkipTerraform) {
    Write-Header "Deploying with Terraform"
    
    Push-Location terraform
    terraform init
    terraform plan -out="tf-plan"
    terraform apply "tf-plan"
    Pop-Location
}
```

### Infrastructure as Code with Terraform

Our Terraform code provisions the AWS resources needed:

```hcl
# terraform/main.tf
variable "container_image_uri" {
  description = "ECR image URI for the Lambda function"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS profile"
  type        = string
  default     = "default"
}

variable "api_stage" {
  description = "API Gateway stage name"
  type        = string
  default     = "dev"
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

# Create Lambda function
resource "aws_lambda_function" "document_processor" {
  function_name = "document-processor"
  package_type  = "Image"
  image_uri     = var.container_image_uri
  
  timeout     = 30
  memory_size = 1024
  
  role = aws_iam_role.lambda_exec.arn
  
  environment {
    variables = {
      ENVIRONMENT = var.api_stage
    }
  }
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_exec" {
  name = "document-processor-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Effect = "Allow"
      }
    ]
  })
}

# Attach policies to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "secrets_manager_read" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.secrets_manager_read.arn
}

# Policy for reading from Secrets Manager
resource "aws_iam_policy" "secrets_manager_read" {
  name        = "document-processor-secrets-read"
  description = "Allow Lambda to read API keys from Secrets Manager"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue",
        ]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:*:secret:llm-utilities/api-keys*"
        Effect   = "Allow"
      }
    ]
  })
}

# API Gateway REST API
resource "aws_apigatewayv2_api" "api" {
  name          = "document-processor-api"
  protocol_type = "HTTP"
}

# API Gateway stage
resource "aws_apigatewayv2_stage" "stage" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = var.api_stage
  auto_deploy = true
}

# API Gateway Lambda integration
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  
  integration_uri    = aws_lambda_function.document_processor.invoke_arn
  integration_method = "POST"
  payload_format_version = "2.0"
}

# API Gateway routes
resource "aws_apigatewayv2_route" "route" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "ANY /{proxy+}"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.document_processor.function_name
  principal     = "apigateway.amazonaws.com"
  
  source_arn = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

# Output API endpoint
output "api_endpoint" {
  value = "${aws_apigatewayv2_stage.stage.invoke_url}"
}
```

## Testing and Using the API

Once deployed, we can test our Lambda-based API:

```python
# examples/test_document_processor.py
import requests
import json
import base64
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Test the document processor API")
    parser.add_argument("--api-url", required=True, help="API Gateway URL")
    parser.add_argument("--test-type", choices=["json", "image", "pdf"], default="json",
                      help="Type of test to run (default: json)")
    return parser.parse_args()

def test_json_processing(api_url):
    # Example JSON data
    test_data = {
        "customer": {
            "id": "C1234",
            "name": "Jane Smith"
        },
        "order": {
            "items": [
                {"product": "Laptop", "price": 1299.99},
                {"product": "Mouse", "price": 24.99}
            ],
            "total": 1324.98
        }
    }
    
    # Prepare the request payload
    payload = {
        "document_data": json.dumps(test_data),
        "document_type": "json",
        "instructions": "Extract the customer name, order total, and list of products purchased."
    }
    
    # Send the request
    response = requests.post(f"{api_url}/process", json=payload)
    
    # Print response
    print(f"\nStatus Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.text}")

def main():
    args = parse_args()
    
    if args.test_type == "json":
        test_json_processing(args.api_url)
    # Additional handlers for image and PDF processing

if __name__ == "__main__":
    main()
```

To run the test:

```powershell
# Get the API endpoint
$apiEndpoint = ./scripts/get_api_endpoint.ps1 -AwsProfile your-profile-name

# Test JSON document processing
python examples/test_document_processor.py --api-url $apiEndpoint --test-type json
```

## Benefits of This Approach

This Lambda-based architecture offers several advantages:

1. **Clean separation**: Your existing infrastructure remains untouched
2. **Python ecosystem access**: Use the latest LLM libraries and techniques
3. **Scalability**: AWS Lambda auto-scales based on usage
4. **Cost-effectiveness**: Pay only for what you use
5. **Security**: API keys are stored securely in AWS Secrets Manager
6. **Infrastructure as code**: Terraform ensures consistent deployments
7. **Containerization**: Docker simplifies dependency management

## Integration with Existing Systems

Existing applications can easily consume the API in any language:

```java
// Java example
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class LambdaApiClient {
    private final String apiUrl;
    private final HttpClient client;
    
    public LambdaApiClient(String apiUrl) {
        this.apiUrl = apiUrl;
        this.client = HttpClient.newHttpClient();
    }
    
    public String processDocument(String documentData, String instructions) throws Exception {
        String payload = String.format(
            "{\"document_data\":%s,\"document_type\":\"json\",\"instructions\":\"%s\"}",
            documentData, instructions
        );
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(apiUrl + "/process"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(payload))
            .build();
            
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() != 200) {
            throw new RuntimeException("API request failed: " + response.body());
        }
        
        return response.body();
    }
}
```

## Conclusion and Future Directions

This approach lets you harness the power of Python-based LLMs in any enterprise environment through AWS Lambda functions. By creating a clean API boundary, you decouple your LLM implementation from existing systems while providing a stable interface for integration.

In future articles, we'll explore:

1. **Java-based LLM applications**: Approaches to building LLM applications directly in Java
2. **Monitoring LLM services**: Implementing effective monitoring and logging 
3. **Evaluation frameworks**: Building systematic evaluation pipelines for LLM-based systems
4. **Cost optimization**: Strategies to minimize costs in production LLM deployments

The complete code for this solution is available in our [GitHub repository](https://github.com/yourusername/llm-lambda-api).

---

By leveraging the serverless paradigm, we can introduce powerful LLM capabilities to legacy systems without disrupting existing workflows or requiring major rewrites. This pragmatic approach enables organizations to benefit from the latest AI advancements regardless of their current technology stack. 