import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from app.services.google_oauth import GoogleOAuthService
from app.models.user import UserGmailStatus, GmailTokens

class TestGmailWorkflow:
    """Test cases for the complete Gmail OAuth workflow."""
    
    @pytest.fixture
    def mock_user_data(self):
        """Mock user data for testing."""
        return {
            "clerk_user_id": "user_2xYk123",
            "email": "test@example.com",
            "is_gmail_connected": False,
            "gmail_email": None,
            "gmail_connected_at": None
        }
    
    @pytest.fixture
    def mock_connected_user_data(self):
        """Mock connected user data for testing."""
        return {
            "clerk_user_id": "user_2xYk123",
            "email": "test@example.com",
            "is_gmail_connected": True,
            "gmail_email": "test@gmail.com",
            "gmail_connected_at": datetime.utcnow().isoformat()
        }
    
    @pytest.mark.asyncio
    @patch('app.services.google_oauth.get_mongo_client')
    async def test_check_gmail_connection_status_not_connected(self, mock_get_mongo_client, mock_user_data):
        """Test checking Gmail connection status when user is not connected."""
        service = GoogleOAuthService()
        
        # Mock database
        mock_db = Mock()
        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = mock_user_data
        mock_db.__getitem__.return_value = mock_collection
        mock_get_mongo_client.return_value = mock_db
        
        # Test status check
        result = await service.check_gmail_connection_status("user_2xYk123")
        
        assert result["is_gmail_connected"] is False
        assert result["user_id"] == "user_2xYk123"
        assert result["email"] == "test@example.com"
        assert "not connected" in result["message"]
    
    @pytest.mark.asyncio
    @patch('app.services.google_oauth.get_mongo_client')
    async def test_check_gmail_connection_status_connected(self, mock_get_mongo_client, mock_connected_user_data):
        """Test checking Gmail connection status when user is connected."""
        service = GoogleOAuthService()
        
        # Mock database
        mock_db = Mock()
        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = mock_connected_user_data
        mock_db.__getitem__.return_value = mock_collection
        mock_get_mongo_client.return_value = mock_db
        
        # Test status check
        result = await service.check_gmail_connection_status("user_2xYk123")
        
        assert result["is_gmail_connected"] is True
        assert result["user_id"] == "user_2xYk123"
        assert result["email"] == "test@example.com"
        assert "connected" in result["message"]
    
    @pytest.mark.asyncio
    @patch('app.services.google_oauth.get_mongo_client')
    async def test_check_gmail_connection_status_user_not_found(self, mock_get_mongo_client):
        """Test checking Gmail connection status when user is not found."""
        service = GoogleOAuthService()
        
        # Mock database
        mock_db = Mock()
        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = None
        mock_db.__getitem__.return_value = mock_collection
        mock_get_mongo_client.return_value = mock_db
        
        # Test status check
        result = await service.check_gmail_connection_status("user_2xYk123")
        
        assert result["is_gmail_connected"] is False
        assert result["user_id"] == "user_2xYk123"
        assert result["message"] == "User not found"
    
    @pytest.mark.asyncio
    @patch('app.services.google_oauth.get_mongo_client')
    @patch('app.services.google_oauth.jwt.decode')
    @patch('app.services.google_oauth.Flow')
    async def test_handle_oauth_callback_updates_user_status(self, mock_flow, mock_jwt_decode, mock_get_mongo_client):
        """Test that OAuth callback properly updates user's Gmail connection status."""
        service = GoogleOAuthService()
        
        # Mock OAuth flow
        mock_flow_instance = Mock()
        mock_credentials = Mock()
        mock_credentials.token = "access_token_123"
        mock_credentials.refresh_token = "refresh_token_123"
        mock_credentials.scopes = ["openid", "https://www.googleapis.com/auth/gmail.readonly"]
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        mock_credentials.expiry = None
        mock_flow_instance.credentials = mock_credentials
        mock_flow.from_client_config.return_value = mock_flow_instance
        
        # Mock JWT decode
        mock_jwt_decode.return_value = {
            "sub": "google_user_123",
            "email": "test@gmail.com",
            "name": "Test User"
        }
        
        # Mock database
        mock_db = Mock()
        mock_oauth_collection = AsyncMock()
        mock_users_collection = AsyncMock()
        mock_db.__getitem__.side_effect = lambda x: mock_oauth_collection if "oauth" in x else mock_users_collection
        mock_get_mongo_client.return_value = mock_db
        
        # Test callback handling
        result = await service.handle_oauth_callback(
            code="auth_code_123",
            state="state_123", 
            clerk_user_id="user_2xYk123"
        )
        
        # Verify OAuth credentials were stored
        mock_oauth_collection.update_one.assert_called_once()
        
        # Verify user's Gmail connection status was updated
        mock_users_collection.update_one.assert_called_once()
        call_args = mock_users_collection.update_one.call_args
        assert call_args[0][0] == {"clerk_user_id": "user_2xYk123"}
        
        # Check that is_gmail_connected was set to True
        update_data = call_args[0][1]["$set"]
        assert update_data["is_gmail_connected"] is True
        assert update_data["gmail_email"] == "test@gmail.com"
        assert "gmail_connected_at" in update_data
        
        # Verify result
        assert result["success"] is True
        assert result["is_gmail_connected"] is True
        assert result["email"] == "test@gmail.com"
    
    @pytest.mark.asyncio
    @patch('app.services.google_oauth.get_mongo_client')
    async def test_revoke_user_access_updates_user_status(self, mock_get_mongo_client):
        """Test that revoking access properly updates user's Gmail connection status."""
        service = GoogleOAuthService()
        
        # Mock database
        mock_db = Mock()
        mock_oauth_collection = AsyncMock()
        mock_users_collection = AsyncMock()
        mock_oauth_collection.delete_one.return_value = Mock(deleted_count=1)
        mock_db.__getitem__.side_effect = lambda x: mock_oauth_collection if "oauth" in x else mock_users_collection
        mock_get_mongo_client.return_value = mock_db
        
        # Test revocation
        result = await service.revoke_user_access("user_2xYk123")
        
        # Verify OAuth credentials were deleted
        mock_oauth_collection.delete_one.assert_called_once_with({"user_id": "user_2xYk123"})
        
        # Verify user's Gmail connection status was updated
        mock_users_collection.update_one.assert_called_once()
        call_args = mock_users_collection.update_one.call_args
        assert call_args[0][0] == {"clerk_user_id": "user_2xYk123"}
        
        # Check that is_gmail_connected was set to False
        update_data = call_args[0][1]["$set"]
        assert update_data["is_gmail_connected"] is False
        assert update_data["gmail_email"] is None
        assert update_data["gmail_connected_at"] is None
        
        # Verify result
        assert result is True

