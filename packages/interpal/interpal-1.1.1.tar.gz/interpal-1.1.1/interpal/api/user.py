"""
User management API endpoints.
"""

from typing import Dict, Any, Optional
from ..models.user import User, Profile, UserSettings, UserCounters


class UserAPI:
    """
    User management endpoints.
    """
    
    def __init__(self, http_client):
        """
        Initialize User API.
        
        Args:
            http_client: HTTP client instance (HTTPClient or AsyncHTTPClient)
        """
        self.http = http_client
    
    def get_self(self) -> Profile:
        """
        Get current user's profile.
        
        Returns:
            Profile object for the authenticated user
        """
        data = self.http.get("/v1/account/self")
        return Profile(data)
    
    def update_self(self, **kwargs) -> Profile:
        """
        Update current user's profile.
        
        Args:
            **kwargs: Profile fields to update (name, bio, age, etc.)
            
        Returns:
            Updated Profile object
        """
        data = self.http.put("/v1/account/self", data=kwargs)
        return Profile(data)
    
    def get_user(self, user_id: str) -> Profile:
        """
        Get a user's profile by ID.
        
        Args:
            user_id: User ID to fetch
            
        Returns:
            Profile object for the user
        """
        data = self.http.get(f"/v1/profile/{user_id}")
        return Profile(data)
    
    def get_account(self, user_id: str) -> Profile:
        """
        Get account information by ID.
        
        Args:
            user_id: User ID to fetch
            
        Returns:
            Profile object
        """
        data = self.http.get(f"/v1/account/{user_id}")
        return Profile(data)
    
    def get_counters(self) -> UserCounters:
        """
        Get user statistics and counters.
        
        Returns:
            UserCounters object with statistics
        """
        data = self.http.get("/v1/user-counters")
        return UserCounters(data)
    
    def get_settings(self) -> UserSettings:
        """
        Get user settings.
        
        Returns:
            UserSettings object
        """
        data = self.http.get("/v1/settings/self")
        return UserSettings(data)
    
    def update_settings(self, **kwargs) -> UserSettings:
        """
        Update user settings.
        
        Args:
            **kwargs: Settings to update
            
        Returns:
            Updated UserSettings object
        """
        data = self.http.put("/v1/settings/self", data=kwargs)
        return UserSettings(data)
    
    def get_activity(self) -> Dict[str, Any]:
        """
        Get user activity information.
        
        Returns:
            Activity data dictionary
        """
        return self.http.get("/v1/activity/self")

