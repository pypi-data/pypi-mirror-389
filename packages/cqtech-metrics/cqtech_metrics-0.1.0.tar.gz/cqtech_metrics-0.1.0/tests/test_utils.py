"""Test suite for CQTech Metrics SDK utilities"""
import unittest
import hashlib
from cqtech_metrics import utils


class TestUtils(unittest.TestCase):
    """Test cases for utility functions"""
    
    def test_generate_checksum(self):
        """Test checksum generation"""
        username = "test_user"
        secret = "test_secret"
        nonce = 1234567890
        curtime = 9876543210
        
        # Calculate expected checksum manually
        check_sum_builder = f"{username}{secret}{nonce}{curtime}"
        expected_checksum = hashlib.sha1(check_sum_builder.encode()).hexdigest()
        
        # Generate checksum with utility function
        actual_checksum = utils.generate_checksum(username, secret, nonce, curtime)
        
        # Verify they match
        self.assertEqual(actual_checksum, expected_checksum)
    
    def test_generate_nonce(self):
        """Test nonce generation"""
        # Generate a nonce
        nonce = utils.generate_nonce()
        
        # Verify it's an integer
        self.assertIsInstance(nonce, int)
        
        # Verify it's a 10-digit number
        self.assertGreaterEqual(nonce, 1000000000)  # 10 digits minimum
        self.assertLessEqual(nonce, 9999999999)     # 10 digits maximum
    
    def test_format_auth_header(self):
        """Test authorization header formatting"""
        access_token = "test_token_123"
        
        # Format the header
        header = utils.format_auth_header(access_token)
        
        # Verify the format
        self.assertEqual(header, {"Authorization": "Bearer test_token_123"})


if __name__ == '__main__':
    unittest.main()