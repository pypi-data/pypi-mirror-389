"""Tests for LoadBalancer class."""

import unittest
from unittest.mock import Mock, patch
import requests
from requests_load_balancer import LoadBalancer


class TestLoadBalancer(unittest.TestCase):
    """Test cases for LoadBalancer."""
    
    def test_initialization_with_hosts(self):
        """Test LoadBalancer initializes with hosts."""
        hosts = ['http://host1.com', 'http://host2.com']
        lb = LoadBalancer(hosts)
        self.assertEqual(lb.hosts, hosts)
    
    def test_initialization_strips_trailing_slashes(self):
        """Test that trailing slashes are stripped from hosts."""
        hosts = ['http://host1.com/', 'http://host2.com/']
        lb = LoadBalancer(hosts)
        self.assertEqual(lb.hosts, ['http://host1.com', 'http://host2.com'])
    
    def test_initialization_without_hosts_raises_error(self):
        """Test that initializing without hosts raises ValueError."""
        with self.assertRaises(ValueError):
            LoadBalancer([])
    
    def test_default_error_codes(self):
        """Test default error codes are set correctly."""
        lb = LoadBalancer(['http://host1.com'])
        self.assertEqual(lb.error_codes, {500, 502, 503, 504})
    
    def test_custom_error_codes(self):
        """Test custom error codes can be set."""
        custom_codes = {400, 404, 500}
        lb = LoadBalancer(['http://host1.com'], error_codes=custom_codes)
        self.assertEqual(lb.error_codes, custom_codes)
    
    @patch('requests_load_balancer.load_balancer.requests.request')
    def test_get_request(self, mock_request):
        """Test GET request is made correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        lb = LoadBalancer(['http://host1.com'])
        response = lb.get('/api/test')
        
        mock_request.assert_called_once_with('GET', 'http://host1.com/api/test')
        self.assertEqual(response, mock_response)
    
    @patch('requests_load_balancer.load_balancer.requests.request')
    def test_post_request(self, mock_request):
        """Test POST request is made correctly."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_request.return_value = mock_response
        
        lb = LoadBalancer(['http://host1.com'])
        response = lb.post('/api/test', json={'key': 'value'})
        
        mock_request.assert_called_once_with('POST', 'http://host1.com/api/test', json={'key': 'value'})
        self.assertEqual(response, mock_response)
    
    @patch('requests_load_balancer.load_balancer.requests.request')
    def test_round_robin_distribution(self, mock_request):
        """Test that requests are distributed in round-robin fashion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        hosts = ['http://host1.com', 'http://host2.com', 'http://host3.com']
        lb = LoadBalancer(hosts)
        
        # Make requests and collect which hosts were used
        lb.get('/test')
        call1_url = mock_request.call_args[0][1]
        
        lb.get('/test')
        call2_url = mock_request.call_args[0][1]
        
        lb.get('/test')
        call3_url = mock_request.call_args[0][1]
        
        # Should cycle through hosts
        self.assertIn('host1.com', call1_url)
        self.assertIn('host2.com', call2_url)
        self.assertIn('host3.com', call3_url)
    
    @patch('requests_load_balancer.load_balancer.requests.request')
    def test_marks_host_unhealthy_on_error_code(self, mock_request):
        """Test that host is marked unhealthy on error code."""
        mock_response_error = Mock()
        mock_response_error.status_code = 500
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        
        mock_request.side_effect = [mock_response_error, mock_response_success]
        
        hosts = ['http://host1.com', 'http://host2.com']
        lb = LoadBalancer(hosts)
        
        response = lb.get('/test')
        
        # First host should be marked unhealthy
        self.assertIn('http://host1.com', lb.unhealthy_hosts)
        # Should have tried second host
        self.assertEqual(mock_request.call_count, 2)
        self.assertEqual(response, mock_response_success)
    
    @patch('requests_load_balancer.load_balancer.requests.request')
    def test_marks_host_unhealthy_on_connection_error(self, mock_request):
        """Test that host is marked unhealthy on connection error."""
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        
        mock_request.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            mock_response_success
        ]
        
        hosts = ['http://host1.com', 'http://host2.com']
        lb = LoadBalancer(hosts)
        
        response = lb.get('/test')
        
        # First host should be marked unhealthy
        self.assertIn('http://host1.com', lb.unhealthy_hosts)
        # Should have successfully used second host
        self.assertEqual(response, mock_response_success)
    
    @patch('requests_load_balancer.load_balancer.requests.request')
    def test_raises_error_when_all_hosts_unhealthy(self, mock_request):
        """Test that RuntimeError is raised when all hosts are unhealthy."""
        mock_response_error = Mock()
        mock_response_error.status_code = 503
        mock_request.return_value = mock_response_error
        
        hosts = ['http://host1.com', 'http://host2.com']
        lb = LoadBalancer(hosts)
        
        with self.assertRaises(RuntimeError) as context:
            lb.get('/test')
        
        self.assertIn("All hosts are unhealthy", str(context.exception))
    
    def test_reset_health(self):
        """Test that reset_health clears unhealthy hosts."""
        lb = LoadBalancer(['http://host1.com', 'http://host2.com'])
        lb.unhealthy_hosts['http://host1.com'] = 0
        
        lb.reset_health()
        
        self.assertEqual(len(lb.unhealthy_hosts), 0)
    
    def test_get_healthy_hosts(self):
        """Test get_healthy_hosts returns only healthy hosts."""
        hosts = ['http://host1.com', 'http://host2.com', 'http://host3.com']
        lb = LoadBalancer(hosts)
        lb.unhealthy_hosts['http://host2.com'] = 0
        
        healthy = lb.get_healthy_hosts()
        
        self.assertEqual(len(healthy), 2)
        self.assertIn('http://host1.com', healthy)
        self.assertIn('http://host3.com', healthy)
        self.assertNotIn('http://host2.com', healthy)
    
    def test_get_unhealthy_hosts(self):
        """Test get_unhealthy_hosts returns unhealthy hosts."""
        hosts = ['http://host1.com', 'http://host2.com', 'http://host3.com']
        lb = LoadBalancer(hosts)
        lb.unhealthy_hosts['http://host2.com'] = 0
        
        unhealthy = lb.get_unhealthy_hosts()
        
        self.assertEqual(len(unhealthy), 1)
        self.assertIn('http://host2.com', unhealthy)
    
    @patch('requests_load_balancer.load_balancer.requests.request')
    def test_put_request(self, mock_request):
        """Test PUT request is made correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        lb = LoadBalancer(['http://host1.com'])
        response = lb.put('/api/test', json={'key': 'value'})
        
        mock_request.assert_called_once_with('PUT', 'http://host1.com/api/test', json={'key': 'value'})
        self.assertEqual(response, mock_response)
    
    @patch('requests_load_balancer.load_balancer.requests.request')
    def test_delete_request(self, mock_request):
        """Test DELETE request is made correctly."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_request.return_value = mock_response
        
        lb = LoadBalancer(['http://host1.com'])
        response = lb.delete('/api/test')
        
        mock_request.assert_called_once_with('DELETE', 'http://host1.com/api/test')
        self.assertEqual(response, mock_response)
    
    @patch('requests_load_balancer.load_balancer.requests.request')
    def test_patch_request(self, mock_request):
        """Test PATCH request is made correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        lb = LoadBalancer(['http://host1.com'])
        response = lb.patch('/api/test', json={'key': 'value'})
        
        mock_request.assert_called_once_with('PATCH', 'http://host1.com/api/test', json={'key': 'value'})
        self.assertEqual(response, mock_response)
    
    @patch('requests_load_balancer.load_balancer.time.time')
    @patch('requests_load_balancer.load_balancer.requests.request')
    def test_skips_unhealthy_hosts_in_rotation(self, mock_request, mock_time):
        """Test that unhealthy hosts are skipped in rotation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        # Keep time constant so unhealthy host doesn't expire
        mock_time.return_value = 100
        
        hosts = ['http://host1.com', 'http://host2.com', 'http://host3.com']
        lb = LoadBalancer(hosts)
        
        # Mark host2 as unhealthy at time 100
        lb.unhealthy_hosts['http://host2.com'] = 100
        
        # Make multiple requests
        lb.get('/test')
        call1_url = mock_request.call_args[0][1]
        
        lb.get('/test')
        call2_url = mock_request.call_args[0][1]
        
        lb.get('/test')
        call3_url = mock_request.call_args[0][1]
        
        # Should not use host2
        self.assertNotIn('host2.com', call1_url)
        self.assertNotIn('host2.com', call2_url)
        self.assertNotIn('host2.com', call3_url)
    
    def test_default_unhealthy_timeout(self):
        """Test that default unhealthy timeout is set."""
        lb = LoadBalancer(['http://host1.com'])
        self.assertEqual(lb.unhealthy_timeout, 60)
    
    def test_custom_unhealthy_timeout(self):
        """Test that custom unhealthy timeout can be set."""
        lb = LoadBalancer(['http://host1.com'], unhealthy_timeout=30)
        self.assertEqual(lb.unhealthy_timeout, 30)
    
    def test_unhealthy_timeout_disabled(self):
        """Test that unhealthy timeout can be disabled."""
        lb = LoadBalancer(['http://host1.com'], unhealthy_timeout=None)
        self.assertIsNone(lb.unhealthy_timeout)
    
    @patch('requests_load_balancer.load_balancer.time.time')
    @patch('requests_load_balancer.load_balancer.requests.request')
    def test_unhealthy_host_recovery_after_timeout(self, mock_request, mock_time):
        """Test that unhealthy hosts are retried after timeout expires."""
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_request.return_value = mock_response_success
        
        # Start at time 0
        mock_time.return_value = 0
        
        hosts = ['http://host1.com', 'http://host2.com']
        lb = LoadBalancer(hosts, unhealthy_timeout=10)
        
        # Manually mark host1 as unhealthy at time 0
        lb.unhealthy_hosts['http://host1.com'] = 0
        
        # At time 5, host1 should still be unhealthy
        mock_time.return_value = 5
        healthy = lb.get_healthy_hosts()
        self.assertEqual(healthy, ['http://host2.com'])
        
        # At time 10+, host1 should be recovered
        mock_time.return_value = 11
        lb._cleanup_expired_unhealthy_hosts()
        healthy = lb.get_healthy_hosts()
        self.assertIn('http://host1.com', healthy)
        self.assertEqual(len(healthy), 2)
    
    @patch('requests_load_balancer.load_balancer.time.time')
    @patch('requests_load_balancer.load_balancer.requests.request')
    def test_no_recovery_when_timeout_disabled(self, mock_request, mock_time):
        """Test that hosts don't recover when timeout is disabled."""
        mock_time.return_value = 0
        
        hosts = ['http://host1.com', 'http://host2.com']
        lb = LoadBalancer(hosts, unhealthy_timeout=None)
        
        # Mark host1 as unhealthy
        lb.unhealthy_hosts['http://host1.com'] = 0
        
        # Even after time passes, host1 should remain unhealthy
        mock_time.return_value = 1000
        lb._cleanup_expired_unhealthy_hosts()
        healthy = lb.get_healthy_hosts()
        self.assertEqual(healthy, ['http://host2.com'])
    
    @patch('requests_load_balancer.load_balancer.time.time')
    @patch('requests_load_balancer.load_balancer.requests.request')
    def test_expired_unhealthy_host_used_in_rotation(self, mock_request, mock_time):
        """Test that expired unhealthy hosts are used in rotation again."""
        mock_response_error = Mock()
        mock_response_error.status_code = 500
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        
        # First request at time 0 - host1 returns error
        mock_time.return_value = 0
        mock_request.side_effect = [mock_response_error, mock_response_success, mock_response_success]
        
        hosts = ['http://host1.com', 'http://host2.com']
        lb = LoadBalancer(hosts, unhealthy_timeout=5)
        
        # First request marks host1 as unhealthy
        response = lb.get('/test')
        self.assertIn('http://host1.com', lb.unhealthy_hosts)
        
        # Time passes beyond timeout
        mock_time.return_value = 10
        
        # Next request should try host1 again (it will be cleaned up)
        response = lb.get('/test')
        # After cleanup, host1 should be available again
        self.assertNotIn('http://host1.com', lb.unhealthy_hosts)


if __name__ == '__main__':
    unittest.main()
