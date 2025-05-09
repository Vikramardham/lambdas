"""
Tests for document processor Lambda function.
"""

import json
import base64
import pytest
from unittest.mock import patch, MagicMock, ANY

from src.lambda_functions.document_processor.models import (
    DocumentProcessRequest,
    DocumentProcessResponse,
    DocumentType,
    DocumentAnalysisResult,
    TextAnnotation,
    EntityAnnotation,
    SummaryAnnotation
)
from src.lambda_functions.document_processor.processor import DocumentProcessor
from src.lambda_functions.document_processor.handler import lambda_handler
from src.utils.llm_client import LLMClient

# Sample test data
SAMPLE_JSON = {
    "name": "John Doe",
    "age": 35,
    "email": "john.doe@example.com",
    "address": {
        "street": "123 Main St",
        "city": "Anytown",
        "zipcode": "12345"
    }
}

SAMPLE_JSON_B64 = base64.b64encode(json.dumps(SAMPLE_JSON).encode()).decode()

# Mock LLM response for testing
MOCK_LLM_RESPONSE = {
    "document_type": "json",
    "metadata": {"keys": ["name", "age", "email", "address"], "size": 4},
    "text_annotations": [
        {"text": "John Doe", "relevance_score": 0.9},
        {"text": "john.doe@example.com", "relevance_score": 0.8}
    ],
    "entity_annotations": [
        {"entity_type": "person", "value": "John Doe", "confidence": 0.95},
        {"entity_type": "email", "value": "john.doe@example.com", "confidence": 0.99},
        {"entity_type": "age", "value": "35", "confidence": 0.9, "normalized_value": 35}
    ],
    "summary": {
        "summary": "Contact information for John Doe, a 35-year-old living in Anytown.",
        "key_points": ["John Doe is 35 years old", "Lives at 123 Main St in Anytown"]
    }
}


@pytest.fixture
def mock_llm_client():
    """Fixture to mock LLM client."""
    with patch('src.lambda_functions.document_processor.processor.LLMClient') as mock_client:
        mock_instance = MagicMock()
        mock_instance.generate_structured_output.return_value = DocumentAnalysisResult(**MOCK_LLM_RESPONSE)
        mock_client.return_value = mock_instance
        yield mock_client


def test_document_processor_with_json(mock_llm_client):
    """Test document processor with JSON input."""
    # Create request
    request = DocumentProcessRequest(
        document_data=json.dumps(SAMPLE_JSON),
        document_type=DocumentType.JSON,
        instructions="Extract contact information."
    )
    
    # Process document
    processor = DocumentProcessor(request)
    response = processor.process()
    
    # Verify response
    assert response.success is True
    assert response.result.document_type == DocumentType.JSON
    assert len(response.result.text_annotations) == 2
    assert len(response.result.entity_annotations) == 3
    assert response.result.summary.summary == "Contact information for John Doe, a 35-year-old living in Anytown."


def test_json_auto_detection(mock_llm_client):
    """Test document processor with auto detection of JSON."""
    # Create request without specifying document type
    request = DocumentProcessRequest(
        document_data=json.dumps(SAMPLE_JSON),
        instructions="Extract contact information."
    )
    
    # Process document
    processor = DocumentProcessor(request)
    response = processor.process()
    
    # Verify response
    assert response.success is True
    assert response.result.document_type == DocumentType.JSON
    
    # Verify that the correct document type was detected
    mock_llm_client.return_value.generate_structured_output.assert_called_once()
    
    # Get the prompt from the call arguments
    # Mock function was called with positional arguments (schema, prompt, system_prompt)
    args, kwargs = mock_llm_client.return_value.generate_structured_output.call_args
    
    # If called with positional args, the prompt should be the second argument
    # If called with kwargs, it should be in the kwargs
    if args and len(args) >= 2:
        prompt = args[1]  # Second positional argument
    else:
        prompt = kwargs.get('prompt', '')
    
    # Verify prompt content
    assert "JSON content:" in prompt
    assert any(key in prompt for key in SAMPLE_JSON.keys())  # Check for JSON keys in prompt


