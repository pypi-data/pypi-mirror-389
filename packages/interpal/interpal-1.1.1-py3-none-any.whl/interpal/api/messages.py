"""
Messaging system API endpoints.
"""

from typing import List, Dict, Any, Optional
from ..models.message import Message, Thread


class MessagesAPI:
    """
    Messaging system endpoints.
    """
    
    def __init__(self, http_client):
        """
        Initialize Messages API.
        
        Args:
            http_client: HTTP client instance
        """
        self.http = http_client
    
    def get_threads(self, limit: int = 50, offset: int = 0) -> List[Thread]:
        """
        Get message threads list.
        
        Args:
            limit: Maximum number of threads to return
            offset: Offset for pagination
            
        Returns:
            List of Thread objects
        """
        params = {"limit": limit, "offset": offset}
        data = self.http.get("/v1/user/self/threads", params=params)
        
        if isinstance(data, list):
            return [Thread(thread) for thread in data]
        elif isinstance(data, dict) and "threads" in data:
            return [Thread(thread) for thread in data["threads"]]
        return []
    
    def get_user_thread(self, user_id: str) -> Thread:
        """
        Get or create a thread with a specific user.
        
        Args:
            user_id: User ID to get thread for
            
        Returns:
            Thread object
        """
        data = self.http.get(f"/v1/user-thread/{user_id}")
        return Thread(data)
    
    def get_thread_messages(
        self,
        thread_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        """
        Get messages in a thread.
        
        Args:
            thread_id: Thread ID
            limit: Maximum number of messages
            offset: Offset for pagination
            
        Returns:
            List of Message objects
        """
        params = {"limit": limit, "offset": offset}
        data = self.http.get(f"/v1/thread/{thread_id}/messages", params=params)
        
        if isinstance(data, list):
            return [Message(msg) for msg in data]
        elif isinstance(data, dict) and "messages" in data:
            return [Message(msg) for msg in data["messages"]]
        return []
    
    def send_message(self, thread_id: str, content: str, **kwargs) -> Message:
        """
        Send a message in a thread.
        
        Args:
            thread_id: Thread ID to send message to
            content: Message content
            **kwargs: Additional parameters
            
        Returns:
            Sent Message object
        """
        data = {
            "thread_id": thread_id,
            "content": content,
            **kwargs
        }
        response = self.http.post("/v1/message", data=data)
        return Message(response)
    
    def start_conversation(self, user_id: str, content: str) -> Dict[str, Any]:
        """
        Start a new conversation with a user.
        
        Args:
            user_id: User ID to message
            content: Initial message content
            
        Returns:
            Response data with thread and message info
        """
        data = {
            "recipient_id": user_id,
            "content": content,
        }
        return self.http.post("/v1/message", data=data)
    
    def mark_thread_viewed(self, thread_id: str) -> Dict[str, Any]:
        """
        Mark a thread as viewed/read.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Response data
        """
        return self.http.put(f"/v1/thread/{thread_id}/viewed")
    
    def set_typing(self, thread_id: str, typing: bool = True) -> Dict[str, Any]:
        """
        Send typing indicator.
        
        Args:
            thread_id: Thread ID
            typing: Whether user is typing
            
        Returns:
            Response data
        """
        data = {"typing": typing}
        return self.http.put(f"/v1/thread/{thread_id}/typing", data=data)
    
    def delete_message(self, message_id: str) -> Dict[str, Any]:
        """
        Delete a message.
        
        Args:
            message_id: Message ID to delete
            
        Returns:
            Response data
        """
        return self.http.delete(f"/v1/message/{message_id}")
    
    def get_unread_count(self) -> int:
        """
        Get count of unread messages from user counters.
        
        Returns:
            Number of unread messages
        """
        # Get unread count from user-counters endpoint
        data = self.http.get("/v1/user-counters")
        if isinstance(data, dict):
            return data.get("unread_messages", data.get("messages", 0))
        return 0

