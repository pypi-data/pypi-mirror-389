"""
Photo and media management API endpoints.
"""

from typing import List, Dict, Any, Optional
from ..models.media import Photo, Album


class MediaAPI:
    """
    Photo and media management endpoints.
    """
    
    def __init__(self, http_client):
        """
        Initialize Media API.
        
        Args:
            http_client: HTTP client instance
        """
        self.http = http_client
    
    def upload_photo(
        self,
        file_path: str,
        caption: Optional[str] = None,
        album_id: Optional[str] = None,
    ) -> Photo:
        """
        Upload a photo.
        
        Args:
            file_path: Path to the photo file
            caption: Photo caption
            album_id: Album ID to add photo to
            
        Returns:
            Photo object
        """
        with open(file_path, 'rb') as f:
            files = {'photo': f}
            data = {}
            
            if caption:
                data['caption'] = caption
            if album_id:
                data['album_id'] = album_id
            
            response = self.http.post("/v1/photo", data=data, files=files)
            return Photo(response)
    
    def get_photo(self, photo_id: str) -> Photo:
        """
        Get photo details.
        
        Args:
            photo_id: Photo ID
            
        Returns:
            Photo object
        """
        data = self.http.get(f"/v1/photo/{photo_id}")
        return Photo(data)
    
    def delete_photo(self, photo_id: str) -> Dict[str, Any]:
        """
        Delete a photo.
        
        Args:
            photo_id: Photo ID to delete
            
        Returns:
            Response data
        """
        return self.http.delete(f"/v1/photo/{photo_id}")
    
    def get_user_photos(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Photo]:
        """
        Get photos for a user.
        
        Args:
            user_id: User ID
            limit: Maximum photos
            offset: Pagination offset
            
        Returns:
            List of Photo objects
        """
        params = {"limit": limit, "offset": offset}
        data = self.http.get(f"/v1/user/{user_id}/photos", params=params)
        
        if isinstance(data, list):
            return [Photo(photo) for photo in data]
        elif isinstance(data, dict) and "photos" in data:
            return [Photo(photo) for photo in data["photos"]]
        return []
    
    def get_album(self, album_id: str) -> Album:
        """
        Get album details.
        
        Args:
            album_id: Album ID
            
        Returns:
            Album object
        """
        data = self.http.get(f"/v1/album/{album_id}")
        return Album(data)
    
    def get_user_albums(self, user_id: str) -> List[Album]:
        """
        Get albums for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of Album objects
        """
        data = self.http.get(f"/v1/user/{user_id}/albums")
        
        if isinstance(data, list):
            return [Album(album) for album in data]
        elif isinstance(data, dict) and "albums" in data:
            return [Album(album) for album in data["albums"]]
        return []
    
    def create_album(self, name: str, description: Optional[str] = None) -> Album:
        """
        Create a new album.
        
        Args:
            name: Album name
            description: Album description
            
        Returns:
            Album object
        """
        data = {"name": name}
        if description:
            data["description"] = description
        
        response = self.http.post("/v1/album", data=data)
        return Album(response)
    
    def update_album(
        self,
        album_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Album:
        """
        Update an album.
        
        Args:
            album_id: Album ID
            name: New album name
            description: New album description
            
        Returns:
            Updated Album object
        """
        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        
        response = self.http.put(f"/v1/album/{album_id}", data=data)
        return Album(response)
    
    def delete_album(self, album_id: str) -> Dict[str, Any]:
        """
        Delete an album.
        
        Args:
            album_id: Album ID to delete
            
        Returns:
            Response data
        """
        return self.http.delete(f"/v1/album/{album_id}")

