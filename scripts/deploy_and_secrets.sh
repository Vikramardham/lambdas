#!/usr/bin/env bash

# This script sets up AWS Secrets Manager and deploys the Lambda (builds Docker image, pushes to ECR, runs Terraform)
# Usage: ./deploy_and_secrets.sh <aws_profile> <aws_region>

set -euo pipefail

AWS_PROFILE=${1:-vikram-admin}
AWS_REGION=${2:-us-east-1}
REPOSITORY_NAME="document-processor"
IMAGE_TAG="latest"
SECRET_NAME="llm-utilities/api-keys"

# Read API keys from environment variables
OPENAI_KEY="${OPENAI_API_KEY:-}"
ANTHROPIC_KEY="${ANTHROPIC_API_KEY:-}"
COHERE_KEY="${COHERE_API_KEY:-}"
GEMINI_KEY="${GEMINI_API_KEY:-}"

missing=()
if [[ -z "$OPENAI_KEY" ]]; then
  missing+=("OPENAI_API_KEY")
fi
if [[ -z "$ANTHROPIC_KEY" ]]; then
  missing+=("ANTHROPIC_API_KEY")
fi
if [[ -z "$COHERE_KEY" ]]; then
  missing+=("COHERE_API_KEY")
fi
if [[ -z "$GEMINI_KEY" ]]; then
  missing+=("GEMINI_API_KEY")
fi

if [[ ${#missing[@]} -eq 4 ]]; then
  echo "Error: None of the required API keys are set in the environment."
  echo "Please set at least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, COHERE_API_KEY, GEMINI_API_KEY."
  exit 1
elif [[ ${#missing[@]} -gt 0 ]]; then
  echo "Warning: The following API keys are not set: ${missing[*]}"
fi

export AWS_PROFILE
export AWS_REGION

echo "\n=== Setting up AWS Secrets Manager ==="
SECRET_STRING="{\"OPENAI_API_KEY\":\"$OPENAI_KEY\",\"ANTHROPIC_API_KEY\":\"$ANTHROPIC_KEY\",\"COHERE_API_KEY\":\"$COHERE_KEY\",\"GEMINI_API_KEY\":\"$GEMINI_KEY\"}"

if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" >/dev/null 2>&1; then
  echo "Updating existing secret: $SECRET_NAME"
  aws secretsmanager put-secret-value --secret-id "$SECRET_NAME" --secret-string "$SECRET_STRING"
else
  echo "Creating new secret: $SECRET_NAME"
  aws secretsmanager create-secret --name "$SECRET_NAME" --secret-string "$SECRET_STRING"
fi

echo "\n=== Building and Pushing Docker Image ==="
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME"

if ! aws ecr describe-repositories --repository-names "$REPOSITORY_NAME" >/dev/null 2>&1; then
  echo "Creating ECR repository: $REPOSITORY_NAME"
  aws ecr create-repository --repository-name "$REPOSITORY_NAME"
fi

echo "Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_URI"

echo "Building Docker image..."
docker build -t "$REPOSITORY_NAME" .

echo "Tagging Docker image..."
docker tag "$REPOSITORY_NAME" "$ECR_URI:$IMAGE_TAG"

echo "Pushing Docker image to ECR..."
docker push "$ECR_URI:$IMAGE_TAG"

# Optionally, tag with timestamp for versioning
timestamp=$(date +%Y%m%d-%H%M%S)
docker tag "$REPOSITORY_NAME" "$ECR_URI:$timestamp"
docker push "$ECR_URI:$timestamp"

# Update terraform.tfvars with the new image URI
cat > terraform/terraform.tfvars <<EOF
container_image_uri = "$ECR_URI:$timestamp"
aws_profile = "$AWS_PROFILE"
aws_region = "$AWS_REGION"
api_stage = "dev"
EOF

echo "\n=== Deploying Infrastructure with Terraform ==="
cd terraform
terraform init
terraform apply -auto-approve
cd ..

echo "\nDeployment complete!"
echo "You can get the API endpoint with: ./scripts/get_api_endpoint.ps1 -AwsProfile $AWS_PROFILE" 