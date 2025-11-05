#!/usr/bin/env python3
"""
Debug script to test Azure OpenAI token extraction
Run this to see if HTTP interception is working correctly
"""

import requests
import json
import logging
from unittest.mock import Mock

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_real_azure_interception():
    """
    Test what happens when we make an actual Azure OpenAI call
    This will help us see if HTTP interception is working
    """
    
    print("🧪 Testing Real Azure OpenAI HTTP Interception...")
    
    # Enable HTTP monitoring
    try:
        from ai_monitor.http_interceptor import enable_http_monitoring
        enable_http_monitoring()
        print("✅ HTTP monitoring enabled")
    except Exception as e:
        print(f"❌ Failed to enable HTTP monitoring: {e}")
        return
    
    # Import the monitor
    try:
        from ai_monitor import get_monitor
        monitor = get_monitor()
        print(f"✅ Monitor instance: {monitor}")
    except Exception as e:
        print(f"❌ Failed to get monitor: {e}")
        return
    
    print("\n🔍 Now you can make an Azure OpenAI call from your application...")
    print("Watch the logs to see if our interception works!")
    print("Look for these debug messages:")
    print("  🚨 [CRITICAL DEBUG] Intercepted POST: ...")
    print("  🚨 [HTTPX CRITICAL] INTERCEPTED AZURE REQUEST")
    print("  🚨 [CRITICAL] record_llm_call called with:")
    
    # Show current monitor stats
    if monitor:
        stats = monitor.get_summary_stats()
        print(f"\n📊 Current monitor stats: {stats}")
        
        calls = monitor.get_llm_calls(limit=5)
        print(f"📊 Recent LLM calls: {len(calls)}")
        for i, call in enumerate(calls[-3:], 1):
            print(f"   {i}. Model: {call.model}, Tokens: {call.input_tokens}→{call.output_tokens}")

def check_interception_status():
    """Check if HTTP interception is properly set up"""
    
    print("\n🔍 Checking HTTP Interception Status...")
    
    import requests
    print(f"✅ requests.post function: {requests.post}")
    
    try:
        import httpx
        print(f"✅ httpx.post function: {httpx.post}")
        print(f"✅ httpx.Client.post function: {httpx.Client.post}")
    except ImportError:
        print("❌ httpx not available")
    
    # Check if functions are patched
    if hasattr(requests.post, '__name__'):
        if 'monitored' in requests.post.__name__:
            print("✅ requests.post is patched for monitoring")
        else:
            print("❌ requests.post is NOT patched")
    
    try:
        import httpx
        if hasattr(httpx.post, '__name__'):
            if 'monitored' in httpx.post.__name__:
                print("✅ httpx.post is patched for monitoring")
            else:
                print("❌ httpx.post is NOT patched")
    except:
        pass

if __name__ == "__main__":
    test_real_azure_interception()
    check_interception_status()
    
    print("\n🎯 Next Steps:")
    print("1. Run this script")
    print("2. Make an Azure OpenAI call from your application") 
    print("3. Check logs for the debug messages listed above")
    print("4. If you don't see the debug messages, the HTTP interception isn't working")
    print("5. If you see the debug messages, we can see what token values are being extracted")
