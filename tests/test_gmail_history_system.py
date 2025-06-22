import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.services.gmail_client import (
    get_incremental_emails, 
    get_current_history_id, 
    handle_history_id_too_old,
    get_latest_emails
)
from app.db.base import get_user_history_id, set_user_history_id
from fastapi.testclient import TestClient
from app.main import app
import json

# Patch db singleton for all tests in this file
def _make_mock_db():
    mock_users = AsyncMock()
    mock_users.find_one = AsyncMock(return_value={"clerk_user_id": "user123", "last_history_id": "12345"})
    mock_users.update_one = AsyncMock()
    mock_db = AsyncMock()
    mock_db.get_collection = lambda name: mock_users
    return mock_db

@pytest.fixture(autouse=True)
def patch_db():
    with patch("app.db.base.db", _make_mock_db()):
        yield

class TestGmailHistorySystem:
    """Test the Gmail historyId system for incremental email processing."""
    
    @pytest.fixture
    def mock_gmail_service(self):
        """Mock Gmail service for testing."""
        mock_service = Mock()
        
        # Mock profile response
        mock_profile = Mock()
        mock_profile.execute.return_value = {"historyId": "12345"}
        mock_service.users.return_value.getProfile.return_value = mock_profile
        
        # Mock history response
        mock_history = Mock()
        mock_history.execute.return_value = {
            "history": [
                {
                    "messagesAdded": [
                        {"message": {"id": "msg1", "threadId": "thread1"}}
                    ]
                }
            ]
        }
        mock_service.users.return_value.history.return_value.list.return_value = mock_history
        
        # Mock message response
        mock_message = Mock()
        mock_message.execute.return_value = {
            "id": "msg1",
            "threadId": "thread1",
            "historyId": "12346",
            "labelIds": ["INBOX"],
            "internalDate": "1640995200000",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Email"},
                    {"name": "From", "value": "test@example.com"},
                    {"name": "Date", "value": "Wed, 13 Mar 2024 15:30:45 +0000"}
                ],
                "body": {"data": "dGVzdCBib2R5"}  # base64 encoded "test body"
            }
        }
        mock_service.users.return_value.messages.return_value.get.return_value = mock_message
        
        return mock_service
    
    @pytest.mark.asyncio
    async def test_get_current_history_id(self, mock_gmail_service):
        """Test getting current historyId from Gmail API."""
        with patch('app.services.gmail_client.get_gmail_service_for_user', return_value=mock_gmail_service):
            history_id = await get_current_history_id("user123")
            assert history_id == "12345"
    
    @pytest.mark.asyncio
    async def test_get_incremental_emails_success(self, mock_gmail_service):
        """Test successful incremental email fetching."""
        with patch('app.services.gmail_client.get_gmail_service_for_user', return_value=mock_gmail_service), \
             patch('app.db.email_db.email_db.already_classified', return_value=False), \
             patch('app.db.email_db.email_db.save_email', return_value=True), \
             patch('app.services.classifier.classify_email', return_value="Test Category"), \
             patch('app.utils.llm_utils.summarize_to_bullets', return_value=["Test summary"]), \
             patch('app.utils.gmail_parser.extract_email_body', return_value="test body"):
            
            emails = await get_incremental_emails("user123", "12344")
            assert len(emails) == 1
            assert emails[0]['gmail_id'] == "msg1"
            assert emails[0]['history_id'] == "12346"
    
    @pytest.mark.asyncio
    async def test_get_incremental_emails_no_new_messages(self, mock_gmail_service):
        """Test incremental email fetching when no new messages exist."""
        # Mock empty history response
        mock_gmail_service.users.return_value.history.return_value.list.return_value.execute.return_value = {
            "history": []
        }
        
        with patch('app.services.gmail_client.get_gmail_service_for_user', return_value=mock_gmail_service):
            emails = await get_incremental_emails("user123", "12344")
            assert len(emails) == 0
    
    @pytest.mark.asyncio
    async def test_get_incremental_emails_history_id_too_old(self, mock_gmail_service):
        """Test incremental email fetching when historyId is too old."""
        # Mock response indicating historyId is too old
        mock_gmail_service.users.return_value.history.return_value.list.return_value.execute.return_value = {
            "historyId": "12350"  # Gmail returns a new historyId when the old one is too old
        }
        
        with patch('app.services.gmail_client.get_gmail_service_for_user', return_value=mock_gmail_service):
            emails = await get_incremental_emails("user123", "12344")
            assert len(emails) == 0
    
    @pytest.mark.asyncio
    async def test_handle_history_id_too_old(self, mock_gmail_service):
        """Test handling when historyId is too old."""
        with patch('app.services.gmail_client.get_gmail_service_for_user', return_value=mock_gmail_service), \
             patch('app.services.gmail_client.get_latest_emails', return_value=[]), \
             patch('app.db.base.set_user_history_id') as mock_set_history:
            
            emails = await handle_history_id_too_old("user123", "12344")
            mock_set_history.assert_called_once_with("user123", "12345")
            assert len(emails) == 0

