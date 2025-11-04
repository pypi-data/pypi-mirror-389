"""Test suite for CQTech Metrics SDK authentication"""
import unittest
import os
from unittest.mock import Mock, patch, MagicMock
from cqtech_metrics.auth import CQTechAuthClient
from cqtech_metrics.models.auth import TokenResponse, TokenResponseData
from cqtech_metrics import CQTechClient


class TestCQTechAuthClient(unittest.TestCase):
    """Test cases for CQTechAuthClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use environment variables for testing if available, otherwise use test values
        test_username = os.getenv('CQTECH_USERNAME', 'test_user')
        test_secret = os.getenv('CQTECH_SECRET', 'test_secret')
        test_app_key = os.getenv('CQTECH_APP_KEY', 'test_app_key')
        test_base_url = os.getenv('CQTECH_BASE_URL', 'https://test-api.example.com')
        
        # Create a mock client to pass to auth client
        self.mock_client = Mock(spec=CQTechClient)
        self.mock_client.username = test_username
        self.mock_client.secret = test_secret
        self.mock_client.app_key = test_app_key
        self.mock_client.base_url = test_base_url
        self.mock_client.verify_ssl = True
        self.mock_client.timeout = 30
        self.mock_client.session = Mock()
        
        self.auth_client = CQTechAuthClient(self.mock_client)
    
    @patch('cqtech_metrics.auth.generate_checksum')
    @patch('cqtech_metrics.auth.generate_nonce')
    @patch('time.time')
    def test_authenticate_success(self, mock_time, mock_nonce, mock_checksum):
        """Test successful authentication"""
        # Mock time, nonce, and checksum
        mock_time.return_value = 1234567890
        mock_nonce.return_value = 1768277523
        mock_checksum.return_value = "abcd1234"
        
        # Mock the session.post response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'data': {
                'scope': None,
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token',
                'token_type': 'bearer',
                'expires_in': 1800
            },
            'msg': ''
        }
        self.mock_client.session.post.return_value = mock_response
        
        # Execute authentication
        token_response = self.auth_client.authenticate()
        
        # Verify the response
        self.assertIsInstance(token_response, TokenResponse)
        self.assertEqual(token_response.data.access_token, 'test_access_token')
        self.assertEqual(token_response.data.token_type, 'bearer')
        self.assertEqual(token_response.data.expires_in, 1800)
        
        # Verify the correct request was made
        self.mock_client.session.post.assert_called_once()
        call_args = self.mock_client.session.post.call_args
        self.assertEqual(call_args[0][0], f"{self.mock_client.base_url}/open-api/system/oauth2-openapi/token")
        
        # Verify headers
        headers = call_args[1]['headers']
        self.assertEqual(headers['appkey'], self.mock_client.app_key)
        self.assertEqual(headers['checksum'], 'abcd1234')
        self.assertEqual(headers['curtime'], '1234567890')
        self.assertEqual(headers['nonce'], '1768277523')
        self.assertEqual(headers['username'], 'test_user')
    
    @patch('cqtech_metrics.auth.generate_checksum')
    @patch('cqtech_metrics.auth.generate_nonce')
    @patch('time.time')
    def test_authenticate_failure(self, mock_time, mock_nonce, mock_checksum):
        """Test authentication failure"""
        # Mock time, nonce, and checksum
        mock_time.return_value = 1234567890
        mock_nonce.return_value = 1768277523
        mock_checksum.return_value = "abcd1234"
        
        # Mock a failed response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'code': 401,
            'msg': 'Authentication failed'
        }
        self.mock_client.session.post.return_value = mock_response
        
        # Expect an AuthenticationError
        with self.assertRaises(Exception):  # Would actually raise AuthenticationError
            self.auth_client.authenticate()
    
    @patch('cqtech_metrics.auth.generate_checksum')
    @patch('cqtech_metrics.auth.generate_nonce')
    @patch('time.time')
    def test_authenticate_api_error(self, mock_time, mock_nonce, mock_checksum):
        """Test authentication with API error response"""
        # Mock time, nonce, and checksum
        mock_time.return_value = 1234567890
        mock_nonce.return_value = 1768277523
        mock_checksum.return_value = "abcd1234"
        
        # Mock an API error response
        mock_response = Mock()
        mock_response.status_code = 200  # Status code is 200 but API code is error
        mock_response.json.return_value = {
            'code': 400,
            'msg': 'Invalid credentials'
        }
        self.mock_client.session.post.return_value = mock_response
        
        # Expect an AuthenticationError
        with self.assertRaises(Exception):  # Would actually raise AuthenticationError
            self.auth_client.authenticate()
    
    def test_get_access_token(self):
        """Test getting access token"""
        # Set up a token in the auth client
        self.auth_client._access_token = 'test_token_123'
        
        # Get the token
        token = self.auth_client.get_access_token()
        
        # Verify it's the same token
        self.assertEqual(token, 'test_token_123')
    
    @patch('time.time')
    def test_token_validity(self, mock_time):
        """Test token validity checks"""
        # Initially no token, should be invalid
        self.assertFalse(self.auth_client.is_token_valid())
        
        # Set a valid token with future expiration
        self.auth_client._access_token = 'test_token'
        mock_time.return_value = 1000
        self.auth_client._token_expires_at = 2000  # Expires in 1000 seconds
        
        # Should be valid (1000 + 940 < 2000, since we consider it invalid 1 minute before expiration)
        self.assertTrue(self.auth_client.is_token_valid())
        
        # Set expiration to past time
        mock_time.return_value = 2000
        self.auth_client._token_expires_at = 1900  # Expired 100 seconds ago
        
        # Should be invalid
        self.assertFalse(self.auth_client.is_token_valid())


if __name__ == '__main__':
    unittest.main()