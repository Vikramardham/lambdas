# Project Memory Bank - LLM Utilities API

## Project Overview
- Building serverless LLM utilities deployed on AWS Lambda
- First application: Document processor that handles images, PDFs, and JSON
- Uses Instructor with LiteLLM for structured outputs from LLMs

## Key Components

### Configuration Management
- Secure API key handling using environment variables and AWS Secrets Manager
- Configuration abstraction to support multiple LLM providers
- Default models configurable through environment variables

### LLM Client
- Instructor integration with LiteLLM for structured outputs
- Support for different LLM providers (OpenAI, Anthropic, Cohere)
- Type-safe response generation using Pydantic schemas

### Document Processing
- Document type detection and parsing for various formats
- Structured document analysis with text and entity extraction
- Summary generation for processed documents

### API Interface
- Lambda handler for AWS API Gateway integration
- FastAPI interface for local testing and development
- Error handling and validation using Pydantic models

## Development Progress

### Initial Setup (Done)
- [x] Project structure established
- [x] Core dependencies identified and configured
- [x] Basic utility modules created

### Document Processor (Done)
- [x] Support for image, PDF, and JSON parsing
- [x] LLM integration for document analysis
- [x] Pydantic models for structured I/O

### AWS Integration (To Do)
- [ ] Lambda packaging script
- [ ] Deployment template for AWS
- [ ] CI/CD setup

### Testing (In Progress)
- [x] Basic unit tests
- [ ] Integration tests
- [ ] Performance testing

## Technical Decisions

### Using Instructor with LiteLLM
- Rationale: Combining Instructor's structured output capabilities with LiteLLM's provider flexibility
- Benefit: Can easily switch between different LLM providers without changing code

### FastAPI for Local Development
- Provides an easy way to test the API locally before deploying to AWS
- Mangum integration allows the same code to be used for both local and Lambda

### Secure Credential Management
- Multi-layered approach using both environment variables and AWS Secrets Manager
- Ensures development environments and production deployments follow security best practices

## Learnings

### Best Practices
- Using Pydantic for request/response validation simplifies API development
- Structured logging is essential for Lambda function debugging
- Clear separation between business logic and interface code improves maintainability

### Challenges
- Managing binary data (images, PDFs) in serverless environments requires careful handling
- Lambda cold start times can be impacted by large dependencies
- Balancing between comprehensive error handling and code simplicity

## Next Steps
1. Complete AWS deployment configuration
2. Add more tests for different document types
3. Consider adding a caching layer for improved performance
4. Implement additional Lambda functions for other LLM utilities

## Dependency Management

### UV Dependency Management
- Using UV package manager for Python dependencies due to its speed and reliability
- UV is faster and more reliable than pip for managing dependencies
- Used in both development and container environments for consistency
- In the Dockerfile, UV is installed and then used to install requirements
- Used with the `--system` flag in Docker to ensure dependencies are installed at the system level

### Dependencies Organization
- Grouped dependencies by function in requirements.txt
- Added explicit dependencies for underlying packages to avoid compatibility issues
- Included pydantic-core to avoid the Import Error experienced with Lambda

## Deployment Process

### AWS ECR and Container Deployment
- Created a PowerShell script (`manual_push.ps1`) to manually push Docker images to Amazon ECR
- The script handles:
  - AWS authentication
  - Repository existence verification
  - Docker image building with UV package manager
  - Image pushing to ECR
  - Terraform variable file generation for subsequent deployment

### Infrastructure as Code
- Using Terraform for infrastructure provisioning
- The deployment process is split into two main steps:
  1. Container image creation and ECR pushing
  2. Terraform deployment of AWS resources (Lambda, API Gateway, etc.)
- Using data sources instead of resources for existing AWS resources (like Secrets Manager)

### Security Considerations
- API keys for LLM services (OpenAI, Anthropic, Cohere, Gemini) are stored in AWS Secrets Manager
- Access controls managed through AWS IAM
- Container security implemented through Docker best practices

## Project Structure
- `/scripts` - Contains deployment and utility scripts
- `/terraform` - Infrastructure as code definitions
- `/docs` - Project documentation including troubleshooting guides

## Best Practices Implemented
- Parameterized scripts with default values for flexibility
- Comprehensive error handling in deployment scripts
- Clear documentation with step-by-step instructions
- Containerization for consistent deployment environments
- Terraform for reproducible infrastructure

## Future Improvements
- Implement CI/CD pipeline for automated deployments
- Add monitoring and logging infrastructure
- Create development/staging/production environment separation 