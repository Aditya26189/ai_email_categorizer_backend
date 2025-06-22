#!/usr/bin/env python3
"""
Test script to verify the Gmail HistoryId system implementation.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.base import get_user_history_id, set_user_history_id, get_mongo_client
from app.services.gmail_client import get_current_history_id, get_incremental_emails
from loguru import logger

async def test_history_id_system():
    """Test the historyId system functionality."""
    
    # Test user ID (replace with actual user ID for testing)
    test_user_id = "user_2abc123def456"
    
    try:
        # Ensure DB is connected
        await get_mongo_client()
        
        logger.info("🧪 Testing Gmail HistoryId System")
        logger.info("=" * 50)
        
        # Test 1: Set and get historyId
        logger.info("Test 1: Setting and getting historyId")
        test_history_id = "12345"
        await set_user_history_id(test_user_id, test_history_id)
        
        retrieved_history_id = await get_user_history_id(test_user_id)
        if retrieved_history_id == test_history_id:
            logger.success("✅ HistoryId storage and retrieval works")
        else:
            logger.error(f"❌ HistoryId mismatch: expected {test_history_id}, got {retrieved_history_id}")
        
        # Test 2: Get current historyId from Gmail (requires valid user)
        logger.info("Test 2: Getting current historyId from Gmail API")
        try:
            current_history_id = await get_current_history_id(test_user_id)
            if current_history_id:
                logger.success(f"✅ Current Gmail historyId: {current_history_id}")
            else:
                logger.warning("⚠️ No current historyId returned (user may not have Gmail connected)")
        except Exception as e:
            logger.warning(f"⚠️ Could not get current historyId: {e}")
        
        # Test 3: Test incremental email fetching (requires valid user and historyId)
        logger.info("Test 3: Testing incremental email fetching")
        try:
            if retrieved_history_id:
                emails = await get_incremental_emails(test_user_id, retrieved_history_id)
                logger.success(f"✅ Incremental email fetch returned {len(emails)} emails")
            else:
                logger.warning("⚠️ No historyId available for incremental testing")
        except Exception as e:
            logger.warning(f"⚠️ Incremental email fetch failed: {e}")
        
        logger.info("=" * 50)
        logger.info("🎉 HistoryId system test completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

async def check_user_history_id_status():
    """Check the historyId status for all users."""
    
    try:
        await get_mongo_client()
        from app.db.base import db
        
        users_collection = db.get_collection('users')
        
        logger.info("📊 Checking HistoryId Status for All Users")
        logger.info("=" * 50)
        
        total_users = 0
        users_with_gmail = 0
        users_with_history_id = 0
        
        async for user in users_collection.find():
            total_users += 1
            
            if user.get("is_gmail_connected"):
                users_with_gmail += 1
                
                if user.get("last_history_id"):
                    users_with_history_id += 1
                    logger.success(f"✅ {user.get('email', 'Unknown')}: {user['last_history_id']}")
                else:
                    logger.warning(f"⚠️ {user.get('email', 'Unknown')}: No historyId")
        
        logger.info("=" * 50)
        logger.info(f"📈 Summary:")
        logger.info(f"   Total users: {total_users}")
        logger.info(f"   Users with Gmail: {users_with_gmail}")
        logger.info(f"   Users with historyId: {users_with_history_id}")
        
        if users_with_gmail > 0:
            coverage = (users_with_history_id / users_with_gmail) * 100
            logger.info(f"   HistoryId coverage: {coverage:.1f}%")
        
    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")
        raise

if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_history_id_system())
    print()
    asyncio.run(check_user_history_id_status()) 