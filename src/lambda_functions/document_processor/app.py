"""
FastAPI app for local development and Lambda deployment.
"""

import json
import sys
import os

# Add parent directories to Python path
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

    @app.post("/lambda-proxy")
    async def lambda_proxy(request: Request):
        """
        Proxy endpoint that simulates AWS Lambda + API Gateway for testing.
        """
        # Get request body
        body = await request.json()
        
        # Create Lambda event
        event = {
            "body": json.dumps(body),
            "headers": dict(request.headers),
            "httpMethod": "POST",
            "path": "/process"
        }
        
        # Call Lambda handler
        response = lambda_handler(event, None)
        
        # Parse response
        status_code = response["statusCode"]
        body = json.loads(response["body"])
        
        # Return response
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=body.get("error", "Unknown error"))
        
        return body

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
            
            # Check if this is API Gateway 1.0 format or direct test invocation
            if "httpMethod" in event and "body" in event:
                return lambda_handler(event, context)
                
            # Default to Mangum for API Gateway v2 and proper API calls
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

    handler = universal_handler
    
except ImportError as e:
    def handler(event, context):
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"Failed to initialize Lambda: ImportError"
            })
        } 