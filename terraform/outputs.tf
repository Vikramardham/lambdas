output "lambda_function_name" {
  description = "Name of the deployed Lambda function"
  value       = aws_lambda_function.document_processor.function_name
}

output "api_gateway_url" {
  description = "URL of the deployed API Gateway"
  value       = "${aws_api_gateway_deployment.llm_utilities_deployment.invoke_url}${aws_api_gateway_resource.document_processor_resource.path}"
}

output "api_endpoint" {
  description = "Full API endpoint URL"
  value       = "${aws_api_gateway_deployment.llm_utilities_deployment.invoke_url}${var.api_stage}/${aws_api_gateway_resource.document_processor_resource.path_part}"
}

output "aws_secret_name" {
  description = "Name of the AWS Secrets Manager secret for API keys"
  value       = data.aws_secretsmanager_secret.llm_api_keys.name
}
