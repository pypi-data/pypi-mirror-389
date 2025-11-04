"""Authentication client for CQTech Metrics SDK"""
import time
from typing import Optional
from .models.auth import TokenResponse
from .utils import generate_checksum, generate_nonce
from .exceptions import AuthenticationError


class CQTechAuthClient:
    """Authentication client for handling token operations (API endpoint 1: 获取APP令牌)
    
    This client handles authentication with the CQTech Metrics API by obtaining 
    access tokens using the OAuth2 API. The authentication interface requires 
    specific parameters to generate a secure checksum for verification.
    
    The authentication process includes:
    - Generating a 10-digit random number (nonce)
    - Getting current timestamp in seconds (curtime)
    - Creating a checksum using SHA1 encryption of username, secret, nonce, and curtime
    - Sending authentication request with required headers
    
    API Endpoint: POST /open-api/system/oauth2-openapi/token
    
    Required header parameters:
    - appkey: Application key assigned to the client
    - checksum: Authentication checksum generated from credentials
    - curtime: Current timestamp when the request is made
    - nonce: Random number to prevent replay attacks
    - username: Username of the requesting user
    
    Response includes:
    - access_token: Token for subsequent API requests
    - refresh_token: Token for refreshing access token (not currently used)
    - token_type: Type of token (always 'bearer')
    - expires_in: Time in seconds until token expiration
    """
    
    def __init__(self, client: 'CQTechClient'):
        self.client = client
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[int] = None
    
    def authenticate(self) -> TokenResponse:
        """
        Authenticate with the API and get an access token (API endpoint 1: 获取APP令牌)
        
        This method performs authentication with the CQTech Metrics API by making 
        a POST request to the authentication endpoint. It follows the required 
        authentication flow by generating necessary parameters and creating a 
        secure checksum for verification.
        
        The authentication process:
        1. Generates a 10-digit random nonce
        2. Gets current timestamp in seconds
        3. Creates checksum using username, secret, nonce, and curtime via SHA1
        4. Makes POST request to /open-api/system/oauth2-openapi/token
        5. Validates response and parses token information
        6. Caches the token for future use
        
        Required parameters are obtained from the parent client:
        - client.app_key: Application key
        - client.secret: Application secret 
        - client.username: Username
        - client.base_url: Base API URL
        
        Returns:
            TokenResponse: Response object containing:
                - access_token: Authentication token for API requests
                - refresh_token: Token for refreshing access (currently unused)
                - token_type: Token type (typically 'bearer')
                - expires_in: Seconds until token expiration
        
        Raises:
            AuthenticationError: If authentication fails due to invalid response
                               or non-zero response code
        
        Example:
            auth_client = CQTechAuthClient(client)
            token_response = auth_client.authenticate()
            access_token = token_response.data.access_token
        """
        # Generate authentication parameters
        nonce = generate_nonce()
        curtime = int(time.time())
        checksum = generate_checksum(self.client.username, self.client.secret, nonce, curtime)
        
        # Prepare headers for authentication
        headers = {
            "appkey": self.client.app_key,
            "checksum": checksum,
            "curtime": str(curtime),
            "nonce": str(nonce),
            "username": self.client.username
        }
        
        # Make the authentication request
        response_data = self.client.session.post(
            f"{self.client.base_url}/open-api/system/oauth2-openapi/token",
            headers=headers,
            verify=self.client.verify_ssl,
            timeout=self.client.timeout
        )
        
        if response_data.status_code != 200:
            raise AuthenticationError(f"Authentication failed with status {response_data.status_code}")
        
        response_json = response_data.json()
        
        if response_json.get('code') != 0:
            raise AuthenticationError(f"Authentication failed: {response_json.get('msg', 'Unknown error')}")
        
        # Parse the response
        token_response = TokenResponse(**response_json)
        
        # Cache the token and expiration time
        self._access_token = token_response.data.accessToken
        self._token_expires_at = int(time.time()) + token_response.data.expiresIn
        
        # Also update the main client's token cache
        self.client._access_token = self._access_token
        self.client._token_expires_at = self._token_expires_at
        
        return token_response
    
    def get_access_token(self) -> Optional[str]:
        """Get the current access token.
        
        Returns the cached access token obtained from the authentication process.
        This token is used in the Authorization header for subsequent API requests
        in the format 'Bearer {access_token}'.
        
        Returns:
            Optional[str]: The current access token if available, None otherwise
        """
        return self._access_token
    
    def is_token_valid(self) -> bool:
        """Check if the current token is still valid.
        
        Validates if the cached access token is still within its expiration window.
        The token is considered invalid 60 seconds before its actual expiration 
        time to account for potential clock differences and allow for timely 
        refresh before complete expiration.
        
        Returns:
            bool: True if token exists and is still valid, False otherwise
        """
        if not self._access_token or not self._token_expires_at:
            return False
        return time.time() < self._token_expires_at - 60  # Consider invalid 1 minute before expiration