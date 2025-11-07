"""
State Management Demo - Shows caching and object identity features.
This demonstrates the new state management system in v2.0.0.
"""

import asyncio
import time
from interpal import AsyncInterpalClient


async def demonstrate_object_identity():
    """
    Demonstrates how the same object is returned for identical requests.
    """
    print("=== Object Identity Demo ===")

    client = AsyncInterpalClient(
        session_cookie="your_session_cookie",
        cache_users=True,
        max_messages=1000
    )

    # Get your profile multiple times
    profile1 = await client.get_self()
    profile2 = await client.get_self()
    profile3 = await client.get_self()

    print(f"Profile 1 ID: {id(profile1)}")
    print(f"Profile 2 ID: {id(profile2)}")
    print(f"Profile 3 ID: {id(profile3)}")

    if profile1 is profile2 is profile3:
        print("✅ All profiles are the same object (perfect caching!)")
    else:
        print("❌ Profiles are different objects")

    # Verify same data
    print(f"Profile name: {profile1.name}")

    await client.close()


async def demonstrate_cache_performance():
    """
    Demonstrates performance improvements from caching.
    """
    print("\n=== Cache Performance Demo ===")

    client = AsyncInterpalClient(
        session_cookie="your_session_cookie",
        max_messages=2000,
        cache_users=True,
        cache_threads=True
    )

    # Get threads (first time - from API)
    start_time = time.time()
    threads1 = await client.get_threads()
    first_call_time = time.time() - start_time

    # Get threads again (should be from cache)
    start_time = time.time()
    threads2 = await client.get_threads()
    second_call_time = time.time() - start_time

    print(f"First call time: {first_call_time:.3f} seconds")
    print(f"Second call time: {second_call_time:.3f} seconds")

    if second_call_time < first_call_time:
        speedup = first_call_time / second_call_time
        print(f"✅ {speedup:.1f}x speedup from caching!")
    else:
        print("⚠️  Cache didn't improve performance (might be first run)")

    # Verify object identity
    for i, (t1, t2) in enumerate(zip(threads1[:3], threads2[:3])):
        if t1 is t2:
            print(f"✅ Thread {i+1}: Same object cached")
        else:
            print(f"❌ Thread {i+1}: Different objects")

    await client.close()


async def demonstrate_cache_configuration():
    """
    Demonstrates different cache configurations.
    """
    print("\n=== Cache Configuration Demo ===")

    # Small cache configuration
    small_client = AsyncInterpalClient(
        session_cookie="your_session_cookie",
        max_messages=100,
        cache_users=True,
        cache_threads=False  # Disable thread caching
    )

    # Large cache configuration
    large_client = AsyncInterpalClient(
        session_cookie="your_session_cookie",
        max_messages=5000,
        cache_users=True,
        cache_threads=True,
        weak_references=False  # Keep objects in memory
    )

    print("Small cache configuration:")
    small_stats = small_client.get_cache_stats()
    print(f"  Max messages: {small_client.max_messages}")
    print(f"  Cache users: {small_client.cache_users}")
    print(f"  Cache threads: {small_client.cache_threads}")

    print("\nLarge cache configuration:")
    large_stats = large_client.get_cache_stats()
    print(f"  Max messages: {large_client.max_messages}")
    print(f"  Cache users: {large_client.cache_users}")
    print(f"  Cache threads: {large_client.cache_threads}")

    await small_client.close()
    await large_client.close()


async def demonstrate_cache_statistics():
    """
    Demonstrates cache statistics and monitoring.
    """
    print("\n=== Cache Statistics Demo ===")

    client = AsyncInterpalClient(
        session_cookie="your_session_cookie",
        max_messages=1000,
        cache_users=True,
        cache_threads=True
    )

    # Perform some operations to generate cache activity
    print("Performing operations to generate cache data...")

    # Get profile (cached)
    await client.get_self()

    # Get threads (cached)
    threads = await client.get_threads()

    # Get some thread messages (cached)
    if threads:
        for thread in threads[:3]:
            await client.messages.get_thread_messages(thread.id, limit=5)

    # Search users (might create cached objects)
    users = await client.search_users(limit=10)

    # Display comprehensive statistics
    stats = client.get_cache_stats()

    print("\n📊 Cache Statistics:")
    print(f"  Cache hit rate: {stats['hit_rate']:.2%}")
    print(f"  Cache hits: {stats['cache_hits']}")
    print(f"  Cache misses: {stats['cache_misses']}")
    print(f"  Objects created: {stats['objects_created']}")
    print(f"  Objects updated: {stats['objects_updated']}")
    print(f"  Cache evictions: {stats['evictions']}")

    print("\n📦 Cache Sizes:")
    cache_sizes = stats['cache_sizes']
    print(f"  Users: {cache_sizes['users']}")
    print(f"  Profiles: {cache_sizes['profiles']}")
    print(f"  Messages: {cache_sizes['messages']}")
    print(f"  Threads: {cache_sizes['threads']}")
    print(f"  Photos: {cache_sizes['photos']}")
    print(f"  Albums: {cache_sizes['albums']}")

    await client.close()


