# Troubleshooting Guide

This document provides solutions for common issues you might encounter when deploying the LLM Utilities API.

## Docker Issues

### Docker Desktop Not Running

**Symptoms:**
- "Cannot connect to the Docker daemon" error
- "Error during connect" messages

**Solutions:**
1. Make sure Docker Desktop is installed and running
2. Check Docker Desktop status in system tray
3. Restart Docker Desktop
4. Ensure WSL 2 backend is properly configured (Windows)

### WSL 2 Configuration (Windows)

If you see errors about Docker pipe connections:

```
ERROR: error during connect: Head "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/_ping": open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```

**Solutions:**
1. Enable WSL 2 in Windows features
   ```powershell
   wsl --install
   ```

2. Make sure Docker Desktop is set to use WSL 2 backend
   - Open Docker Desktop settings
   - Go to Resources → WSL Integration
   - Enable "Use the WSL 2 based engine"

3. Restart Docker Desktop and your computer

## AWS ECR Issues

### Image Not Found

**Symptoms:**
- "Source image does not exist" error in Terraform
- "The repository with name does not exist" errors

**Solutions:**
1. Verify ECR repository exists:
   ```bash
   aws ecr describe-repositories --repository-names document-processor
   ```

2. Check if image was pushed correctly:
   ```bash
   aws ecr describe-images --repository-name document-processor
   ```

3. Manually push the image:
   ```bash
   aws ecr get-login-password | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
   docker build -t document-processor .
   docker tag document-processor $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/document-processor:latest
   docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/document-processor:latest
   ```

### AWS Credentials Issues

**Symptoms:**
- "Access denied" errors
- Authentication failures

**Solutions:**
1. Verify your credentials are correct:
   ```bash
   aws sts get-caller-identity --profile your-profile-name
   ```

2. Make sure your user has the required permissions:
   - Amazon ECR permissions (ecr:*)
   - Lambda permissions (lambda:*)
   - IAM permissions (iam:CreateRole, etc.)
   - Secrets Manager permissions (secretsmanager:*)
   - API Gateway permissions (apigateway:*)

3. If using temporary credentials, ensure they haven't expired

## Lambda and API Gateway Issues

### Missing Dependencies

**Symptoms:**
- "No module named x" errors in Lambda logs
- Lambda function crashes on startup

**Solutions:**
1. Check the Dockerfile to ensure all dependencies are included
2. Make sure the requirements.txt file contains all needed packages
3. Test the container locally before deploying:
   ```bash
   docker build -t document-processor-local-test .
   docker run -p 9000:8080 document-processor-local-test
   ```

### API Gateway Integration Issues

**Symptoms:**
- API returns 5xx errors
- "Internal server error" responses

**Solutions:**
1. Check Lambda CloudWatch logs for errors:
   ```bash
   aws logs get-log-events --log-group-name /aws/lambda/document-processor --log-stream-name <latest-stream>
   ```

2. Test the Lambda function directly:
   ```bash
   aws lambda invoke --function-name document-processor --payload '{"body": "{\"document_data\": \"{}\", \"instructions\": \"test\"}"}'  output.json
   ```

3. Ensure API Gateway has permission to invoke Lambda

## General Troubleshooting Steps

1. **Check logs**: Always start by checking CloudWatch logs
2. **Verify resources**: Make sure all required AWS resources exist
3. **Test locally**: Try running the container locally before deploying
4. **Incremental testing**: Test each component separately (Docker → ECR → Lambda → API Gateway)
5. **Clean and redeploy**: Sometimes removing resources and redeploying can fix issues:
   ```bash
   terraform destroy
   ./scripts/container_deploy.ps1 -AwsProfile your-profile-name
   ``` 