provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

# Lambda function for document processor
resource "aws_lambda_function" "document_processor" {
  function_name = "document-processor"

  # Container configuration
  package_type = "Image"
  image_uri    = var.container_image_uri

  # Lambda configuration
  timeout     = 30
  memory_size = 1024

  environment {
    variables = {
      DEFAULT_LLM_PROVIDER = var.default_llm_provider
      AWS_SECRET_NAME      = data.aws_secretsmanager_secret.llm_api_keys.name
    }
  }

  role = aws_iam_role.lambda_role.arn

  depends_on = [
    aws_iam_role_policy_attachment.lambda_logs_policy_attachment,
    aws_iam_role_policy_attachment.lambda_secretsmanager_policy_attachment,
    aws_cloudwatch_log_group.document_processor_logs,
  ]
}

# CloudWatch log group for Lambda
resource "aws_cloudwatch_log_group" "document_processor_logs" {
  name              = "/aws/lambda/document-processor"
  retention_in_days = 30
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "document-processor-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for CloudWatch Logs
resource "aws_iam_policy" "lambda_logs_policy" {
  name = "document-processor-lambda-logs-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "${aws_cloudwatch_log_group.document_processor_logs.arn}:*"
      }
    ]
  })
}

# IAM policy attachment for logs
resource "aws_iam_role_policy_attachment" "lambda_logs_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_logs_policy.arn
}

# IAM policy for Secrets Manager
resource "aws_iam_policy" "lambda_secretsmanager_policy" {
  name = "document-processor-lambda-secretsmanager-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Effect   = "Allow"
        Resource = data.aws_secretsmanager_secret.llm_api_keys.arn
      }
    ]
  })
}

# IAM policy attachment for Secrets Manager
resource "aws_iam_role_policy_attachment" "lambda_secretsmanager_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_secretsmanager_policy.arn
}

# Use existing Secrets Manager secret for API keys
data "aws_secretsmanager_secret" "llm_api_keys" {
  name = var.aws_secret_name
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "llm_utilities_api" {
  name        = "llm-utilities-api"
  description = "API for LLM utilities"
}

# API Gateway resource
resource "aws_api_gateway_resource" "document_processor_resource" {
  rest_api_id = aws_api_gateway_rest_api.llm_utilities_api.id
  parent_id   = aws_api_gateway_rest_api.llm_utilities_api.root_resource_id
  path_part   = "process"
}

# API Gateway method
resource "aws_api_gateway_method" "document_processor_method" {
  rest_api_id   = aws_api_gateway_rest_api.llm_utilities_api.id
  resource_id   = aws_api_gateway_resource.document_processor_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

# API Gateway integration
resource "aws_api_gateway_integration" "document_processor_integration" {
  rest_api_id             = aws_api_gateway_rest_api.llm_utilities_api.id
  resource_id             = aws_api_gateway_resource.document_processor_resource.id
  http_method             = aws_api_gateway_method.document_processor_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.document_processor.invoke_arn
}

# API Gateway deployment
resource "aws_api_gateway_deployment" "llm_utilities_deployment" {
  depends_on = [
    aws_api_gateway_integration.document_processor_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.llm_utilities_api.id
  stage_name  = var.api_stage
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.document_processor.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.llm_utilities_api.execution_arn}/*/*"
}