async def demonstrate_cache_management():
    """
    Demonstrates cache management operations.
    """
    print("\n=== Cache Management Demo ===")

    client = AsyncInterpalClient(
        session_cookie="your_session_cookie",
        max_messages=1000,
        cache_users=True,
        cache_threads=True
    )

    # Generate some cached data
    await client.get_self()
    threads = await client.get_threads()

    stats_before = client.get_cache_stats()
    print(f"Before cleanup:")
    print(f"  Users cached: {stats_before['cache_sizes']['users']}")
    print(f"  Messages cached: {stats_before['cache_sizes']['messages']}")
    print(f"  Threads cached: {stats_before['cache_sizes']['threads']}")

    # Clear specific caches
    print("\n🧹 Clearing user cache...")
    client.clear_user_cache()

    stats_after_user_clear = client.get_cache_stats()
    print(f"After user cache clear:")
    print(f"  Users cached: {stats_after_user_clear['cache_sizes']['users']}")
    print(f"  Messages cached: {stats_after_user_clear['cache_sizes']['messages']}")
    print(f"  Threads cached: {stats_after_user_clear['cache_sizes']['threads']}")

    # Clear all caches
    print("\n🧹 Clearing all caches...")
    client.clear_caches()

    stats_after_all_clear = client.get_cache_stats()
    print(f"After all caches clear:")
    print(f"  Users cached: {stats_after_all_clear['cache_sizes']['users']}")
    print(f"  Messages cached: {stats_after_all_clear['cache_sizes']['messages']}")
    print(f"  Threads cached: {stats_after_all_clear['cache_sizes']['threads']}")

    await client.close()


async def demonstrate_weak_references():
    """
    Demonstrates weak reference behavior.
    """
    print("\n=== Weak References Demo ===")

    # Client with weak references (default)
    weak_client = AsyncInterpalClient(
        session_cookie="your_session_cookie",
        max_messages=1000,
        cache_users=True,
        weak_references=True
    )

    # Client without weak references
    strong_client = AsyncInterpalClient(
        session_cookie="your_session_cookie",
        max_messages=1000,
        cache_users=True,
        weak_references=False
    )

    print("Weak reference client:")
    print(f"  weak_references: {weak_client.weak_references}")
    print(f"  Cache type: Memory-efficient (automatic cleanup)")

    print("\nStrong reference client:")
    print(f"  weak_references: {strong_client.weak_references}")
    print(f"  Cache type: Persistent (objects kept in memory)")

    await weak_client.close()
    await strong_client.close()


async def main():
    """
    Run all state management demonstrations.
    """
    print("🚀 Interpal State Management Demo")
    print("=" * 50)
    print("This demo showcases the new state management features in v2.0.0")
    print("Note: Replace 'your_session_cookie' with a real session cookie")
    print()

    try:
        await demonstrate_object_identity()
        await demonstrate_cache_performance()
        await demonstrate_cache_configuration()
        await demonstrate_cache_statistics()
        await demonstrate_cache_management()
        await demonstrate_weak_references()

        print("\n" + "=" * 50)
        print("✅ All demos completed successfully!")
        print("\nKey takeaways:")
        print("• Same objects are reused throughout the session")
        print("• Caching provides significant performance improvements")
        print("• Cache configuration can be tuned for your use case")
        print("• Monitor cache statistics to optimize performance")
        print("• Manage caches manually when needed")
        print("• Weak references prevent memory leaks")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Make sure you have a valid session cookie")
        print("This demo requires authentication to work properly")


if __name__ == "__main__":
    asyncio.run(main())