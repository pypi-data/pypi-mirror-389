"""
Photo and album data models.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from .base import BaseModel
from .user import User
from ..utils import parse_timestamp


class Photo(BaseModel):
    """
    Photo model with metadata.
    """
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self.id: Optional[str] = None
        self.url: Optional[str] = None
        self.thumbnail_url: Optional[str] = None
        self.caption: Optional[str] = None
        self.owner: Optional[User] = None
        self.owner_id: Optional[str] = None
        self.upload_date: Optional[datetime] = None
        self.likes: int = 0
        self.comments: int = 0
        self.width: Optional[int] = None
        self.height: Optional[int] = None
        
        super().__init__(data)
    
    def _from_dict(self, data: Dict[str, Any]):
        """Parse photo data from API response."""
        self.id = str(data.get('id', data.get('photo_id', '')))
        self.url = data.get('url', data.get('image_url'))
        self.thumbnail_url = data.get('thumbnail_url', data.get('thumb_url'))
        self.caption = data.get('caption', data.get('description'))
        
        # Parse owner information
        owner_data = data.get('owner', data.get('user'))
        if owner_data:
            self.owner = User(owner_data)
        self.owner_id = str(data.get('owner_id', data.get('user_id', '')))
        
        self.upload_date = parse_timestamp(data.get('upload_date', data.get('created_at')))
        self.likes = data.get('likes', data.get('like_count', 0))
        self.comments = data.get('comments', data.get('comment_count', 0))
        self.width = data.get('width')
        self.height = data.get('height')


class Album(BaseModel):
    """
    Photo album model.
    """
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self.id: Optional[str] = None
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.photos: List[Photo] = []
        self.owner: Optional[User] = None
        self.owner_id: Optional[str] = None
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
        self.photo_count: int = 0
        
        super().__init__(data)
    
    def _from_dict(self, data: Dict[str, Any]):
        """Parse album data from API response."""
        self.id = str(data.get('id', data.get('album_id', '')))
        self.name = data.get('name', data.get('title'))
        self.description = data.get('description')
        
        # Parse photos
        photos_data = data.get('photos', [])
        self.photos = [Photo(p) for p in photos_data]
        
        # Parse owner information
        owner_data = data.get('owner', data.get('user'))
        if owner_data:
            self.owner = User(owner_data)
        self.owner_id = str(data.get('owner_id', data.get('user_id', '')))
        
        self.created_at = parse_timestamp(data.get('created_at'))
        self.updated_at = parse_timestamp(data.get('updated_at'))
        self.photo_count = data.get('photo_count', len(self.photos))


class MediaUpload(BaseModel):
    """
    Media upload status and progress model.
    """
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self.upload_id: Optional[str] = None
        self.status: str = "pending"  # pending, uploading, completed, failed
        self.progress: float = 0.0
        self.url: Optional[str] = None
        self.error: Optional[str] = None
        
        super().__init__(data)
    
    def _from_dict(self, data: Dict[str, Any]):
        """Parse upload data from API response."""
        self.upload_id = str(data.get('upload_id', data.get('id', '')))
        self.status = data.get('status', 'pending')
        self.progress = data.get('progress', 0.0)
        self.url = data.get('url')
        self.error = data.get('error')

