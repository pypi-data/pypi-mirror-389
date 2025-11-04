"""
LoadBalancer class for routing requests across multiple hosts with health checking.
"""

import requests
import time
from typing import List, Optional, Set, Dict
from itertools import cycle


class LoadBalancer:
    """
    A load balancer that routes HTTP requests across multiple hosts.
    
    Features:
    - Round-robin load balancing
    - Automatic host health checking based on error codes
    - Automatic failover to healthy hosts
    
    Args:
        hosts: List of host URLs to load balance across
        error_codes: Set of HTTP status codes that indicate an unhealthy host
                     (default: {500, 502, 503, 504})
        unhealthy_timeout: Time in seconds after which an unhealthy host should be
                          retried (default: 60 seconds). Set to None to disable.
    
    Example:
        >>> lb = LoadBalancer(['http://host1.com', 'http://host2.com'])
        >>> response = lb.get('/api/endpoint')
    """
    
    def __init__(self, hosts: List[str], error_codes: Optional[Set[int]] = None, 
                 unhealthy_timeout: Optional[float] = 60):
        """
        Initialize the LoadBalancer with hosts and error codes.
        
        Args:
            hosts: List of host URLs to balance requests across
            error_codes: Set of HTTP status codes indicating unhealthy hosts
            unhealthy_timeout: Time in seconds before retrying an unhealthy host
        """
        if not hosts:
            raise ValueError("At least one host must be provided")
        
        self.hosts = [host.rstrip('/') for host in hosts]
        self.error_codes = error_codes or {500, 502, 503, 504}
        self.unhealthy_timeout = unhealthy_timeout
        self.unhealthy_hosts: Dict[str, float] = {}
        self._host_cycle = cycle(self.hosts)
        self._current_host = None
    
    def _cleanup_expired_unhealthy_hosts(self):
        """Remove hosts from unhealthy list if their timeout has expired."""
        if self.unhealthy_timeout is None:
            return
        
        current_time = time.time()
        expired_hosts = [
            host for host, timestamp in self.unhealthy_hosts.items()
            if current_time - timestamp >= self.unhealthy_timeout
        ]
        for host in expired_hosts:
            del self.unhealthy_hosts[host]
    
    def _get_next_host(self) -> Optional[str]:
        """
        Get the next healthy host using round-robin strategy.
        
        Returns:
            Next healthy host URL or None if all hosts are unhealthy
        """
        # Clean up expired unhealthy hosts before selecting next host
        self._cleanup_expired_unhealthy_hosts()
        
        healthy_hosts = [h for h in self.hosts if h not in self.unhealthy_hosts]
        
        if not healthy_hosts:
            return None
        
        # If we need to switch to healthy hosts only, recreate the cycle
        if self._current_host in self.unhealthy_hosts or self._current_host is None:
            self._host_cycle = cycle(healthy_hosts)
        
        # Find next host that is healthy
        attempts = 0
        while attempts < len(self.hosts):
            host = next(self._host_cycle)
            if host not in self.unhealthy_hosts:
                self._current_host = host
                return host
            attempts += 1
        
        return None
    
    def _mark_unhealthy(self, host: str):
        """Mark a host as unhealthy with a timestamp."""
        self.unhealthy_hosts[host] = time.time()
    
    def _is_error_response(self, status_code: int) -> bool:
        """Check if status code indicates an unhealthy host."""
        return status_code in self.error_codes
    
    def _make_request(self, method: str, path: str, **kwargs):
        """
        Make an HTTP request with automatic failover.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path to request
            **kwargs: Additional arguments to pass to requests
        
        Returns:
            Response object from requests library
        
        Raises:
            RuntimeError: If all hosts are unhealthy
        """
        attempts = 0
        max_attempts = len(self.hosts)
        
        while attempts < max_attempts:
            host = self._get_next_host()
            
            if host is None:
                raise RuntimeError("All hosts are unhealthy")
            
            url = f"{host}{path}"
            
            try:
                response = requests.request(method, url, **kwargs)
                
                # Check if response indicates unhealthy host
                if self._is_error_response(response.status_code):
                    self._mark_unhealthy(host)
                    attempts += 1
                    continue
                
                return response
                
            except requests.exceptions.RequestException:
                # Mark host as unhealthy on connection errors
                self._mark_unhealthy(host)
                attempts += 1
                continue
        
        raise RuntimeError("All hosts are unhealthy")
    
    def get(self, path: str, **kwargs):
        """
        Make a GET request.
        
        Args:
            path: URL path to request
            **kwargs: Additional arguments to pass to requests.get
        
        Returns:
            Response object
        """
        return self._make_request('GET', path, **kwargs)
    
    def post(self, path: str, **kwargs):
        """
        Make a POST request.
        
        Args:
            path: URL path to request
            **kwargs: Additional arguments to pass to requests.post
        
        Returns:
            Response object
        """
        return self._make_request('POST', path, **kwargs)
    
    def put(self, path: str, **kwargs):
        """
        Make a PUT request.
        
        Args:
            path: URL path to request
            **kwargs: Additional arguments to pass to requests.put
        
        Returns:
            Response object
        """
        return self._make_request('PUT', path, **kwargs)
    
    def delete(self, path: str, **kwargs):
        """
        Make a DELETE request.
        
        Args:
            path: URL path to request
            **kwargs: Additional arguments to pass to requests.delete
        
        Returns:
            Response object
        """
        return self._make_request('DELETE', path, **kwargs)
    
    def patch(self, path: str, **kwargs):
        """
        Make a PATCH request.
        
        Args:
            path: URL path to request
            **kwargs: Additional arguments to pass to requests.patch
        
        Returns:
            Response object
        """
        return self._make_request('PATCH', path, **kwargs)
    
    def reset_health(self):
        """Reset all hosts to healthy status."""
        self.unhealthy_hosts.clear()
    
    def get_healthy_hosts(self) -> List[str]:
        """Get list of currently healthy hosts."""
        return [h for h in self.hosts if h not in self.unhealthy_hosts]
    
    def get_unhealthy_hosts(self) -> List[str]:
        """Get list of currently unhealthy hosts."""
        return list(self.unhealthy_hosts)
