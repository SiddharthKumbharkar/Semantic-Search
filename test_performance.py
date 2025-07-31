#!/usr/bin/env python3
"""
Performance test script for semantic search
"""

import time
import json
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from api_server import initialize_backend, handle_search_request, handle_chatbot_request

def test_search_performance():
    """Test search performance with various queries"""
    print("Initializing backend...")
    if not initialize_backend():
        print("Failed to initialize backend")
        return
    
    test_queries = [
        "What is Numpy?",
        "machine learning",
        "data analysis",
        "programming",
        "algorithms"
    ]
    
    print("\n=== Search Performance Test ===")
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        start_time = time.time()
        
        try:
            result = handle_search_request({
                'query': query,
                'userId': 'test_user',
                'accessLevel': 'all'
            })
            
            response_time = time.time() - start_time
            result_count = len(result.get('results', []))
            
            print(f"  Response time: {response_time:.2f}s")
            print(f"  Results found: {result_count}")
            
            if 'error' in result:
                print(f"  Error: {result['error']}")
                
        except Exception as e:
            response_time = time.time() - start_time
            print(f"  Response time: {response_time:.2f}s")
            print(f"  Error: {str(e)}")

def test_chatbot_performance():
    """Test chatbot performance with various queries"""
    print("\n=== Chatbot Performance Test ===")
    
    test_queries = [
        "What is Numpy?",
        "Explain machine learning",
        "How to analyze data?",
        "What is programming?",
        "Tell me about algorithms"
    ]
    
    for query in test_queries:
        print(f"\nTesting chatbot query: '{query}'")
        start_time = time.time()
        
        try:
            result = handle_chatbot_request({
                'query': query,
                'userId': 'test_user',
                'accessLevel': 'all'
            })
            
            response_time = time.time() - start_time
            response_length = len(result.get('response', ''))
            
            print(f"  Response time: {response_time:.2f}s")
            print(f"  Response length: {response_length} characters")
            
            if 'error' in result:
                print(f"  Error: {result['error']}")
                
        except Exception as e:
            response_time = time.time() - start_time
            print(f"  Response time: {response_time:.2f}s")
            print(f"  Error: {str(e)}")

if __name__ == "__main__":
    print("Starting performance tests...")
    test_search_performance()
    test_chatbot_performance()
    print("\nPerformance tests completed!") 