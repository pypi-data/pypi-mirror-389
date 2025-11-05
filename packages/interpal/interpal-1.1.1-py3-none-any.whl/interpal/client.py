"""
Main client classes for the Interpals library.
Provides both synchronous and asynchronous interfaces.
"""

from typing import Optional, Callable, Dict, Any
from .auth import AuthManager
from .http import HTTPClient, AsyncHTTPClient
from .websocket import WebSocketClient, SyncWebSocketClient
from .session_manager import SessionManager
from .api.user import UserAPI
from .api.messages import MessagesAPI
from .api.search import SearchAPI
from .api.media import MediaAPI
from .api.social import SocialAPI
from .api.realtime import RealtimeAPI


class InterpalClient:
    """
    Synchronous Interpals client.
    
    Example:
        >>> client = InterpalClient(username="user", password="pass")
        >>> client.login()
        >>> profile = client.get_self()
        >>> print(f"Logged in as {profile.name}")
    """
    
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        session_cookie: Optional[str] = None,
        auth_token: Optional[str] = None,
        auto_login: bool = False,
        user_agent: str = "interpal-python-lib/1.0.0",
        persist_session: bool = False,
        session_file: Optional[str] = None,
        session_expiration_hours: int = 24
    ):
        """
        Initialize Interpals client.
        
        Args:
            username: Interpals username for login
            password: Account password
            session_cookie: Existing session cookie
            auth_token: Existing auth token
            auto_login: Automatically login on initialization
            user_agent: User agent string
            persist_session: Enable persistent session storage
            session_file: Path to session file (default: .interpals_session.json)
            session_expiration_hours: Hours until session expires (default: 24)
        """
        # Store credentials
        self._username = username
        self._password = password
        
        # Initialize session manager
        self._persist_session = persist_session
        self._session_manager = None
        if persist_session:
            self._session_manager = SessionManager(
                session_file=session_file,
                expiration_hours=session_expiration_hours
            )
        
        # Initialize auth manager
        self.auth = AuthManager(user_agent=user_agent)
        
        # Try to load saved session first if persist_session is enabled
        loaded_from_file = False
        if self._session_manager:
            saved_session = self._session_manager.load_session()
            if saved_session:
                print(f"Loading saved session for {saved_session.get('username', 'user')}...")
                self.auth.import_session(
                    saved_session['session_cookie'],
                    saved_session.get('auth_token')
                )
                loaded_from_file = True
                
                # Validate the loaded session
                try:
                    if not self.auth.validate_session():
                        print("Saved session is invalid. Will login with credentials.")
                        loaded_from_file = False
                        self._session_manager.clear_session()
                    else:
                        print("Saved session is valid!")
                except Exception as e:
                    print(f"Session validation failed: {e}")
                    loaded_from_file = False
                    self._session_manager.clear_session()
        
        # Import session if provided explicitly
        if not loaded_from_file and session_cookie:
            self.auth.import_session(session_cookie, auth_token)
        
        # Initialize HTTP client
        self.http = HTTPClient(self.auth)
        
        # Initialize WebSocket client
        self._ws_client: Optional[SyncWebSocketClient] = None
        
        # Initialize API modules
        self.user = UserAPI(self.http)
        self.messages = MessagesAPI(self.http)
        self.search = SearchAPI(self.http)
        self.media = MediaAPI(self.http)
        self.social = SocialAPI(self.http)
        self.realtime = RealtimeAPI(self.http)
        
        # Auto login if requested and no valid session was loaded
        if not loaded_from_file and auto_login and username and password:
            self.login()
    
    def login(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Login to Interpals and save session if persist_session is enabled.
        
        Args:
            username: Username (uses constructor value if not provided)
            password: Password (uses constructor value if not provided)
        """
        user = username or self._username
        pwd = password or self._password
        
        if not user or not pwd:
            raise ValueError("Username and password required for login")
        
        # Perform login
        session_data = self.auth.login(user, pwd)
        
        # Save session if persistence is enabled
        if self._session_manager:
            self._session_manager.save_session(
                session_cookie=session_data['session_cookie'],
                auth_token=session_data.get('auth_token'),
                username=user
            )
            print(f"Session saved and will expire in {self._session_manager.expiration_hours} hours")
    
    def import_session(self, cookie_string: str, auth_token: Optional[str] = None):
        """
        Import an existing session.
        
        Args:
            cookie_string: Session cookie value
            auth_token: Optional auth token
        """
        self.auth.import_session(cookie_string, auth_token)
    
    def export_session(self) -> Dict[str, Optional[str]]:
        """
        Export current session for storage.
        
        Returns:
            Dictionary with session_cookie and auth_token
        """
        return self.auth.export_session()
    
    def validate_session(self) -> bool:
        """
        Validate current session.
        
        Returns:
            True if session is valid
        """
        return self.auth.validate_session()
    
    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self.auth.is_authenticated
    
    # Convenience methods for common operations
    
    def get_self(self):
        """Get current user profile."""
        return self.user.get_self()
    
    def get_user(self, user_id: str):
        """Get user profile by ID."""
        return self.user.get_user(user_id)
    
    def get_threads(self):
        """Get message threads."""
        return self.messages.get_threads()
    
    def get_user_thread(self, user_id: str):
        """Get or create thread with a user."""
        return self.messages.get_user_thread(user_id)
    
    def send_message(self, thread_id: str, content: str):
        """Send a message."""
        return self.messages.send_message(thread_id, content)
    
    def search_users(self, **kwargs):
        """Search for users."""
        return self.search.search_users(**kwargs)
    
    def get_feed(self, feed_type: str = "global", limit: int = 20, **kwargs):
        """
        Get main feed.
        
        Args:
            feed_type: Type of feed - "global" or "following" (default: "global")
            limit: Maximum items (default: 20)
            **kwargs: Additional parameters (offset, extra)
        """
        return self.search.get_feed(feed_type=feed_type, limit=limit, **kwargs)
    
    def upload_photo(self, file_path: str, caption: Optional[str] = None):
        """Upload a photo."""
        return self.media.upload_photo(file_path, caption)
    
    def get_notifications(self):
        """Get notifications."""
        return self.realtime.get_notifications()
    
    # WebSocket event system
    
    def event(self, event_name: str):
        """
        Decorator for registering WebSocket event handlers.
        
        Args:
            event_name: Name of the event (e.g., 'on_message', 'on_typing')
            
        Example:
            @client.event('on_message')
            def handle_message(data):
                print(f"New message: {data}")
        """
        if self._ws_client is None:
            self._ws_client = SyncWebSocketClient(self.auth)
        return self._ws_client.on(event_name)
    
    def start_websocket(self):
        """Start WebSocket connection for real-time events."""
        if self._ws_client is None:
            self._ws_client = SyncWebSocketClient(self.auth)
        self._ws_client.connect()
    
    def stop_websocket(self):
        """Stop WebSocket connection."""
        if self._ws_client:
            self._ws_client.disconnect()
    
    def close(self):
        """Close all connections."""
        self.http.close()
        if self._ws_client:
            self._ws_client.disconnect()
        self.auth.clear_session()
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about stored session.
        
        Returns:
            Dictionary with session info or None if no session manager
        """
        if self._session_manager:
            return self._session_manager.get_session_info()
        return None
    
    def clear_saved_session(self):
        """Clear saved session file."""
        if self._session_manager:
            self._session_manager.clear_session()
            print("Saved session cleared")


class AsyncInterpalClient:
    """
    Asynchronous Interpals client.
    
    Example:
        >>> client = AsyncInterpalClient(username="user", password="pass")
        >>> await client.login()
        >>> profile = await client.get_self()
        >>> print(f"Logged in as {profile.name}")
    """
    
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        session_cookie: Optional[str] = None,
        auth_token: Optional[str] = None,
        user_agent: str = "interpal-python-lib/1.0.0",
        persist_session: bool = False,
        session_file: Optional[str] = None,
        session_expiration_hours: int = 24
    ):
        """
        Initialize async Interpals client.
        
        Args:
            username: Interpals username for login
            password: Account password
            session_cookie: Existing session cookie
            auth_token: Existing auth token
            user_agent: User agent string
            persist_session: Enable persistent session storage
            session_file: Path to session file (default: .interpals_session.json)
            session_expiration_hours: Hours until session expires (default: 24)
        """
        # Store credentials
        self._username = username
        self._password = password
        
        # Initialize session manager
        self._persist_session = persist_session
        self._session_manager = None
        if persist_session:
            self._session_manager = SessionManager(
                session_file=session_file,
                expiration_hours=session_expiration_hours
            )
        
        # Initialize auth manager
        self.auth = AuthManager(user_agent=user_agent)
        
        # Try to load saved session first if persist_session is enabled
        loaded_from_file = False
        if self._session_manager:
            saved_session = self._session_manager.load_session()
            if saved_session:
                print(f"Loading saved session for {saved_session.get('username', 'user')}...")
                self.auth.import_session(
                    saved_session['session_cookie'],
                    saved_session.get('auth_token')
                )
                loaded_from_file = True
                
                # Validate the loaded session
                try:
                    if not self.auth.validate_session():
                        print("Saved session is invalid. Will login with credentials.")
                        loaded_from_file = False
                        self._session_manager.clear_session()
                    else:
                        print("Saved session is valid!")
                except Exception as e:
                    print(f"Session validation failed: {e}")
                    loaded_from_file = False
                    self._session_manager.clear_session()
        
        # Import session if provided explicitly
        if not loaded_from_file and session_cookie:
            self.auth.import_session(session_cookie, auth_token)
        
        # Initialize async HTTP client
        self.http = AsyncHTTPClient(self.auth)
        
        # Initialize WebSocket client
        self._ws_client: Optional[WebSocketClient] = None
        
        # Initialize API modules (they'll use async methods)
        self.user = UserAPI(self.http)
        self.messages = MessagesAPI(self.http)
        self.search = SearchAPI(self.http)
        self.media = MediaAPI(self.http)
        self.social = SocialAPI(self.http)
        self.realtime = RealtimeAPI(self.http)
    
    def login(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Login to Interpals and save session if persist_session is enabled (sync operation).
        
        Args:
            username: Username (uses constructor value if not provided)
            password: Password (uses constructor value if not provided)
        """
        user = username or self._username
        pwd = password or self._password
        
        if not user or not pwd:
            raise ValueError("Username and password required for login")
        
        # Login is synchronous even in async client
        session_data = self.auth.login(user, pwd)
        
        # Save session if persistence is enabled
        if self._session_manager:
            self._session_manager.save_session(
                session_cookie=session_data['session_cookie'],
                auth_token=session_data.get('auth_token'),
                username=user
            )
            print(f"Session saved and will expire in {self._session_manager.expiration_hours} hours")
    
    def import_session(self, cookie_string: str, auth_token: Optional[str] = None):
        """
        Import an existing session.
        
        Args:
            cookie_string: Session cookie value
            auth_token: Optional auth token
        """
        self.auth.import_session(cookie_string, auth_token)
    
    def export_session(self) -> Dict[str, Optional[str]]:
        """
        Export current session for storage.
        
        Returns:
            Dictionary with session_cookie and auth_token
        """
        return self.auth.export_session()
    
    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self.auth.is_authenticated
    
    # Async convenience methods for common operations
    
    async def get_self(self):
        """Get current user profile."""
        data = await self.http.get("/v1/account/self")
        from .models.user import Profile
        return Profile(data)
    
    async def get_user(self, user_id: str):
        """Get user profile by ID."""
        data = await self.http.get(f"/v1/profile/{user_id}")
        from .models.user import Profile
        return Profile(data)
    
    async def get_threads(self):
        """Get message threads."""
        data = await self.http.get("/v1/thread")
        from .models.message import Thread
        if isinstance(data, list):
            return [Thread(t) for t in data]
        elif isinstance(data, dict) and "threads" in data:
            return [Thread(t) for t in data["threads"]]
        return []
    
    async def send_message(self, thread_id: str, content: str):
        """Send a message."""
        data = {"thread_id": thread_id, "content": content}
        response = await self.http.post("/v1/message", data=data)
        from .models.message import Message
        return Message(response)
    
    async def search_users(self, **kwargs):
        """Search for users."""
        params = {k: v for k, v in kwargs.items() if v is not None}
        data = await self.http.get("/v1/search/user", params=params)
        from .models.user import Profile
        if isinstance(data, list):
            return [Profile(u) for u in data]
        elif isinstance(data, dict) and "results" in data:
            return [Profile(u) for u in data["results"]]
        return []
    
    async def get_feed(
        self,
        feed_type: str = "global",
        limit: int = 20,
        offset: int = 0,
        extra: Optional[str] = "photos.user"
    ):
        """
        Get main feed.
        
        Args:
            feed_type: Type of feed - "global" or "following" (default: "global")
            limit: Maximum items (default: 20)
            offset: Pagination offset
            extra: Extra data to include (default: "photos.user")
        """
        params = {
            "type": feed_type,
            "limit": limit,
            "offset": offset
        }
        
        if extra:
            params["extra"] = extra
        
        data = await self.http.get("/v1/feed", params=params)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "feed" in data:
            return data["feed"]
        return []
    
    async def get_notifications(self):
        """Get notifications."""
        data = await self.http.get("/v1/notification/my")
        from .models.social import Notification
        if isinstance(data, list):
            return [Notification(n) for n in data]
        elif isinstance(data, dict) and "notifications" in data:
            return [Notification(n) for n in data["notifications"]]
        return []
    
    # WebSocket event system
    
    def event(self, event_name: str):
        """
        Decorator for registering WebSocket event handlers.
        
        Args:
            event_name: Name of the event (e.g., 'on_message', 'on_typing')
            
        Example:
            @client.event('on_message')
            async def handle_message(data):
                print(f"New message: {data}")
        """
        if self._ws_client is None:
            self._ws_client = WebSocketClient(self.auth)
        return self._ws_client.on(event_name)
    
    async def start(self):
        """
        Start the client and connect WebSocket for real-time events.
        This method will run indefinitely until stopped.
        """
        if self._ws_client is None:
            self._ws_client = WebSocketClient(self.auth)
        await self._ws_client.start()
    
    async def connect_websocket(self):
        """Connect to WebSocket without blocking."""
        if self._ws_client is None:
            self._ws_client = WebSocketClient(self.auth)
        await self._ws_client.connect()
    
    async def disconnect_websocket(self):
        """Disconnect WebSocket."""
        if self._ws_client:
            await self._ws_client.disconnect()
    
    async def close(self):
        """Close all connections."""
        await self.http.close()
        if self._ws_client:
            await self._ws_client.disconnect()
        self.auth.clear_session()
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about stored session.
        
        Returns:
            Dictionary with session info or None if no session manager
        """
        if self._session_manager:
            return self._session_manager.get_session_info()
        return None
    
    def clear_saved_session(self):
        """Clear saved session file."""
        if self._session_manager:
            self._session_manager.clear_session()
            print("Saved session cleared")

