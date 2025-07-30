#!/usr/bin/env python3
"""
Test script for the API server
"""

import subprocess
import json
import sys
from pathlib import Path

def test_api_server():
    """Test the API server functionality"""
    
    # Test search functionality
    print("Testing search functionality...")
    search_data = {"query": "resume"}
    result = subprocess.run([
        "python", "api_server.py", "search", json.dumps(search_data)
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            response = json.loads(result.stdout)
            print("✅ Search test passed")
            print(f"Response: {response}")
        except json.JSONDecodeError:
            print("❌ Search test failed - Invalid JSON response")
            print(f"Output: {result.stdout}")
    else:
        print("❌ Search test failed")
        print(f"Error: {result.stderr}")
    
    # Test chatbot functionality
    print("\nTesting chatbot functionality...")
    chat_data = {"query": "What is this document about?"}
    result = subprocess.run([
        "python", "api_server.py", "chatbot", json.dumps(chat_data)
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            response = json.loads(result.stdout)
            print("✅ Chatbot test passed")
            print(f"Response: {response}")
        except json.JSONDecodeError:
            print("❌ Chatbot test failed - Invalid JSON response")
            print(f"Output: {result.stdout}")
    else:
        print("❌ Chatbot test failed")
        print(f"Error: {result.stderr}")
    
    # Test process functionality
    print("\nTesting process functionality...")
    process_data = {"files": ["test.pdf"]}
    result = subprocess.run([
        "python", "api_server.py", "process", json.dumps(process_data)
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            response = json.loads(result.stdout)
            print("✅ Process test passed")
            print(f"Response: {response}")
        except json.JSONDecodeError:
            print("❌ Process test failed - Invalid JSON response")
            print(f"Output: {result.stdout}")
    else:
        print("❌ Process test failed")
        print(f"Error: {result.stderr}")

if __name__ == "__main__":
    test_api_server() 