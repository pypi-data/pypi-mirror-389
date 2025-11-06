"""
Storage Client - Simple API for apps to access Drive storage

This client provides a simple interface for apps to read/write their own data
using the Drive storage API. Each app can only access its own data directory.
"""
import json
import httpx
from typing import Optional, Dict, Any, List
from pathlib import Path
import os


class StorageClient:
    """
    Client for accessing Drive storage API.
    
    Drive is local-only storage, but accessible via forwarded requests:
    - Local: Direct access to localhost:8000/drive/api
    - Production: Requests to api.oneaurica.com are forwarded to local execution node
    """
    
    def __init__(self, app_name: str, base_url: Optional[str] = None):
        """
        Initialize storage client for an app.
        
        Args:
            app_name: Name of the app (e.g., 'chat-app', 'digital-twin')
            base_url: Base URL for Drive API (defaults to localhost)
        """
        self.app_name = app_name
        # Drive is local, but accessible via request forwarding in production
        self.base_url = base_url or "http://localhost:8000/drive/api"
        # Data is stored in centralized data/{app-name}/ directory
        self.base_path = app_name
        
    def _get_full_path(self, path: str) -> str:
        """Get full path with app prefix"""
        # Remove leading slash if present
        path = path.lstrip('/')
        # All app data is stored in data/{app-name}/
        return f"{self.base_path}/{path}"
    
    def read(self, path: str) -> Optional[str]:
        """
        Read file contents.
        
        Args:
            path: File path relative to app's data directory
            
        Returns:
            File contents or None if not found
        """
        try:
            full_path = self._get_full_path(path)
            response = httpx.get(
                f"{self.base_url}/read",
                params={"path": full_path},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()["content"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        except Exception as e:
            print(f"⚠️ Error reading {path}: {e}")
            return None
    
    def write(self, path: str, content: str, create_dirs: bool = True) -> bool:
        """
        Write content to a file.
        
        Args:
            path: File path relative to app's data directory
            content: Content to write
            create_dirs: Create parent directories if needed
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self._get_full_path(path)
            response = httpx.post(
                f"{self.base_url}/write",
                json={
                    "path": full_path,
                    "content": content,
                    "create_dirs": create_dirs
                },
                timeout=10.0
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"⚠️ Error writing {path}: {e}")
            return False
    
    def read_json(self, path: str) -> Optional[Dict]:
        """
        Read and parse JSON file.
        
        Args:
            path: File path relative to app's data directory
            
        Returns:
            Parsed JSON data or None if not found
        """
        content = self.read(path)
        if content is None:
            return None
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"⚠️ Error parsing JSON from {path}: {e}")
            return None
    
    def write_json(self, path: str, data: Dict, indent: int = 2) -> bool:
        """
        Write data as JSON file.
        
        Args:
            path: File path relative to app's data directory
            data: Data to serialize as JSON
            indent: JSON indentation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            return self.write(path, content)
        except Exception as e:
            print(f"⚠️ Error writing JSON to {path}: {e}")
            return False
    
    def delete(self, path: str) -> bool:
        """
        Delete a file.
        
        Args:
            path: File path relative to app's data directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self._get_full_path(path)
            response = httpx.delete(
                f"{self.base_url}/delete",
                params={"path": full_path},
                timeout=10.0
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"⚠️ Error deleting {path}: {e}")
            return False
    
    def list(self, path: str = "", include_hidden: bool = False) -> Optional[List[Dict]]:
        """
        List files and directories.
        
        Args:
            path: Directory path relative to app's data directory
            include_hidden: Include hidden files
            
        Returns:
            List of file/directory info or None on error
        """
        try:
            full_path = self._get_full_path(path) if path else self.base_path
            response = httpx.get(
                f"{self.base_url}/list",
                params={
                    "path": full_path,
                    "include_hidden": include_hidden
                },
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()["items"]
        except Exception as e:
            print(f"⚠️ Error listing {path}: {e}")
            return None
    
    def create_dir(self, path: str) -> bool:
        """
        Create a directory.
        
        Args:
            path: Directory path relative to app's data directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self._get_full_path(path)
            response = httpx.post(
                f"{self.base_url}/create-dir",
                json={"path": full_path},
                timeout=10.0
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"⚠️ Error creating directory {path}: {e}")
            return False
    
    def exists(self, path: str) -> bool:
        """
        Check if a file or directory exists.
        
        Args:
            path: Path relative to app's data directory
            
        Returns:
            True if exists, False otherwise
        """
        content = self.read(path)
        return content is not None


# Convenience function for quick access
def get_storage_client(app_name: str) -> StorageClient:
    """Get a storage client for an app"""
    return StorageClient(app_name)
