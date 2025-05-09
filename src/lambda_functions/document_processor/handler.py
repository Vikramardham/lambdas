"""
AWS Lambda handler for document processing API.
"""

import json
import traceback
from typing import Dict, Any

from src.lambda_functions.document_processor.models import (
    DocumentProcessRequest,
    DocumentProcessResponse
)
from src.lambda_functions.document_processor.processor import DocumentProcessor

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for document processing.
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    try:
        # Parse request body
        body = event.get('body')
        if not body:
            return _build_response(400, {"error": "Missing request body"})
        
        # Parse JSON if body is a string
        if isinstance(body, str):
            body = json.loads(body)
        
        # Validate request with Pydantic model
        try:
            request = DocumentProcessRequest(**body)
        except Exception as e:
            return _build_response(400, {"error": f"Invalid request: {str(e)}"})
        
        # Process document
        processor = DocumentProcessor(request)
        response = processor.process()
        
        # Return response
        return _build_response(
            200 if response.success else 500,
            response.dict()
        )
        
    except Exception as e:
        # Log the error
        print(f"Error processing document: {str(e)}")
        traceback.print_exc()
        
        # Return error response
        return _build_response(500, {
            "error": "Internal server error",
            "message": str(e)
        })

def _build_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build Lambda response for API Gateway.
    
    Args:
        status_code: HTTP status code
        body: Response body
        
    Returns:
        API Gateway response
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        },
        "body": json.dumps(body)
    } 