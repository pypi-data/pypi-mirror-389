"""
Basic synchronous usage example for Interpals Python Library.
"""

from interpal import InterpalClient

def main():
    # Method 1: Auto-login with credentials and persistent session
    print("=== Method 1: Auto-login with Persistent Session ===")
    client = InterpalClient(
        username="",
        password="",
        auto_login=True,
        persist_session=True  # Enable session persistence (reuses session for 24 hours)
    )
    
    # Or Method 2: Manual login
    # client = InterpalClient(username="your_username", password="your_password")
    # client.login()
    
    # Or Method 3: Import existing session
    # client = InterpalClient(session_cookie="interpals_sessid=abc123...")
    # client.validate_session()
    
    # Get current user profile
    print("\n=== Getting Profile ===")
    profile = client.get_self()
    
    global_feed = client.get_feed(feed_type="following", limit=20)
    print("\n=== Global Feed ===")
    for item in global_feed:
        print(item)
    
   
    client.close()
    print("\n=== Done! ===")


if __name__ == "__main__":
    main()

