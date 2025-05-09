"""
Document parsers for different input file types (images, PDFs, JSON).
"""

import json
import base64
from typing import Dict, Any, Union, Optional
import io

from PIL import Image
from pypdf import PdfReader

class DocumentParser:
    """
    Parser for different document types (images, PDFs, JSON).
    """
    
    @staticmethod
    def parse_image(image_data: Union[str, bytes]) -> Dict[str, Any]:
        """
        Parse image data (either base64 encoded string or raw bytes).
        
        Args:
            image_data: Base64 encoded image or raw image bytes
            
        Returns:
            Dict with image metadata and base64 encoded data
        """
        # Convert base64 string to bytes if needed
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                # Handle Data URLs
                header, encoded = image_data.split(',', 1)
                image_data = base64.b64decode(encoded)
            else:
                # Regular base64 string
                image_data = base64.b64decode(image_data)
        
        # Extract image metadata
        image = Image.open(io.BytesIO(image_data))
        width, height = image.size
        format_name = image.format or "UNKNOWN"
        
        # Prepare output
        result = {
            "image_type": format_name,
            "width": width,
            "height": height,
            "mode": image.mode,
            "base64_data": base64.b64encode(image_data).decode('utf-8')
        }
        
        return result
    
    @staticmethod
    def parse_pdf(pdf_data: Union[str, bytes]) -> Dict[str, Any]:
        """
        Parse PDF data (either base64 encoded string or raw bytes).
        
        Args:
            pdf_data: Base64 encoded PDF or raw PDF bytes
            
        Returns:
            Dict with PDF metadata and extracted text
        """
        # Convert base64 string to bytes if needed
        if isinstance(pdf_data, str):
            if pdf_data.startswith('data:application/pdf'):
                # Handle Data URLs
                header, encoded = pdf_data.split(',', 1)
                pdf_data = base64.b64decode(encoded)
            else:
                # Regular base64 string
                pdf_data = base64.b64decode(pdf_data)
        
        # Parse PDF
        pdf_file = io.BytesIO(pdf_data)
        pdf_reader = PdfReader(pdf_file)
        
        # Extract text from pages
        pages = []
        for i, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            pages.append({
                "page_number": i + 1,
                "text": text
            })
        
        # Prepare output
        result = {
            "page_count": len(pdf_reader.pages),
            "metadata": dict(pdf_reader.metadata or {}),
            "pages": pages,
        }
        
        return result
    
    @staticmethod
    def parse_json(json_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse JSON data (either string or already parsed dict).
        
        Args:
            json_data: JSON string or parsed JSON object
            
        Returns:
            Parsed JSON data as dict
        """
        if isinstance(json_data, str):
            return json.loads(json_data)
        return json_data
    
    @classmethod
    def parse(cls, data: Any, file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse document data based on type.
        
        Args:
            data: Document data (bytes, string, or dict)
            file_type: Optional hint for the file type ('image', 'pdf', 'json')
                       If None, will try to detect automatically
                       
        Returns:
            Dict with parsed document data
        """
        # Try to determine file type if not provided
        if file_type is None:
            if isinstance(data, dict):
                file_type = 'json'
            elif isinstance(data, (str, bytes)):
                # Try to detect from content
                if isinstance(data, str):
                    if data.startswith('data:image'):
                        file_type = 'image'
                    elif data.startswith('data:application/pdf'):
                        file_type = 'pdf'
                    elif data.startswith('{') and data.endswith('}'):
                        file_type = 'json'
                    else:
                        try:
                            base64.b64decode(data)
                            # We'll need to try to detect if this is a PDF or image
                            # Simplified detection - can be improved
                            if b'%PDF' in base64.b64decode(data)[:10]:
                                file_type = 'pdf'
                            else:
                                file_type = 'image'
                        except:
                            raise ValueError("Could not determine file type")
                else:  # bytes
                    if data[:4] == b'%PDF':
                        file_type = 'pdf'
                    else:
                        file_type = 'image'  # Assume image for other binary data
        
        # Parse based on determined file type
        if file_type == 'image':
            return cls.parse_image(data)
        elif file_type == 'pdf':
            return cls.parse_pdf(data)
        elif file_type == 'json':
            return cls.parse_json(data)
        else:
            raise ValueError(f"Unsupported file type: {file_type}") 