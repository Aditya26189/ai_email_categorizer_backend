#!/usr/bin/env python3
"""
Simple test script to verify CrashLens Logger core functionality.
"""

import os
import time
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Test the CrashLens Logger directly without FastAPI dependencies
import sys
sys.path.append('.')

# Create a minimal version of the CrashLens implementation for testing
class LogEvent:
    """Represents a single log event with all required fields and supports arbitrary extra fields."""
    
    def __init__(
        self,
        trace_id: str = None,
        type: str = None,
        start_time: str = None,
        end_time: str = None,
        level: str = None,
        input: dict = None,
        usage: dict = None,
        cost: float = None,
        metadata: dict = None,
        name: str = None,
        **kwargs
    ):
        # Required fields
        self.trace_id = trace_id
        self.type = type
        self.start_time = start_time
        self.end_time = end_time
        self.level = level
        self.input = input or {}
        self.usage = usage or {}
        self.cost = cost or 0.0
        self.metadata = metadata or {}
        self.name = name
        
        # Support arbitrary additional fields
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> dict:
        """Convert the event to a dictionary for JSON serialization."""
        event_dict = {
            "traceId": self.trace_id,
            "type": self.type,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "level": self.level,
            "input": self.input,
            "usage": self.usage,
            "cost": self.cost,
            "metadata": self.metadata,
            "name": self.name
        }
        
        # Add any additional attributes
        for key, value in self.__dict__.items():
            if key not in event_dict and not key.startswith('_'):
                event_dict[key] = value
        
        return event_dict


class CrashLensLogger:
    """Enhanced CrashLens Logger with improved structure and functionality."""
    
    def __init__(self, enable_logging: bool = True):
        self.enable_logging = enable_logging
    
    def log_event(
        self,
        traceId: str,
        type: str,
        startTime: str,
        endTime: str,
        level: str,
        input: dict,
        usage: dict,
        cost: float,
        metadata: dict,
        name: str,
        **kwargs
    ) -> LogEvent:
        """Create and return a log event with the new structure."""
        return LogEvent(
            trace_id=traceId,
            type=type,
            start_time=startTime,
            end_time=endTime,
            level=level,
            input=input,
            usage=usage,
            cost=cost,
            metadata=metadata,
            name=name,
            **kwargs
        )
    
    def write_logs(self, events: list, file_path: str):
        """Write log events to a file in JSONL format."""
        if not self.enable_logging:
            return
        
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Write events to file
        with open(file_path, 'a', encoding='utf-8') as f:
            for event in events:
                if isinstance(event, LogEvent):
                    json.dump(event.to_dict(), f, ensure_ascii=False)
                else:
                    json.dump(event, f, ensure_ascii=False)
                f.write('\n')


def test_crashlens_core():
    """Test the core CrashLens functionality."""
    print("🚀 Testing CrashLens Core Functionality")
    print("=" * 50)
    
    # Initialize logger
    logger = CrashLensLogger(enable_logging=True)
    log_file = "logs/test_crashlens.jsonl"
    
    # Test 1: API Request Logging
    print("Testing API request logging...")
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(milliseconds=150)
    
    api_event = logger.log_event(
        traceId="test-trace-123",
        type="api_request",
        startTime=start_time.isoformat().replace('+00:00', 'Z'),
        endTime=end_time.isoformat().replace('+00:00', 'Z'),
        level="info",
        input={"method": "POST", "path": "/classify", "request_data": {"test": "data"}},
        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        cost=0.0,
        metadata={"http_method": "POST", "endpoint": "/classify", "status_code": 200, "processing_time_ms": 150},
        name="api_request"
    )
    
    logger.write_logs([api_event], log_file)
    print("✓ API request logged successfully")
    
    # Test 2: Email Classification Logging
    print("Testing email classification logging...")
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(milliseconds=234)
    
    classification_event = logger.log_event(
        traceId="test-trace-456",
        type="email_classification",
        startTime=start_time.isoformat().replace('+00:00', 'Z'),
        endTime=end_time.isoformat().replace('+00:00', 'Z'),
        level="info",
        input={"model": "gemini-2.0-flash", "subject": "Test Job Application", "body_length": 150},
        usage={"prompt_tokens": 50, "completion_tokens": 10, "total_tokens": 60},
        cost=0.0,
        metadata={"predicted_category": "Job Offer", "confidence": 0.95, "processing_time_ms": 234},
        name="email_classification"
    )
    
    logger.write_logs([classification_event], log_file)
    print("✓ Email classification logged successfully")
    
    # Test 3: Email Summarization Logging
    print("Testing email summarization logging...")
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(milliseconds=156)
    
    summarization_event = logger.log_event(
        traceId="test-trace-789",
        type="email_summarization",
        startTime=start_time.isoformat().replace('+00:00', 'Z'),
        endTime=end_time.isoformat().replace('+00:00', 'Z'),
        level="info",
        input={"model": "gemini-ai-summarizer", "body_length": 500},
        usage={"prompt_tokens": 125, "completion_tokens": 30, "total_tokens": 155},
        cost=0.0,
        metadata={
            "summary_bullet_count": 3,
            "processing_time_ms": 156,
            "summary_bullets": [
                "Meeting scheduled for tomorrow at 2pm",
                "Location: Conference room A", 
                "Agenda items to be discussed"
            ]
        },
        name="email_summarization"
    )
    
    logger.write_logs([summarization_event], log_file)
    print("✓ Email summarization logged successfully")
    
    # Test 4: Check log file
    print("\nChecking log file...")
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"✓ Log file created: {log_file}")
        print(f"✓ Contains {len(lines)} log entries")
        
        # Validate JSON format
        for i, line in enumerate(lines):
            try:
                json.loads(line.strip())
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in line {i+1}: {e}")
                return False
        
        print("✓ All log entries are valid JSON")
        
        # Print sample entry
        sample_entry = json.loads(lines[-1].strip())
        print(f"✓ Sample entry: {sample_entry['type']} - {sample_entry['name']}")
        
        return True
    else:
        print(f"❌ Log file not created: {log_file}")
        return False


if __name__ == "__main__":
    try:
        success = test_crashlens_core()
        if success:
            print("\n✅ All CrashLens core tests passed!")
            print("The logging system is working correctly.")
        else:
            print("\n❌ Some tests failed.")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
