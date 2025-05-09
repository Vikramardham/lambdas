#!/usr/bin/env python3
"""
Test entry point for the Lambda handler (local simulation).
This script simulates an AWS Lambda event and prints the response.
"""

import json
import sys

# Import the handler from your Lambda app
try:
    from src.lambda_functions.document_processor.app import handler
except ImportError as e:
    print(f"Failed to import handler: {e}")
    sys.exit(1)

# Example event simulating an API Gateway request to /process
sample_event = {
    "body": json.dumps({
        "document_data": json.dumps({"test": "data"}),
        "document_type": "json",
        "instructions": "Summarize the test data"
    }),
    "httpMethod": "POST",
    "path": "/process",
    "headers": {
        "Content-Type": "application/json"
    }
}

def main():
    print("Invoking Lambda handler with sample event...")
    response = handler(sample_event, None)
    print("\nLambda handler response:")
    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    main() 