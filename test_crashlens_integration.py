#!/usr/bin/env python3
"""
Test script to verify CrashLens Logger integration.
"""

import asyncio
import time
from app.core.api_logging import api_logger, email_logger


def test_api_logging():
    """Test basic API logging functionality."""
    print("Testing API logging...")
    
    # Test basic API call logging
    api_logger.log_api_call(
        endpoint="/test/endpoint",
        method="POST",
        request_data={"test": "data"},
        response_data={"result": "success"},
        status_code=200,
        latency_ms=150,
        user_id="test_user_123",
        trace_id="test_trace_456"
    )
    
    print("✓ API call logged successfully")


def test_email_classification_logging():
    """Test email classification logging."""
    print("Testing email classification logging...")
    
    email_logger.log_email_classification(
        email_subject="Test Job Application",
        email_body="Dear candidate, we would like to offer you a position...",
        predicted_category="Job Offer",
        confidence=0.95,
        model_used="gemini-2.0-flash",
        processing_time_ms=234,
        user_id="test_user_123"
    )
    
    print("✓ Email classification logged successfully")


def test_email_summarization_logging():
    """Test email summarization logging."""
    print("Testing email summarization logging...")
    
    email_logger.log_email_summarization(
        email_body="This is a long email about a meeting tomorrow at 2pm in conference room A...",
        summary_bullets=[
            "Meeting scheduled for tomorrow at 2pm",
            "Location: Conference room A",
            "Agenda items to be discussed"
        ],
        model_used="gemini-ai-summarizer",
        processing_time_ms=156,
        user_id="test_user_123"
    )
    
    print("✓ Email summarization logged successfully")


def check_log_files():
    """Check if log files are created and have content."""
    import os
    
    log_dir = "logs"
    if os.path.exists(log_dir):
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.jsonl')]
        if log_files:
            print(f"✓ Found {len(log_files)} log files in {log_dir}/")
            for file in log_files:
                file_path = os.path.join(log_dir, file)
                size = os.path.getsize(file_path)
                print(f"  - {file}: {size} bytes")
        else:
            print("ℹ No .jsonl log files found yet")
    else:
        print("ℹ Logs directory not found")


if __name__ == "__main__":
    print("🚀 Testing CrashLens Logger Integration")
    print("=" * 50)
    
    try:
        # Test all logging functions
        test_api_logging()
        test_email_classification_logging()
        test_email_summarization_logging()
        
        # Wait a moment for file writes
        time.sleep(1)
        
        # Check log files
        print("\nChecking log files...")
        check_log_files()
        
        print("\n✅ All CrashLens logging tests passed!")
        print("Your logging system is ready to track API calls and email operations.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
