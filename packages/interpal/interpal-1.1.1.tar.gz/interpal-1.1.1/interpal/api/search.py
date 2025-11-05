"""
User discovery and search API endpoints.
"""

from typing import List, Dict, Any, Optional
from ..models.user import User, Profile


class SearchAPI:
    """
    User discovery and search endpoints.
    """
    
    def __init__(self, http_client):
        """
        Initialize Search API.
        
        Args:
            http_client: HTTP client instance
        """
        self.http = http_client
    
    def search_users(
        self,
        query: Optional[str] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        gender: Optional[str] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        language: Optional[str] = None,
        looking_for: Optional[str] = None,
        online_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Profile]:
        """
        Search for users with filters.
        
        Args:
            query: Search query string
            age_min: Minimum age
            age_max: Maximum age
            gender: Gender filter
            country: Country filter
            city: City filter
            language: Language filter
            looking_for: Looking for filter
            online_only: Only show online users
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of Profile objects
        """
        params = {
            "q": query,
            "age_min": age_min,
            "age_max": age_max,
            "gender": gender,
            "country": country,
            "city": city,
            "language": language,
            "looking_for": looking_for,
            "online_only": online_only,
            "limit": limit,
            "offset": offset,
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        data = self.http.get("/v1/search/user", params=params)
        
        if isinstance(data, list):
            return [Profile(user) for user in data]
        elif isinstance(data, dict) and "results" in data:
            return [Profile(user) for user in data["results"]]
        return []
    
    def search_by_location(
        self,
        latitude: float,
        longitude: float,
        radius: int = 50,
        limit: int = 50,
    ) -> List[Profile]:
        """
        Search users by geographic location.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius: Search radius in kilometers
            limit: Maximum results
            
        Returns:
            List of Profile objects
        """
        params = {
            "lat": latitude,
            "lon": longitude,
            "radius": radius,
            "limit": limit,
        }
        
        data = self.http.get("/v1/search/geo", params=params)
        
        if isinstance(data, list):
            return [Profile(user) for user in data]
        elif isinstance(data, dict) and "results" in data:
            return [Profile(user) for user in data["results"]]
        return []
    
    def get_feed(
        self,
        feed_type: str = "global",
        limit: int = 20,
        offset: int = 0,
        extra: Optional[str] = "photos.user"
    ) -> List[Dict[str, Any]]:
        """
        Get main content feed.
        
        Args:
            feed_type: Type of feed - "global" or "following" (default: "global")
            limit: Maximum items (default: 20)
            offset: Pagination offset
            extra: Extra data to include (default: "photos.user")
            
        Returns:
            List of feed items
        """
        params = {
            "type": feed_type,
            "limit": limit,
            "offset": offset
        }
        
        if extra:
            params["extra"] = extra
        
        response = self.http.get("/v1/feed", params=params)
        
        # Response format: {'data': [...], 'user': {...}, ...}
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        elif isinstance(response, list):
            return response
        
        # Fallback
        return []
    
    def get_nearby_users(self, limit: int = 50) -> List[Profile]:
        """
        Get nearby users based on current location.
        
        Args:
            limit: Maximum results
            
        Returns:
            List of Profile objects
        """
        params = {"limit": limit}
        data = self.http.get("/v1/nearby", params=params)
        
        if isinstance(data, list):
            return [Profile(user) for user in data]
        elif isinstance(data, dict) and "users" in data:
            return [Profile(user) for user in data["users"]]
        return []
    
    def get_suggestions(self, limit: int = 20) -> List[Profile]:
        """
        Get suggested users based on profile and interests.
        
        Args:
            limit: Maximum results
            
        Returns:
            List of Profile objects
        """
        params = {"limit": limit}
        data = self.http.get("/v1/suggestions", params=params)
        
        if isinstance(data, list):
            return [Profile(user) for user in data]
        elif isinstance(data, dict) and "suggestions" in data:
            return [Profile(user) for user in data["suggestions"]]
        return []