def test_processor_builds_proper_prompt():
    """Test that the processor builds a proper prompt for the LLM."""
    with patch('src.lambda_functions.document_processor.processor.LLMClient'):
        request = DocumentProcessRequest(
            document_data=json.dumps(SAMPLE_JSON),
            document_type=DocumentType.JSON,
            instructions="Extract contact information."
        )
        
        processor = DocumentProcessor(request)
        
        # Test _build_prompt method directly
        parsed_doc = {"name": "John Doe", "age": 35}
        prompt = processor._build_prompt(parsed_doc, DocumentType.JSON)
        
        # Verify prompt structure
        assert "# Document Analysis Task" in prompt
        assert "## Instructions\nExtract contact information." in prompt
        assert "## Document Type\njson" in prompt
        assert "JSON content:" in prompt
        assert "John Doe" in prompt


def test_processor_extracts_correct_metadata():
    """Test that the processor extracts correct metadata."""
    with patch('src.lambda_functions.document_processor.processor.LLMClient'):
        request = DocumentProcessRequest(
            document_data=json.dumps(SAMPLE_JSON),
            document_type=DocumentType.JSON,
            instructions="Extract contact information."
        )
        
        processor = DocumentProcessor(request)
        
        # Test metadata extraction for different document types
        json_data = {"name": "John", "age": 30}
        json_metadata = processor._extract_metadata(json_data, DocumentType.JSON)
        assert set(json_metadata["keys"]) == {"name", "age"}
        assert json_metadata["size"] == 2
        
        pdf_data = {"page_count": 3, "metadata": {"author": "Someone"}}
        pdf_metadata = processor._extract_metadata(pdf_data, DocumentType.PDF)
        assert pdf_metadata["page_count"] == 3
        assert pdf_metadata["metadata"]["author"] == "Someone"
        
        image_data = {"image_type": "JPEG", "width": 800, "height": 600, "mode": "RGB"}
        image_metadata = processor._extract_metadata(image_data, DocumentType.IMAGE)
        assert image_metadata["image_type"] == "JPEG"
        assert image_metadata["width"] == 800
        assert image_metadata["height"] == 600


def test_processor_error_handling():
    """Test error handling in the processor."""
    # Test with invalid JSON
    request = DocumentProcessRequest(
        document_data="invalid-json",
        document_type=DocumentType.JSON,
        instructions="Extract contact information."
    )
    
    processor = DocumentProcessor(request)
    response = processor.process()
    
    # Verify error response
    assert response.success is False
    assert response.error_message is not None


def test_processor_with_different_llm_provider(mock_llm_client):
    """Test processor with different LLM provider."""
    # Create request with specific LLM provider
    request = DocumentProcessRequest(
        document_data=json.dumps(SAMPLE_JSON),
        document_type=DocumentType.JSON,
        instructions="Extract contact information.",
        llm_provider="anthropic"
    )
    
    # Process document
    processor = DocumentProcessor(request)
    processor.process()
    
    # Verify LLM client was initialized with correct provider
    mock_llm_client.assert_called_once_with(provider="anthropic")


def test_lambda_handler():
    """Test Lambda handler function."""
    with patch('src.lambda_functions.document_processor.processor.DocumentProcessor') as mock_processor:
        # Mock processor
        mock_instance = MagicMock()
        mock_instance.process.return_value = DocumentProcessResponse(
            request_id="test-id",
            success=True,
            result=DocumentAnalysisResult(**MOCK_LLM_RESPONSE)
        )
        mock_processor.return_value = mock_instance
        
        # Create Lambda event
        event = {
            "body": json.dumps({
                "document_data": json.dumps(SAMPLE_JSON),
                "document_type": "json",
                "instructions": "Extract contact information."
            })
        }
        
        # Call Lambda handler
        response = lambda_handler(event, None)
        
        # Verify response
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True


def test_invalid_request():
    """Test Lambda handler with invalid request."""
    # Create invalid Lambda event (missing required field)
    event = {
        "body": json.dumps({
            "document_data": json.dumps(SAMPLE_JSON),
            # Missing instructions
        })
    }
    
    # Call Lambda handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body 