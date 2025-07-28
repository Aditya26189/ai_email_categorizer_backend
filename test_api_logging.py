#!/usr/bin/env python3
"""
Test script for API logging functionality.
"""

import asyncio
import json
from pathlib import Path

from app.core.api_logging import api_logger, email_logger

async def test_api_logging():
    """Test the API logging functionality."""
    print("🧪 Testing API Logging Functionality")
    print("=" * 50)
    
    # Test API call logging
    print("\n1. Testing API call logging...")
    api_logger.log_api_call(
        endpoint="/emails",
        method="GET",
        request_data={"category": "Work", "page": 1, "limit": 20},
        response_data={"total": 15, "emails": ["email1", "email2"]},
        status_code=200,
        latency_ms=250,
        user_id="test_user_123",
        trace_id="test-trace-001"
    )
    print("✅ API call logged successfully")
    
    # Test email classification logging
    print("\n2. Testing email classification logging...")
    email_logger.log_email_classification(
        email_subject="Meeting Request for Tomorrow",
        email_body="Hi, let's schedule a meeting for tomorrow at 2 PM to discuss the project...",
        predicted_category="Work",
        confidence=0.95,
        model_used="gemini-2.0-flash",
        processing_time_ms=1200,
        user_id="test_user_123"
    )
    print("✅ Email classification logged successfully")
    
    # Test email summarization logging
    print("\n3. Testing email summarization logging...")
    email_logger.log_email_summarization(
        email_body="This is a long email about project updates and deadlines...",
        summary_bullets=[
            "Project milestone achieved",
            "Next deadline is Friday",
            "Team meeting scheduled"
        ],
        model_used="gemini-ai-summarizer",
        processing_time_ms=800,
        user_id="test_user_123"
    )
    print("✅ Email summarization logged successfully")
    
    # Check if log file was created
    log_file = Path("logs/api_calls.jsonl")
    if log_file.exists():
        print(f"\n📄 Log file created: {log_file}")
        print(f"📊 Log file size: {log_file.stat().st_size} bytes")
        
        # Show last few log entries
        print("\n📋 Recent log entries:")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[-3:], 1):
                try:
                    log_entry = json.loads(line)
                    model = log_entry.get('input', {}).get('model', 'unknown')
                    latency = log_entry.get('latency_ms', 0)
                    print(f"  {i}. Model: {model}, Latency: {latency}ms")
                except:
                    print(f"  {i}. Invalid log entry")
    else:
        print("❌ Log file was not created")
    
    print("\n🎉 API logging test completed!")
    print("\nNext steps:")
    print("1. Start your FastAPI server")
    print("2. Make some API calls")
    print("3. Run: python analyze_api_logs.py --all")

if __name__ == "__main__":
    asyncio.run(test_api_logging())
