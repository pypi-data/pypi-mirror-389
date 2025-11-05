"""
Asynchronous usage example for Interpals Python Library.
"""

import asyncio
from interpal import AsyncInterpalClient


async def main():
    # Initialize async client
    print("=== Initializing Async Client ===")
    client = AsyncInterpalClient(
        username="your_username",
        password="your_password"
    )
    
    # Login (sync operation)
    client.login()
    
    # Or import existing session
    # client.import_session("interpals_sessid=abc123...")
    
    # Get profile and threads concurrently
    print("\n=== Fetching Data Concurrently ===")
    profile, threads, notifications = await asyncio.gather(
        client.get_self(),
        client.get_threads(),
        client.get_notifications()
    )
    
    print(f"Logged in as: {profile.name}")
    print(f"You have {len(threads)} message threads")
    print(f"You have {len(notifications)} notifications")
    
    # Search users
    print("\n=== Searching Users ===")
    users = await client.search_users(
        country="France",
        age_min=25,
        age_max=35,
        limit=10
    )
    print(f"Found {len(users)} users from France")
    
    # Get feed
    print("\n=== Getting Feed ===")
    feed = await client.get_feed()
    print(f"Feed has {len(feed)} items")
    
    # Process multiple threads concurrently
    if len(threads) >= 3:
        print("\n=== Processing Multiple Threads ===")
        message_lists = await asyncio.gather(
            client.messages.get_thread_messages(threads[0].id, limit=5),
            client.messages.get_thread_messages(threads[1].id, limit=5),
            client.messages.get_thread_messages(threads[2].id, limit=5),
        )
        
        for i, messages in enumerate(message_lists):
            print(f"Thread {i+1}: {len(messages)} messages")
    
    # Send multiple messages concurrently
    # if threads:
    #     await asyncio.gather(
    #         client.send_message(threads[0].id, "Hello from async Python!"),
    #         client.send_message(threads[1].id, "This is sent concurrently!"),
    #     )
    #     print("Sent messages to multiple threads")
    
    # Close connections
    await client.close()
    print("\n=== Done! ===")


async def concurrent_user_lookup():
    """
    Example of looking up multiple users concurrently.
    """
    client = AsyncInterpalClient(session_cookie="your_session_cookie")
    
    user_ids = ["123456789", "987654321", "111222333"]
    
    # Fetch all users concurrently
    users = await asyncio.gather(
        *[client.get_user(user_id) for user_id in user_ids]
    )
    
    for user in users:
        print(f"User: {user.name}, {user.age}, {user.city}")
    
    await client.close()


async def process_notifications():
    """
    Example of processing notifications.
    """
    client = AsyncInterpalClient(session_cookie="your_session_cookie")
    
    # Get notifications
    notifications = await client.get_notifications()
    
    # Mark all as read concurrently
    if notifications:
        await asyncio.gather(
            *[
                client.realtime.mark_notification_read(notif.id)
                for notif in notifications
                if not notif.read
            ]
        )
        print(f"Marked {len(notifications)} notifications as read")
    
    await client.close()


if __name__ == "__main__":
    # Run main example
    asyncio.run(main())
    
    # Uncomment to run other examples:
    # asyncio.run(concurrent_user_lookup())
    # asyncio.run(process_notifications())

