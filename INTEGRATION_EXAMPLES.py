"""
JARVIS Upgrade - Complete Integration Examples
Executable code snippets showing how to use all new features
"""

# ============================================================================
# 1. CACHING EXAMPLES
# ============================================================================

def example_caching():
    """Demonstrate caching functionality."""
    from cache_manager import get_cache_manager
    import json
    
    cache = get_cache_manager()
    
    # Example 1: Simple cache operations
    cache.memory_cache.set("user_name", "Alex", ttl=3600)
    name = cache.memory_cache.get("user_name")
    print(f"✅ Cached value: {name}")
    
    # Example 2: Cache embeddings
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    cache.cache_embedding("hello world", embedding)
    retrieved = cache.get_embedding("hello world")
    print(f"✅ Embedding cached: {len(retrieved)} dimensions")
    
    # Example 3: Cache API responses
    params = {"model": "gpt-4", "prompt": "Explain AI"}
    response = "Artificial Intelligence is..."
    cache.cache_api_response("POST", "https://api.example.com", params, response)
    cached_response = cache.get_api_response("POST", "https://api.example.com", params)
    print(f"✅ API response cached: {cached_response[:30]}...")
    
    # Example 4: Check cache statistics
    stats = cache.get_stats()
    print(f"✅ Cache stats: {json.dumps(stats, indent=2)}")
    
    # Example 5: Clear cache if needed
    cache.clear_all()
    print("✅ Cache cleared")


# ============================================================================
# 2. RATE LIMITING EXAMPLES
# ============================================================================

def example_rate_limiting():
    """Demonstrate rate limiting functionality."""
    from rate_limiter import get_rate_limiter
    import time
    
    limiter = get_rate_limiter()
    
    # Example 1: Check if request allowed
    model = "gpt-4"
    if limiter.can_request(model):
        print(f"✅ Can make request to {model}")
    
    # Example 2: Record successful request
    limiter.record_success(model)
    print("✅ Request success recorded")
    
    # Example 3: Get model statistics
    stats = limiter.get_stats(model)
    print(f"✅ Model stats:")
    print(f"   - Circuit state: {stats['circuit_state']}")
    print(f"   - Requests/min: {stats['requests_per_minute']}")
    print(f"   - Available tokens: {stats['tokens_available']}")
    
    # Example 4: Update token budget for model
    limiter.update_budget("gpt-4", capacity=200, refill_rate=20.0)
    print("✅ Token budget updated")
    
    # Example 5: Reset rate limiting for a model
    limiter.reset_model("gpt-4")
    print("✅ Rate limiter reset")


# ============================================================================
# 3. REQUEST QUEUE EXAMPLES
# ============================================================================

def example_request_queue():
    """Demonstrate request queue functionality."""
    from request_queue import get_request_queue, RequestPriority
    import time
    
    queue = get_request_queue()
    
    # Example 1: Enqueue critical request
    def critical_task():
        return "Critical result"
    
    req_id = queue.enqueue(
        executor=critical_task,
        priority=RequestPriority.CRITICAL,
        timeout=10
    )
    print(f"✅ Enqueued critical request: {req_id[:8]}")
    
    # Example 2: Enqueue normal request
    def normal_task():
        time.sleep(0.1)
        return "Normal result"
    
    req_id2 = queue.enqueue(
        executor=normal_task,
        priority=RequestPriority.NORMAL,
        max_retries=3
    )
    print(f"✅ Enqueued normal request: {req_id2[:8]}")
    
    # Example 3: Enqueue background task
    def background_task():
        return "Background result"
    
    req_id3 = queue.enqueue(
        executor=background_task,
        priority=RequestPriority.LOW
    )
    print(f"✅ Enqueued background request: {req_id3[:8]}")
    
    # Example 4: Check queue status
    stats = queue.get_stats()
    print(f"✅ Queue status:")
    print(f"   - Queued: {stats['queue_size']}")
    print(f"   - In progress: {stats['in_progress']}")
    print(f"   - Processed: {stats['stats']['processed']}")
    
    # Example 5: Try to get result (non-blocking)
    result = queue.try_result(req_id)
    if result:
        print(f"✅ Result available: {result}")
    else:
        print("⏳ Result not ready yet")


# ============================================================================
# 4. MEMORY DATABASE EXAMPLES
# ============================================================================

def example_memory_database():
    """Demonstrate memory database functionality."""
    from memory_db import get_memory_db
    import json
    
    db = get_memory_db()
    
    # Example 1: Add conversation
    conv_id = db.add_conversation(
        user_text="What's my favorite food?",
        jarvis_response="Your favorite foods are pizza and sushi",
        model="gpt-4"
    )
    print(f"✅ Conversation added: {conv_id[:8]}")
    
    # Example 2: Store memory entry
    db.add_memory_entry(
        category="preferences",
        key="favorite_foods",
        value="Pizza and sushi"
    )
    print("✅ Memory entry stored")
    
    # Example 3: Retrieve recent conversations
    recent = db.get_conversations(limit=5)
    print(f"✅ Retrieved {len(recent)} recent conversations")
    
    # Example 4: Search conversations
    search_results = db.get_conversations(search_text="pizza")
    print(f"✅ Search found {len(search_results)} matches")
    
    # Example 5: Get memory entries by category
    preferences = db.get_memory_entries(category="preferences")
    for entry in preferences:
        print(f"✅ Preference: {entry['key']} = {entry['value']}")
    
    # Example 6: Cache embedding
    db.cache_embedding("hello world", [0.1, 0.2, 0.3])
    embedding = db.get_embedding("hello world")
    print(f"✅ Embedding cached: {embedding}")
    
    # Example 7: Get database statistics
    stats = db.get_stats()
    print(f"✅ Database stats:")
    print(f"   - Conversations: {stats['conversations']}")
    print(f"   - Memory entries: {stats['memory_entries']}")
    print(f"   - Database size: {stats['db_size_mb']}MB")


