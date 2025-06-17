# app/core/oauth.py
from authlib.integrations.starlette_client import OAuth, OAuthError
from app.core.config import settings
from typing import Optional, Any, Dict
from starlette.requests import Request

class GoogleClient:
    def __init__(self, oauth: OAuth):
        self._client = oauth.google
        if self._client is None:
            raise RuntimeError("Google OAuth client not initialized")

    async def authorize_redirect(self, request: Request, redirect_uri: str):
        if self._client is None:
            raise RuntimeError("Google OAuth client not initialized")
        return await self._client.authorize_redirect(request, redirect_uri)

    async def authorize_access_token(self, request: Request) -> Dict:
        if self._client is None:
            raise RuntimeError("Google OAuth client not initialized")
        return await self._client.authorize_access_token(request)

    async def userinfo(self, token: Dict) -> Dict:
        if self._client is None:
            raise RuntimeError("Google OAuth client not initialized")
        return await self._client.userinfo(token=token)

class OAuthClient:
    def __init__(self):
        self._oauth: Optional[OAuth] = None
        self._google: Optional[GoogleClient] = None

    @property
    def oauth(self) -> OAuth:
        if self._oauth is None:
            self._oauth = OAuth()
            self._oauth.register(
                name='google',
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                access_token_url='https://oauth2.googleapis.com/token',
                authorize_url='https://accounts.google.com/o/oauth2/auth',
                api_base_url='https://www.googleapis.com/oauth2/v1/',
                userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
                client_kwargs={
                    'scope': 'openid email profile https://www.googleapis.com/auth/gmail.readonly',
                    'redirect_uri': settings.GOOGLE_REDIRECT_URI
                }
            )
        return self._oauth

    @property
    def google(self) -> GoogleClient:
        if self._google is None:
            self._google = GoogleClient(self.oauth)
        return self._google

oauth_client = OAuthClient()
oauth = oauth_client.oauth
oauth.google = oauth_client.google
