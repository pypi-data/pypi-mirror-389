"""
Example demonstrating the use of WebSocket event models.

This example shows how to use the structured event models for better
type safety and easier access to event data.
"""

import asyncio
from interpal import InterpalClient
from interpal.models import ThreadNewMessageEvent, ThreadTypingEvent, CounterUpdateEvent


async def main():
    # Initialize client
    client = InterpalClient(username="your_username", password="your_password")
    
    # Login
    await client.login()
    
    # Create WebSocket client
    ws = client.create_websocket()
    
    @ws.on('on_message')
    async def handle_new_message(event: ThreadNewMessageEvent):
        """
        Handle new messages with structured event model.
        
        The event parameter is now a ThreadNewMessageEvent object with:
        - event.sender: Full User object with all sender information
        - event.data: MessageEventData with message details
        - event.counters: EventCounters with all counter values
        - event.click_url: Direct URL to the message thread
        """
        print("\n" + "="*60)
        print("📨 NEW MESSAGE RECEIVED")
        print("="*60)
        
        # Access sender information
        print(f"\n👤 From: {event.sender.name} (@{event.sender.username})")
        print(f"   Age: {event.sender.age}, {event.sender.country_code}")
        print(f"   Online: {'🟢' if event.sender.is_online else '🔴'}")
        
        if event.sender.avatar_url:
            print(f"   Avatar: {event.sender.avatar_url}")
        
        # Access message content
        print(f"\n💬 Message: {event.data.message}")
        print(f"   ID: {event.data.id}")
        print(f"   Thread: {event.data.thread_id}")
        print(f"   Time: {event.data.created}")
        
        # Access counters
        print(f"\n📊 Counters:")
        print(f"   New messages: {event.counters.new_messages}")
        print(f"   Unread threads: {event.counters.unread_threads}")
        print(f"   Total threads: {event.counters.total_threads}")
        print(f"   New notifications: {event.counters.new_notifications}")
        print(f"   New views: {event.counters.new_views}")
        
        # Access direct URL
        print(f"\n🔗 URL: {event.click_url}")
        
        # Use convenience properties
        print(f"\n✨ Convenience properties:")
        print(f"   event.message: {event.message}")
        print(f"   event.message_id: {event.message_id}")
        print(f"   event.thread_id: {event.thread_id}")
        
        print("="*60 + "\n")
        
        # Reply to the message
        try:
            await client.send_message(
                user_id=event.sender.id,
                message=f"Thanks for your message: '{event.message}'"
            )
            print(f"✅ Replied to {event.sender.name}")
        except Exception as e:
            print(f"❌ Failed to reply: {e}")
    
    @ws.on('on_typing')
    async def handle_typing(event: ThreadTypingEvent):
        """
        Handle typing indicators with structured event model.
        """
        if event.is_typing:
            print(f"✍️  {event.user.name if event.user else event.user_id} is typing...")
        else:
            print(f"⏸️  {event.user.name if event.user else event.user_id} stopped typing")
    
    @ws.on('on_notification')
    async def handle_counter_update(event: CounterUpdateEvent):
        """
        Handle counter updates with structured event model.
        """
        print(f"\n🔔 Counter Update:")
        print(f"   Messages: {event.counters.new_messages}")
        print(f"   Notifications: {event.counters.new_notifications}")
        print(f"   Friend Requests: {event.counters.new_friend_requests}")
    
    @ws.on('on_ready')
    async def on_ready():
        print("✅ WebSocket connected and ready!")
    
    @ws.on('on_disconnect')
    async def on_disconnect():
        print("⚠️  WebSocket disconnected!")
    
    # Connect and listen
    print("🔌 Connecting to WebSocket...")
    await ws.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

