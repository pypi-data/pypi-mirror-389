import requests
import time
from typing import Optional, List, Dict
import datetime

class PermissionError(Exception):
    """Raised when the API key doesn't have sufficient permissions"""
    pass


class ProgressBar:
    def __init__(self, api_url: str, api_key: str, auto_detect: bool = True):
        """
        Initializes the ProgressBar SDK.
        
        :param api_url: The base URL of the progress bar server (e.g., "http://localhost:8080").
        :param api_key: Your API key (read/write/admin).
        :param auto_detect: Whether to automatically detect key permissions (default: True).
        """
        if not api_url.endswith('/'):
            api_url += '/'
        self.api_url = api_url
        self.progress_url = f"{api_url}progress"
        self.key_info_url = f"{api_url}api/key-info"
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-API-KEY": api_key
        }
        
        self.key_type: Optional[str] = None
        self.permissions: List[str] = []
        
        if auto_detect:
            self._fetch_key_info()
    
    def _fetch_key_info(self):
        """Fetches and caches the API key information"""
        try:
            response = requests.get(self.key_info_url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            self.key_type = data.get('type', 'unknown')
            self.permissions = data.get('permissions', [])
            print(f"✓ API Key Type: {self.key_type.upper() if self.key_type else 'UNKNOWN'}")
            print(f"✓ Permissions: {', '.join(self.permissions)}")
        except requests.exceptions.RequestException as e:
            print(f"Warning: Could not fetch key info: {e}")
            self.key_type = "unknown"
            self.permissions = []
    
    def _check_permission(self, required_permission: str) -> bool:
        """Check if the current key has a specific permission"""
        return required_permission in self.permissions
    
    def _require_permission(self, required_permission: str, action: str):
        """Raise an error if the key doesn't have the required permission"""
        if not self._check_permission(required_permission):
            raise PermissionError(
                f"Your API key (type: {self.key_type}) does not have permission to {action}. "
                f"Required permission: {required_permission}. "
                f"Available permissions: {', '.join(self.permissions)}"
            )

    def get_all(self) -> List[Dict]:
        """
        Retrieves all progress items from the server.
        
        :return: List of progress items.
        :raises PermissionError: If the key doesn't have read permission.
        """
        self._require_permission("read", "read progress items")
        
        try:
            response = requests.get(self.progress_url, headers=self.headers)
            response.raise_for_status()
            items = response.json()
            if not isinstance(items, list):
                items = []
            print(f"✓ Retrieved {len(items)} progress items")
            return items
        except requests.exceptions.RequestException as e:
            print(f"Error fetching progress: {e}")
            return []

    def create(self, item_id: str, title: str, description: str, value: float, weight: int = 0):
        """
        Creates a new progress item on the server.
        
        For write keys: Creates a new item owned by this key.
        For admin keys: Creates a new item.
        
        :param item_id: A unique identifier for the progress item (e.g., "video-processing-123").
        :param title: The main title of the progress item.
        :param description: A short description of the current status.
        :param value: The progress value, from 0.0 to 1.0.
        :param weight: An integer for sorting. Higher values are shown first. Defaults to 0.
        :raises PermissionError: If the key doesn't have create permission.
        :raises ValueError: If an item with this ID already exists.
        """
        self._require_permission("create", "create progress items")
        
        payload = {
            "id": item_id,
            "title": title,
            "description": description,
            "value": value,
            "weight": weight
        }
        
        try:
            response = requests.post(self.progress_url, json=payload, headers=self.headers)
            response.raise_for_status()
            print(f"✓ [{item_id}] Created with progress {value*100:.2f}%")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                raise ValueError(f"Item with ID '{item_id}' already exists. Use update() to modify it.")
            elif e.response.status_code == 403:
                raise PermissionError(f"Permission denied: {e.response.text}")
            else:
                print(f"Error creating progress for '{item_id}': {e}")
                raise
        except requests.exceptions.RequestException as e:
            print(f"Error creating progress for '{item_id}': {e}")
            raise

    def update(self, item_id: str, title: str, description: str, value: float, weight: int = 0):
        """
        Updates an existing progress item on the server.
        
        For write keys: Can only update items created by this key.
        For admin keys: Can update any item.
        
        NOTE: The item must already exist. Use create() to create new items.
        
        :param item_id: The unique identifier of an existing progress item.
        :param title: The main title of the progress item.
        :param description: A short description of the current status.
        :param value: The progress value, from 0.0 to 1.0.
        :param weight: An integer for sorting. Higher values are shown first. Defaults to 0.
        :raises PermissionError: If the key doesn't have update permission.
        :raises ValueError: If the item doesn't exist.
        """
        # Check if we have permission (either update_own or update_all)
        has_permission = (
            self._check_permission("update_own") or 
            self._check_permission("update_all")
        )
        if not has_permission:
            raise PermissionError(
                f"Your API key (type: {self.key_type}) does not have permission to update progress items. "
                f"Available permissions: {', '.join(self.permissions)}"
            )
        
        payload = {
            "id": item_id,
            "title": title,
            "description": description,
            "value": value,
            "weight": weight
        }
        
        try:
            response = requests.put(self.progress_url, json=payload, headers=self.headers)
            response.raise_for_status()
            print(f"✓ [{item_id}] Updated progress to {value*100:.2f}%")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Item with ID '{item_id}' not found. Use create() to create new items.")
            elif e.response.status_code == 403:
                raise PermissionError(
                    f"Permission denied: {e.response.text}. "
                    f"Write keys can only update items they created."
                )
            else:
                print(f"Error updating progress for '{item_id}': {e}")
                raise
        except requests.exceptions.RequestException as e:
            print(f"Error updating progress for '{item_id}': {e}")
            raise

    def delete(self, item_id: str):
        """
        Deletes a progress item from the server.
        
        For write keys: Can only delete items created by this key.
        For admin keys: Can delete any item.
        
        :param item_id: The unique identifier of the progress item to delete.
        :raises PermissionError: If the key doesn't have delete permission.
        """
        # Check if we have permission (either delete_own or delete_all)
        has_permission = (
            self._check_permission("delete_own") or 
            self._check_permission("delete_all")
        )
        if not has_permission:
            raise PermissionError(
                f"Your API key (type: {self.key_type}) does not have permission to delete progress items. "
                f"Available permissions: {', '.join(self.permissions)}"
            )
        
        params = {"id": item_id}
        try:
            response = requests.delete(self.progress_url, params=params, headers=self.headers)
            response.raise_for_status()
            print(f"✓ Successfully deleted progress for '{item_id}'.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise PermissionError(
                    f"Permission denied: {e.response.text}. "
                    f"Write keys can only delete items they created."
                )
            else:
                print(f"Error deleting progress for '{item_id}': {e}")
        except requests.exceptions.RequestException as e:
            print(f"Error deleting progress for '{item_id}': {e}")
    
    def is_admin(self) -> bool:
        """Check if the current key is an admin key"""
        return self.key_type == "admin"
    
    def is_read_only(self) -> bool:
        """Check if the current key is read-only"""
        return self.key_type == "read"
    
    def can_write(self) -> bool:
        """Check if the current key can write (create/update)"""
        return "create" in self.permissions or "update_own" in self.permissions or "update_all" in self.permissions
    
    def can_delete(self) -> bool:
        """Check if the current key can delete"""
        return "delete_own" in self.permissions or "delete_all" in self.permissions
