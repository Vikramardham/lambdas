"""
Document processing logic for the Lambda function.
"""

import uuid
from typing import Dict, Any, Optional

from src.utils.llm_client import LLMClient
from src.utils.document_parsers import DocumentParser
from src.lambda_functions.document_processor.models import (
    DocumentProcessRequest,
    DocumentProcessResponse,
    DocumentAnalysisResult,
    DocumentType,
    TextAnnotation,
    EntityAnnotation,
    SummaryAnnotation
)

class DocumentProcessor:
    """
    Processes documents using LLM for analysis and structured output.
    """
    
    def __init__(self, request: DocumentProcessRequest):
        """
        Initialize document processor with request.
        
        Args:
            request: The document processing request
        """
        self.request = request
        self.request_id = str(uuid.uuid4())
        
        # Initialize LLM client with specified provider
        self.llm_client = LLMClient(provider=request.llm_provider)
    
    def process(self) -> DocumentProcessResponse:
        """
        Process the document according to the request.
        
        Returns:
            Document processing response with results
        """
        try:
            # Parse document data
            document_type = self.request.document_type.value if self.request.document_type else None
            parsed_document = DocumentParser.parse(
                self.request.document_data, 
                file_type=document_type
            )
            
            # Determine document type from parsed result
            if "image_type" in parsed_document:
                doc_type = DocumentType.IMAGE
            elif "page_count" in parsed_document:
                doc_type = DocumentType.PDF
            else:
                doc_type = DocumentType.JSON
            
            # Generate analysis results using LLM
            analysis_result = self._generate_analysis(parsed_document, doc_type)
            
            # Prepare successful response
            return DocumentProcessResponse(
                request_id=self.request_id,
                success=True,
                result=analysis_result
            )
            
        except Exception as e:
            # Return error response
            return DocumentProcessResponse(
                request_id=self.request_id,
                success=False,
                error_message=str(e)
            )
    
    def _generate_analysis(self, document_data: Dict[str, Any], doc_type: DocumentType) -> DocumentAnalysisResult:
        """
        Generate document analysis using LLM.
        
        Args:
            document_data: Parsed document data
            doc_type: Document type
            
        Returns:
            Document analysis result
        """
        # Create analysis schema for LLM output
        analysis_result = self._get_llm_analysis(document_data, doc_type)
        
        # Create document analysis result
        return DocumentAnalysisResult(
            document_type=doc_type,
            metadata=self._extract_metadata(document_data, doc_type),
            text_annotations=analysis_result.text_annotations,
            entity_annotations=analysis_result.entity_annotations,
            summary=analysis_result.summary,
            raw_llm_response=analysis_result.dict()
        )
    
    def _extract_metadata(self, document_data: Dict[str, Any], doc_type: DocumentType) -> Dict[str, Any]:
        """
        Extract metadata from document data.
        
        Args:
            document_data: Parsed document data
            doc_type: Document type
            
        Returns:
            Document metadata
        """
        if doc_type == DocumentType.IMAGE:
            return {
                "image_type": document_data.get("image_type"),
                "width": document_data.get("width"),
                "height": document_data.get("height"),
                "mode": document_data.get("mode")
            }
        elif doc_type == DocumentType.PDF:
            return {
                "page_count": document_data.get("page_count"),
                "metadata": document_data.get("metadata", {})
            }
        else:  # JSON
            # For JSON, we'll just include basic info about the structure
            if isinstance(document_data, dict):
                return {
                    "keys": list(document_data.keys()),
                    "size": len(document_data)
                }
            elif isinstance(document_data, list):
                return {
                    "length": len(document_data),
                    "type": "array"
                }
            else:
                return {"type": str(type(document_data))}
    
    def _get_llm_analysis(self, document_data: Dict[str, Any], doc_type: DocumentType) -> DocumentAnalysisResult:
        """
        Get document analysis from LLM.
        
        Args:
            document_data: Parsed document data
            doc_type: Document type
            
        Returns:
            Document analysis result
        """
        # Build prompt for LLM
        prompt = self._build_prompt(document_data, doc_type)
        
        # Define system prompt
        system_prompt = (
            "You are an expert document analyzer. "
            "Extract relevant information from the provided document based on the instructions. "
            "Provide structured output with text annotations, entity annotations, and a summary."
        )
        
        # Get structured output from LLM
        return self.llm_client.generate_structured_output(
            schema=DocumentAnalysisResult,
            prompt=prompt,
            system_prompt=system_prompt
        )
    
    def _build_prompt(self, document_data: Dict[str, Any], doc_type: DocumentType) -> str:
        """
        Build prompt for LLM based on document data and type.
        
        Args:
            document_data: Parsed document data
            doc_type: Document type
            
        Returns:
            Prompt for LLM
        """
        prompt_parts = [
            f"# Document Analysis Task\n\n",
            f"## Instructions\n{self.request.instructions}\n\n",
            f"## Document Type\n{doc_type.value}\n\n",
            "## Document Content\n"
        ]
        
        # Add document-specific content
        if doc_type == DocumentType.IMAGE:
            prompt_parts.append(
                f"Image of type {document_data.get('image_type')} "
                f"with dimensions {document_data.get('width')}x{document_data.get('height')}.\n"
                "Base64 data is available but not displayed for brevity.\n\n"
            )
        elif doc_type == DocumentType.PDF:
            prompt_parts.append("PDF content:\n\n")
            for page in document_data.get("pages", []):
                prompt_parts.append(f"Page {page.get('page_number')}:\n{page.get('text')}\n\n")
        else:  # JSON
            prompt_parts.append(f"JSON content:\n{str(document_data)}\n\n")
        
        # Add analysis instructions
        prompt_parts.append(
            "Based on the document and instructions provided, "
            "create a detailed analysis with text annotations, entity annotations, and a summary."
        )
        
        return "".join(prompt_parts) 