#!/usr/bin/env python
"""
Test script for the document processor API.

This script sends example requests to the document processor API to verify 
it's working correctly.
"""

import json
import sys
import argparse
import requests
import base64
from typing import Dict, Any, Optional


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Test the document processor API")
    parser.add_argument("--api-url", required=True, help="API Gateway URL")
    parser.add_argument("--test-type", choices=["json", "image", "pdf"], default="json",
                        help="Type of test to run (default: json)")
    return parser.parse_args()


def test_json_processing(api_url: str) -> None:
    """Test processing a JSON document."""
    print("\n=== Testing JSON Document Processing ===\n")
    
    # Example JSON data
    test_data = {
        "customer": {
            "id": "C1234",
            "name": "Jane Smith",
            "email": "jane.smith@example.com"
        },
        "order": {
            "id": "ORD-987",
            "items": [
                {"product": "Laptop", "price": 1299.99},
                {"product": "Mouse", "price": 24.99},
                {"product": "Keyboard", "price": 89.99}
            ],
            "total": 1414.97,
            "shipping_address": "123 Main St, Anytown, AN 12345"
        },
        "status": "processing"
    }
    
    # Prepare the request payload
    payload = {
        "document_data": json.dumps(test_data),
        "document_type": "json",
        "instructions": "Extract the customer name, order total, and list of products purchased."
    }
    
    # Send the request
    print("Sending request to API...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{api_url}/process", json=payload)
        
        # Print the response
        print(f"\nStatus Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")


def test_image_processing(api_url: str) -> None:
    """Test processing an image document."""
    print("\n=== Testing Image Document Processing ===\n")
    
    # For testing, we'll use a simple image file
    try:
        with open("examples/sample_receipt.jpg", "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        print("Sample image file not found. Please create examples/sample_receipt.jpg")
        return
    
    # Prepare the request payload
    payload = {
        "document_data": image_data,
        "document_type": "image",
        "instructions": "Extract the store name, date, total amount, and list of items purchased from this receipt."
    }
    
    # Send the request
    print("Sending request to API...")
    print(f"Payload: {json.dumps({**payload, 'document_data': '[BASE64 IMAGE DATA]'}, indent=2)}")
    
    try:
        response = requests.post(f"{api_url}/process", json=payload)
        
        # Print the response
        print(f"\nStatus Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")


def test_pdf_processing(api_url: str) -> None:
    """Test processing a PDF document."""
    print("\n=== Testing PDF Document Processing ===\n")
    
    # For testing, we'll use a simple PDF file
    try:
        with open("examples/sample_invoice.pdf", "rb") as pdf_file:
            pdf_data = base64.b64encode(pdf_file.read()).decode("utf-8")
    except FileNotFoundError:
        print("Sample PDF file not found. Please create examples/sample_invoice.pdf")
        return
    
    # Prepare the request payload
    payload = {
        "document_data": pdf_data,
        "document_type": "pdf",
        "instructions": "Extract the invoice number, date, customer details, and line items with their prices."
    }
    
    # Send the request
    print("Sending request to API...")
    print(f"Payload: {json.dumps({**payload, 'document_data': '[BASE64 PDF DATA]'}, indent=2)}")
    
    try:
        response = requests.post(f"{api_url}/process", json=payload)
        
        # Print the response
        print(f"\nStatus Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")


def main():
    """Main function."""
    args = parse_args()
    
    # Run the appropriate test
    if args.test_type == "json":
        test_json_processing(args.api_url)
    elif args.test_type == "image":
        test_image_processing(args.api_url)
    elif args.test_type == "pdf":
        test_pdf_processing(args.api_url)
    else:
        print(f"Unknown test type: {args.test_type}")
        sys.exit(1)


if __name__ == "__main__":
    main() 