# ============================================================================
# 5. METRICS & MONITORING EXAMPLES
# ============================================================================

def example_metrics():
    """Demonstrate metrics and monitoring."""
    from metrics import get_metrics_collector, get_health_monitor
    import json
    
    metrics = get_metrics_collector()
    monitor = get_health_monitor()
    
    # Example 1: Record API call
    metrics.record_api_call(
        model="gpt-4",
        tokens_used=150,
        latency=1.5,
        cached=False
    )
    print("✅ API call recorded")
    
    # Example 2: Record cache hit
    metrics.record_api_call(
        model="gpt-4",
        cached=True
    )
    print("✅ Cache hit recorded")
    
    # Example 3: Record memory operation
    metrics.record_memory_operation("read", duration=0.05)
    print("✅ Memory read recorded")
    
    # Example 4: Record error
    metrics.record_error("api_timeout")
    print("✅ Error recorded")
    
    # Example 5: Get comprehensive statistics
    stats = metrics.get_stats()
    print(f"✅ Metrics stats: {json.dumps(stats, indent=2)[:200]}...")
    
    # Example 6: Check system health
    health = monitor.check_health(stats)
    print(f"✅ System health: {health['status'].upper()}")
    if health['alerts']:
        print(f"⚠️  Alerts: {health['alerts']}")
    
    # Example 7: Print health report
    print("\n✅ Full health report:")
    monitor.print_report(stats)
    
    # Example 8: Save metrics to file
    metrics.save_metrics()
    print("✅ Metrics saved to metrics/performance.json")


# ============================================================================
# 6. MIGRATION EXAMPLES
# ============================================================================

def example_migration():
    """Demonstrate migration functionality."""
    from migration_helper import migrate_if_needed, validate_migration
    
    # Example 1: Auto-migrate if needed
    success = migrate_if_needed(force=False)
    if success:
        print("✅ Migration successful")
    else:
        print("❌ Migration failed")
    
    # Example 2: Validate migration
    try:
        valid, msg = validate_migration()
        print(f"✅ Migration validation: {msg}")
    except Exception as e:
        print(f"⚠️  Validation skipped: {e}")


# ============================================================================
# 7. INTEGRATION EXAMPLES
# ============================================================================

def example_full_integration():
    """Demonstrate full integration of all features."""
    from cache_manager import get_cache_manager
    from rate_limiter import get_rate_limiter
    from request_queue import get_request_queue, RequestPriority
    from memory_db import get_memory_db
    from metrics import get_metrics_collector, get_health_monitor
    
    print("\n" + "=" * 60)
    print("🧪 Full Integration Test")
    print("=" * 60)
    
    # Initialize all systems
    cache = get_cache_manager()
    limiter = get_rate_limiter()
    queue = get_request_queue()
    db = get_memory_db()
    metrics = get_metrics_collector()
    monitor = get_health_monitor()
    
    # Simulate typical workflow
    print("\n1️⃣  User asks a question...")
    user_question = "What is machine learning?"
    
    # Check if cached
    cached = cache.memory_cache.get(f"qa:{user_question}")
    if cached:
        print("   ✅ Found in cache!")
        response = cached
    else:
        print("   ❌ Not in cache, checking rate limits...")
        
        # Check rate limits
        model = "gpt-4"
        if not limiter.can_request(model):
            print("   ⏸️  Rate limited, waiting...")
            limiter.wait_for_request(model)
        
        print("   📤 Sending API request...")
        response = "Machine learning is a type of AI that learns from data"
        
        # Record API call
        metrics.record_api_call(model, tokens_used=50, latency=2.0)
        limiter.record_success(model)
        
        # Cache response
        cache.memory_cache.set(f"qa:{user_question}", response, ttl=3600)
    
    print(f"   💬 Response: {response}\n")
    
    # Store in memory
    print("2️⃣  Storing conversation...")
    db.add_conversation(user_question, response, model="gpt-4")
    print("   ✅ Stored\n")
    
    # Check metrics
    print("3️⃣  Checking system health...")
    stats = metrics.get_stats()
    health = monitor.check_health(stats)
    print(f"   📊 Status: {health['status'].upper()}")
    print(f"   📈 Cache hit rate: {stats['cache']['overall_hit_rate']:.1f}%\n")
    
    # Simulate second query
    print("4️⃣  User asks similar question...")
    user_question2 = "What is machine learning?"
    
    cached2 = cache.memory_cache.get(f"qa:{user_question2}")
    if cached2:
        print("   ⚡ FAST: Returned from cache!")
        metrics.record_api_call("gpt-4", cached=True)
    
    print("\n" + "=" * 60)
    print("✅ Full integration working perfectly!")
    print("=" * 60)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 JARVIS Upgrade - Integration Examples")
    print("=" * 70)
    
    try:
        print("\n\n📦 1. Caching Examples")
        print("-" * 70)
        example_caching()
        
        print("\n\n🔒 2. Rate Limiting Examples")
        print("-" * 70)
        example_rate_limiting()
        
        print("\n\n📋 3. Request Queue Examples")
        print("-" * 70)
        example_request_queue()
        
        print("\n\n🗄️  4. Memory Database Examples")
        print("-" * 70)
        example_memory_database()
        
        print("\n\n📊 5. Metrics & Monitoring Examples")
        print("-" * 70)
        example_metrics()
        
        print("\n\n🔄 6. Migration Examples")
        print("-" * 70)
        example_migration()
        
        print("\n\n🎯 7. Full Integration Example")
        print("-" * 70)
        example_full_integration()
        
        print("\n\n" + "=" * 70)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
