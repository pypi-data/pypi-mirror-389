"""
RecallBricks Python SDK
The Memory Layer for AI - Persistent memory across all AI models
"""

import requests
import functools
import time
from typing import List, Dict, Optional, Any
from .exceptions import AuthenticationError, RateLimitError, APIError, RecallBricksError


class RecallBricks:
    """
    RecallBricks client for saving and retrieving AI memories.
    
    Usage:
        >>> from recallbricks import RecallBricks
        >>> memory = RecallBricks(api_key="your_api_key")
        >>> memory.save("Important context about the project")
        >>> memories = memory.get_all()
    """
    
    def __init__(self, api_key: str, base_url: str = "https://recallbricks-api-production.up.railway.app"):
        """
        Initialize RecallBricks client.
        
        Args:
            api_key: Your RecallBricks API key
            base_url: API base URL (default: production)
        """
        if not api_key:
            raise AuthenticationError("API key is required")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to RecallBricks API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get('X-RateLimit-Reset')
                raise RateLimitError(
                    "Rate limit exceeded. Please try again later.",
                    retry_after=retry_after
                )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            
            # Handle other errors
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise APIError(
                    error_data.get('message', 'API request failed'),
                    status_code=response.status_code
                )
            
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            raise RecallBricksError(f"Network error: {str(e)}")
    
    def save(
        self,
        text: str,
        source: str = "api",
        project_id: str = "default",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Save a new memory with automatic retry on failure.

        Args:
            text: The memory content to save
            source: Source of the memory (default: "api")
            project_id: Project identifier (default: "default")
            tags: Optional list of tags
            metadata: Optional metadata dictionary
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Dictionary containing the created memory with id, created_at, etc.

        Example:
            >>> memory.save("User prefers dark mode and TypeScript")
        """
        payload = {
            "text": text,
            "source": source,
            "project_id": project_id,
        }

        if tags:
            payload["tags"] = tags
        if metadata:
            payload["metadata"] = metadata

        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                return self._request("POST", "/api/v1/memories", json=payload)
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"Save failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise RecallBricksError(f"Failed to save after {max_retries} attempts: {e}")
    
    def get_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all memories.
        
        Args:
            limit: Optional limit on number of memories to return
            
        Returns:
            List of memory dictionaries
            
        Example:
            >>> all_memories = memory.get_all(limit=10)
        """
        params = {}
        if limit:
            params['limit'] = limit
            
        response = self._request("GET", "/api/v1/memories", params=params)
        return response.get('memories', [])
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories by text.
        
        Args:
            query: Search query
            limit: Maximum number of results (default: 10)
            
        Returns:
            List of matching memory dictionaries
            
        Example:
            >>> results = memory.search("dark mode", limit=5)
        """
        # Simple client-side search for now
        # TODO: Add server-side search endpoint
        all_memories = self.get_all()
        query_lower = query.lower()
        
        matches = [
            m for m in all_memories 
            if query_lower in m.get('text', '').lower()
        ]
        
        return matches[:limit]
    
    def get(self, memory_id: str) -> Dict[str, Any]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: The memory ID
            
        Returns:
            Memory dictionary
            
        Example:
            >>> specific = memory.get("123e4567-e89b-12d3-a456-426614174000")
        """
        return self._request("GET", f"/api/v1/memories/{memory_id}")
    
    def delete(self, memory_id: str) -> Dict[str, Any]:
        """
        Delete a memory.
        
        Args:
            memory_id: The memory ID to delete
            
        Returns:
            Success confirmation
            
        Example:
            >>> memory.delete("123e4567-e89b-12d3-a456-426614174000")
        """
        return self._request("DELETE", f"/api/v1/memories/{memory_id}")
    
    def get_rate_limit(self) -> Dict[str, Any]:
        """
        Get current rate limit status.

        Returns:
            Dictionary with limit, remaining, reset, percentUsed

        Example:
            >>> status = memory.get_rate_limit()
            >>> print(f"Remaining: {status['remaining']}/{status['limit']}")
        """
        return self._request("GET", "/api/v1/rate-limit")

    def capture_function(self, save_inputs: bool = True, save_outputs: bool = True, include_errors: bool = True):
        """
        Decorator that automatically captures function inputs and outputs.

        Args:
            save_inputs: Whether to save function inputs (default: True)
            save_outputs: Whether to save function outputs (default: True)
            include_errors: Whether to save errors (default: True)

        Usage:
            >>> @rb.capture_function()
            >>> def process_email(email):
            >>>     return email.reply()
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Save inputs
                if save_inputs:
                    input_data = f"[AUTO-CAPTURE] Function: {func.__name__}, Args: {args}, Kwargs: {kwargs}"
                    try:
                        self.save(input_data, source="api")
                    except Exception as e:
                        if include_errors:
                            print(f"Failed to save inputs: {e}")

                # Execute function
                try:
                    result = func(*args, **kwargs)

                    # Save outputs
                    if save_outputs:
                        output_data = f"[AUTO-CAPTURE] Function: {func.__name__}, Result: {result}"
                        try:
                            self.save(output_data, source="api")
                        except Exception as e:
                            if include_errors:
                                print(f"Failed to save outputs: {e}")

                    return result

                except Exception as e:
                    # Save errors
                    if include_errors:
                        error_data = f"[AUTO-CAPTURE-ERROR] Function: {func.__name__}, Error: {str(e)}"
                        try:
                            self.save(error_data, source="api")
                        except:
                            pass
                    raise

            return wrapper
        return decorator
