import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.google_oauth import GoogleOAuthService, GMAIL_SCOPES
from app.core.config import settings

class TestGoogleOAuthService:
    """Test cases for Google OAuth service."""
    
    def test_gmail_scopes(self):
        """Test that Gmail scopes are correctly defined."""
        expected_scopes = [
            "openid",
            "email", 
            "profile",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.labels",
            "https://www.googleapis.com/auth/gmail.settings.basic"
        ]
        
        assert GMAIL_SCOPES == expected_scopes
        assert len(GMAIL_SCOPES) == 8
    
    def test_oauth_service_initialization(self):
        """Test OAuth service initialization."""
        service = GoogleOAuthService()
        
        assert service.client_id == settings.GOOGLE_CLIENT_ID
        assert service.client_secret == settings.GOOGLE_CLIENT_SECRET
        assert service.redirect_uri == settings.GOOGLE_REDIRECT_URI
    
    @patch('app.services.google_oauth.Flow')
    def test_create_oauth_flow(self, mock_flow):
        """Test OAuth flow creation."""
        service = GoogleOAuthService()
        mock_flow_instance = Mock()
        mock_flow.from_client_config.return_value = mock_flow_instance
        
        flow = service.create_oauth_flow()
        
        mock_flow.from_client_config.assert_called_once()
        assert flow == mock_flow_instance
    
    @patch('app.services.google_oauth.Flow')
    def test_generate_auth_url(self, mock_flow):
        """Test OAuth URL generation."""
        service = GoogleOAuthService()
        mock_flow_instance = Mock()
        mock_flow_instance.authorization_url.return_value = ("https://example.com/auth", "state123")
        mock_flow.from_client_config.return_value = mock_flow_instance
        
        auth_url, state = service.generate_auth_url()
        
        assert auth_url == "https://example.com/auth"
        assert state == "state123"
        mock_flow_instance.authorization_url.assert_called_once_with(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true"
        )

@pytest.mark.asyncio
class TestGoogleOAuthAsync:
    """Test cases for async OAuth methods."""
    
    @patch('app.services.google_oauth.get_mongo_client')
    @patch('app.services.google_oauth.jwt.decode')
    @patch('app.services.google_oauth.Flow')
    async def test_handle_oauth_callback(self, mock_flow, mock_jwt_decode, mock_get_mongo_client):
        """Test OAuth callback handling."""
        service = GoogleOAuthService()
        
        # Mock dependencies
        mock_flow_instance = Mock()
        mock_credentials = Mock()
        mock_credentials.token = "access_token_123"
        mock_credentials.refresh_token = "refresh_token_123"
        mock_credentials.scopes = GMAIL_SCOPES
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        mock_credentials.expiry = None
        mock_flow_instance.credentials = mock_credentials
        mock_flow.from_client_config.return_value = mock_flow_instance
        
        mock_jwt_decode.return_value = {
            "sub": "google_user_123",
            "email": "test@example.com",
            "name": "Test User"
        }
        
        mock_db = Mock()
        mock_collection = AsyncMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_get_mongo_client.return_value = mock_db
        
        # Test callback handling
        result = await service.handle_oauth_callback(
            code="auth_code_123",
            state="state_123", 
            clerk_user_id="clerk_user_123"
        )
        
        assert result["success"] is True
        assert result["user_id"] == "clerk_user_123"
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"
        
        # Verify database update was called
        mock_collection.update_one.assert_called_once()
    
    @patch('app.services.google_oauth.get_mongo_client')
    async def test_get_user_credentials_not_found(self, mock_get_mongo_client):
        """Test getting user credentials when not found."""
        service = GoogleOAuthService()
        
        mock_db = Mock()
        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = None
        mock_db.__getitem__.return_value = mock_collection
        mock_get_mongo_client.return_value = mock_db
        
        credentials = await service.get_user_credentials("user_123")
        
        assert credentials is None
    
    @patch('app.services.google_oauth.get_mongo_client')
    async def test_revoke_user_access(self, mock_get_mongo_client):
        """Test revoking user access."""
        service = GoogleOAuthService()
        
        mock_db = Mock()
        mock_collection = AsyncMock()
        mock_collection.delete_one.return_value = Mock(deleted_count=1)
        mock_db.__getitem__.return_value = mock_collection
        mock_get_mongo_client.return_value = mock_db
        
        result = await service.revoke_user_access("user_123")
        
        assert result is True
        mock_collection.delete_one.assert_called_once_with({"user_id": "user_123"}) 