class TestGmailWorkflowIntegration:
    """Integration tests for the complete Gmail workflow."""
    
    def test_gmail_scopes_match_requirements(self):
        """Test that Gmail scopes match the workflow requirements."""
        from app.services.google_oauth import GMAIL_SCOPES
        
        expected_scopes = [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.labels",
            "https://www.googleapis.com/auth/gmail.settings.basic"
        ]
        
        assert GMAIL_SCOPES == expected_scopes
        assert len(GMAIL_SCOPES) == 8
    
    def test_user_model_includes_gmail_fields(self):
        """Test that UserInDB model includes Gmail connection fields."""
        from app.models.user import UserInDB
        
        # Create a user instance
        user = UserInDB(
            clerk_user_id="user_2xYk123",
            email="test@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Check that Gmail fields are present with default values
        assert hasattr(user, "is_gmail_connected")
        assert user.is_gmail_connected is False
        assert hasattr(user, "gmail_email")
        assert user.gmail_email is None
        assert hasattr(user, "gmail_connected_at")
        assert user.gmail_connected_at is None
    
    def test_gmail_status_model(self):
        """Test the UserGmailStatus model."""
        user_status = UserGmailStatus(
            user_id="user_2xYk123",
            is_gmail_connected=True,
            gmail_email="test@gmail.com",
            gmail_connected_at=datetime.utcnow(),
            message="Gmail connected"
        )
        
        assert user_status.user_id == "user_2xYk123"
        assert user_status.is_gmail_connected is True
        assert user_status.gmail_email == "test@gmail.com"
        assert user_status.message == "Gmail connected"
    
    def test_gmail_tokens_model(self):
        """Test the GmailTokens model."""
        tokens = GmailTokens(
            access_token="access_token_123",
            refresh_token="refresh_token_123",
            expires_at=datetime.utcnow()
        )
        
        assert tokens.access_token == "access_token_123"
        assert tokens.refresh_token == "refresh_token_123"
        assert isinstance(tokens.expires_at, datetime) 