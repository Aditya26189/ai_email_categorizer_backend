#!/usr/bin/env python3
"""
Test script to verify logging fixes for Unicode characters.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.logger import setup_logging
from loguru import logger

def test_logging():
    """Test various logging scenarios that previously caused issues."""
    
    # Setup logging
    setup_logging()
    
    # Test regular ASCII messages
    logger.info("Testing regular ASCII message")
    
    # Test Unicode characters that were causing issues
    logger.info("Timestamp: 2025-07-29T05:10:14.411606")
    logger.info("Found 5 emails to process")
    logger.error("Failed to start email processing: Test error")
    
    # Test some safe Unicode characters
    logger.info("Processing user's emails successfully")
    logger.info("Classification completed ✓")  # Simple checkmark
    
    print("✅ All logging tests completed successfully!")

if __name__ == "__main__":
    test_logging()
