"""Test suite for CQTech Metrics SDK"""
import unittest
import os
from unittest.mock import Mock, patch, MagicMock
from cqtech_metrics import CQTechClient
from cqtech_metrics.models.auth import TokenResponse, TokenResponseData
from cqtech_metrics.models.scenes import SceneVersionQuery
from cqtech_metrics.models.metrics import MetricQuery


class TestCQTechClient(unittest.TestCase):
    """Test cases for CQTechClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use environment variables for testing if available, otherwise use test values
        self.base_url = os.getenv('CQTECH_BASE_URL', 'https://test-api.example.com')
        self.app_key = os.getenv('CQTECH_APP_KEY', 'test_app_key')
        self.secret = os.getenv('CQTECH_SECRET', 'test_secret')
        self.username = os.getenv('CQTECH_USERNAME', 'test_username')
        self.client = CQTechClient(
            base_url=self.base_url,
            app_key=self.app_key,
            secret=self.secret,
            username=self.username
        )
    
    @patch('cqtech_metrics.auth.CQTechAuthClient.authenticate')
    @patch('requests.Session.post')
    def test_client_initialization(self, mock_post, mock_auth):
        """Test client initialization"""
        # Mock successful authentication
        mock_auth.return_value = TokenResponse(
            code=0,
            data=TokenResponseData(
                scope=None,
                access_token='test_token',
                refresh_token=None,
                token_type='bearer',
                expires_in=1800
            )
        )
        
        # Mock the token endpoint response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'data': {
                'scope': None,
                'access_token': 'test_token',
                'refresh_token': None,
                'token_type': 'bearer',
                'expires_in': 1800
            },
            'msg': ''
        }
        mock_post.return_value = mock_response
        
        # Verify client properties
        self.assertEqual(self.client.base_url, self.base_url)
        self.assertEqual(self.client.app_key, self.app_key)
        self.assertEqual(self.client.secret, self.secret)
        self.assertEqual(self.client.username, self.username)
    
    @patch('cqtech_metrics.auth.CQTechAuthClient.authenticate')
    @patch('requests.Session.request')
    def test_query_all_scene_versions(self, mock_request, mock_auth):
        """Test querying all scene versions"""
        # Mock authentication
        mock_auth_response = TokenResponse(
            code=0,
            data=TokenResponseData(
                scope=None,
                access_token='test_token',
                refresh_token=None,
                token_type='bearer',
                expires_in=1800
            )
        )
        mock_auth.return_value = mock_auth_response
        
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'data': {
                'list': [],
                'total': 0
            },
            'msg': ''
        }
        mock_request.return_value = mock_response
        
        # Create query parameters
        query = SceneVersionQuery(
            page_num=1,
            page_size=10
        )
        
        # Execute the method
        result = self.client.query_all_scene_versions(query)
        
        # Verify the call was made
        mock_request.assert_called_once()
        
        # Verify response
        self.assertEqual(result.code, 0)
    
    @patch('cqtech_metrics.auth.CQTechAuthClient.authenticate')
    @patch('requests.Session.request')
    def test_query_metric_results_by_codes(self, mock_request, mock_auth):
        """Test querying metric results by codes"""
        # Mock authentication
        mock_auth_response = TokenResponse(
            code=0,
            data=TokenResponseData(
                scope=None,
                access_token='test_token',
                refresh_token=None,
                token_type='bearer',
                expires_in=1800
            )
        )
        mock_auth.return_value = mock_auth_response
        
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'data': {},
            'msg': ''
        }
        mock_request.return_value = mock_response
        
        # Create query parameters
        query = MetricQuery(
            scene_version_uid="test-uid",
            instance_codes=["test_code"]
        )
        
        # Execute the method
        result = self.client.query_metric_results_by_codes(query)
        
        # Verify the call was made
        mock_request.assert_called_once()
        
        # Verify response
        self.assertEqual(result.code, 0)
    
    def test_client_context_manager(self):
        """Test client context manager functionality"""
        with CQTechClient(
            base_url=self.base_url,
            app_key=self.app_key,
            secret=self.secret,
            username=self.username
        ) as client:
            self.assertIsNotNone(client.session)
        
        # After context exit, session should be closed
        # (Note: In a real test, we'd check if session.close() was called)
    
    def tearDown(self):
        """Clean up after tests"""
        self.client.close()


if __name__ == '__main__':
    unittest.main()