"""
Pydantic models for document processing API.
"""

from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, validator


class DocumentType(str, Enum):
    """Supported document types."""
    IMAGE = "image"
    PDF = "pdf"
    JSON = "json"


class DocumentProcessRequest(BaseModel):
    """
    Request model for document processing.
    """
    document_data: str = Field(..., description="Document data (base64 encoded or JSON string)")
    document_type: Optional[DocumentType] = Field(
        None, 
        description="Type of document (image, pdf, json). If not provided, will try to detect automatically."
    )
    llm_provider: Optional[str] = Field(
        None, 
        description="LLM provider to use (openai, anthropic, cohere). Uses default if not specified."
    )
    instructions: str = Field(
        ..., 
        description="Instructions for processing the document."
    )


class TextAnnotation(BaseModel):
    """
    Model for text annotations produced by the LLM.
    """
    text: str = Field(..., description="Extracted or annotated text")
    relevance_score: Optional[float] = Field(None, description="Relevance score between 0 and 1")
    page_number: Optional[int] = Field(None, description="Page number for PDF documents")
    bounding_box: Optional[Dict[str, float]] = Field(None, description="Bounding box for images (x, y, width, height)")


class EntityAnnotation(BaseModel):
    """
    Model for entity annotations (names, dates, amounts, etc).
    """
    entity_type: str = Field(..., description="Type of entity (person, date, amount, etc)")
    value: str = Field(..., description="Entity value")
    confidence: Optional[float] = Field(None, description="Confidence score between 0 and 1")
    normalized_value: Optional[Any] = Field(None, description="Normalized value (e.g. parsed date)")


class SummaryAnnotation(BaseModel):
    """
    Model for document summaries.
    """
    summary: str = Field(..., description="Document summary")
    key_points: List[str] = Field(default_factory=list, description="Key points from the document")


class DocumentAnalysisResult(BaseModel):
    """
    Base model for document analysis results.
    """
    document_type: DocumentType = Field(..., description="Type of document processed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    text_annotations: List[TextAnnotation] = Field(default_factory=list, description="Text annotations")
    entity_annotations: List[EntityAnnotation] = Field(default_factory=list, description="Entity annotations")
    summary: Optional[SummaryAnnotation] = Field(None, description="Document summary")
    raw_llm_response: Optional[Dict[str, Any]] = Field(None, description="Raw LLM response for debugging")


class DocumentProcessResponse(BaseModel):
    """
    Response model for document processing.
    """
    request_id: str = Field(..., description="Unique request ID")
    success: bool = Field(..., description="Whether processing was successful")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    result: Optional[DocumentAnalysisResult] = Field(None, description="Document analysis result")
    
    @validator('result', always=True)
    def result_required_if_success(cls, v, values):
        """Validate that result is provided if success is True."""
        if values.get('success', False) and v is None:
            raise ValueError('result is required when success is True')
        return v 