class TestWebhookIntegration:
    """Test webhook integration with proper mocking."""
    
    @pytest.mark.asyncio
    async def test_webhook_with_history_id(self):
        """Test webhook processing with historyId."""
        from app.routers.webhook import gmail_push_webhook
        from fastapi import Request
        from unittest.mock import AsyncMock
        
        # Create mock request
        mock_request = AsyncMock(spec=Request)
        mock_request.headers = {
            'host': 'testserver',
            'accept': '*/*',
            'content-type': 'application/json'
        }
        mock_request.json = AsyncMock(return_value={
            "emailAddress": "test@example.com",
            "historyId": "12346"
        })
        
        with patch('app.routers.webhook.get_user_id_by_email', return_value="user123"), \
             patch('app.db.base.get_user_history_id', return_value="12345"), \
             patch('app.services.gmail_client.get_incremental_emails', return_value=[]), \
             patch('app.db.base.set_user_history_id') as mock_set_history:
            
            response = await gmail_push_webhook(mock_request)
            assert response.status_code == 200
            assert json.loads(response.body.decode()) == {"status": "success", "processed": 0}
            mock_set_history.assert_called_once_with("user123", "12346")
    
    @pytest.mark.asyncio
    async def test_webhook_without_history_id(self):
        """Test webhook processing without historyId."""
        from app.routers.webhook import gmail_push_webhook
        from fastapi import Request
        from unittest.mock import AsyncMock
        
        # Create mock request
        mock_request = AsyncMock(spec=Request)
        mock_request.headers = {
            'host': 'testserver',
            'accept': '*/*',
            'content-type': 'application/json'
        }
        mock_request.json = AsyncMock(return_value={
            "emailAddress": "test@example.com"
        })
        
        with patch('app.routers.webhook.get_user_id_by_email', return_value="user123"), \
             patch('app.db.base.get_user_history_id', return_value=None), \
             patch('app.services.email_ingestion.fetch_and_process_new_emails', return_value=5):
            
            response = await gmail_push_webhook(mock_request)
            assert response.status_code == 200
            assert json.loads(response.body.decode()) == {"status": "success", "processed": 5}
    
    @pytest.mark.asyncio
    async def test_webhook_pubsub_message(self):
        """Test webhook processing with Pub/Sub encoded message."""
        from app.routers.webhook import gmail_push_webhook
        from fastapi import Request
        from unittest.mock import AsyncMock
        import base64
        import json as pyjson
        
        # Create Pub/Sub style payload
        webhook_data = {
            "emailAddress": "test@example.com",
            "historyId": "12346"
        }
        encoded_data = base64.b64encode(pyjson.dumps(webhook_data).encode()).decode()
        
        pubsub_payload = {
            "message": {
                "data": encoded_data
            }
        }
        
        # Create mock request
        mock_request = AsyncMock(spec=Request)
        mock_request.headers = {
            'host': 'testserver',
            'accept': '*/*',
            'content-type': 'application/json'
        }
        mock_request.json = AsyncMock(return_value=pubsub_payload)
        
        with patch('app.routers.webhook.get_user_id_by_email', return_value="user123"), \
             patch('app.db.base.get_user_history_id', return_value="12345"), \
             patch('app.services.gmail_client.get_incremental_emails', return_value=[]), \
             patch('app.db.base.set_user_history_id') as mock_set_history:
            
            response = await gmail_push_webhook(mock_request)
            assert response.status_code == 200
            assert json.loads(response.body.decode()) == {"status": "success", "processed": 0}
            mock_set_history.assert_called_once_with("user123", "12346")

class TestHistoryIdDatabase:
    """Test historyId database operations."""
    
    @pytest.mark.asyncio
    async def test_set_and_get_history_id(self):
        """Test setting and getting historyId from database."""
        # Create async mock for database operations
        mock_users = AsyncMock()
        mock_users.update_one = AsyncMock()
        mock_users.find_one = AsyncMock()
        
        with patch('app.db.base.db.get_collection', return_value=mock_users):
            # Test setting historyId
            await set_user_history_id("user123", "12345")
            mock_users.update_one.assert_called_once_with(
                {"clerk_user_id": "user123"},
                {"$set": {"last_history_id": "12345"}}
            )
            
            # Test getting historyId
            mock_users.find_one.return_value = {"clerk_user_id": "user123", "last_history_id": "12345"}
            history_id = await get_user_history_id("user123")
            assert history_id == "12345"
            
            # Test getting historyId for non-existent user
            mock_users.find_one.return_value = None
            history_id = await get_user_history_id("nonexistent")
            assert history_id is None

if __name__ == "__main__":
    pytest.main([__file__]) 