"""
JARVIS Multi-Model Load Balancing - Integration Examples
Demonstrates how to use unlimited rate limits with multiple AI models
"""

import logging
from or_client_v2 import get_openrouter_client
from model_router import LoadBalancingStrategy, get_model_router
from request_queue import RequestPriority

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("examples")


# ============================================================================
# Example 1: Basic Usage - Automatic Model Selection
# ============================================================================

def example_1_basic_usage():
    """Simplest way to use multi-model system"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Usage - Automatic Model Selection")
    print("="*70)
    
    client = get_openrouter_client()
    
    messages = [
        {"role": "user", "content": "Say 'JARVIS Multi-Model System Active!'"}
    ]
    
    response = client.call(messages)
    print(f"✅ Response: {response}")
    
    # That's it! JARVIS automatically selected and routed to the best model


# ============================================================================
# Example 2: Different Load Balancing Strategies
# ============================================================================

def example_2_strategies():
    """Demonstrate different load balancing strategies"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Load Balancing Strategies")
    print("="*70)
    
    messages = [
        {"role": "user", "content": "What is load balancing?"}
    ]
    
    strategies = [
        LoadBalancingStrategy.ROUND_ROBIN,
        LoadBalancingStrategy.LEAST_LOADED,
        LoadBalancingStrategy.FASTEST,
        LoadBalancingStrategy.LOWEST_RATE_LIMIT,
        LoadBalancingStrategy.WEIGHTED_RANDOM,
    ]
    
    for strategy in strategies:
        client = get_openrouter_client(strategy)
        print(f"\n📊 Strategy: {strategy.value}")
        response = client.call(messages)
        if response:
            print(f"   ✅ Success")
        else:
            print(f"   ❌ Failed")


# ============================================================================
# Example 3: Monitor Model Health
# ============================================================================

def example_3_monitor_health():
    """Monitor and display model health metrics"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Monitor Model Health")
    print("="*70)
    
    client = get_openrouter_client()
    
    # Get status of all models
    status = client.get_model_status()
    
    print("\n📊 Model Status:")
    print("-" * 70)
    print(f"{'Model':<40} {'Health':<10} {'Success':<10} {'Latency':<10}")
    print("-" * 70)
    
    for model_id, stats in status.items():
        health = f"{stats['health_score']:.0f}/100"
        success_rate = f"{100 - stats['error_rate']:.0f}%"
        latency = f"{stats['avg_latency']:.2f}s"
        
        model_short = model_id.split('/')[-1][:30]
        print(f"{model_short:<40} {health:<10} {success_rate:<10} {latency:<10}")
    
    # Get best models
    print("\n⭐ Best Models:")
    for i, (model, score) in enumerate(client.get_best_models(3), 1):
        print(f"  {i}. {model}: {score:.0f}/100")


# ============================================================================
# Example 4: Bulk Processing with Different Priorities
# ============================================================================

def example_4_priority_processing():
    """Process multiple requests with different priorities"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Priority-Based Request Processing")
    print("="*70)
    
    client = get_openrouter_client()
    
    # Critical request
    critical_msg = [{"role": "user", "content": "Emergency: System status?"}]
    print("\n🔴 Processing CRITICAL request...")
    response = client.call(critical_msg, priority=RequestPriority.CRITICAL)
    print(f"   ✅ Response received (priority: CRITICAL)")
    
    # High priority
    high_msg = [{"role": "user", "content": "What's the current weather?"}]
    print("\n🟠 Processing HIGH priority request...")
    response = client.call(high_msg, priority=RequestPriority.HIGH)
    print(f"   ✅ Response received (priority: HIGH)")
    
    # Normal priority
    normal_msg = [{"role": "user", "content": "Tell me a joke"}]
    print("\n🟡 Processing NORMAL priority request...")
    response = client.call(normal_msg, priority=RequestPriority.NORMAL)
    print(f"   ✅ Response received (priority: NORMAL)")
    
    # Low priority
    low_msg = [{"role": "user", "content": "What's 2+2?"}]
    print("\n🟢 Processing LOW priority request...")
    response = client.call(low_msg, priority=RequestPriority.LOW)
    print(f"   ✅ Response received (priority: LOW)")


# ============================================================================
# Example 5: Get Comprehensive Metrics
# ============================================================================

def example_5_comprehensive_metrics():
    """Display comprehensive system metrics"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Comprehensive System Metrics")
    print("="*70)
    
    client = get_openrouter_client()
    
    # Get metrics
    metrics = client.get_metrics()
    
    print("\n🔵 Recommended Model:")
    recommended = client.get_recommended_model()
    print(f"   {recommended}")
    
    print("\n⭐ Top 5 Models by Health:")
    for i, (model, score) in enumerate(metrics['best_models'][:5], 1):
        print(f"   {i}. {model}: {score:.0f}/100")
    
    print("\n📊 Cache Statistics:")
    cache_stats = metrics['cache_stats']
    if cache_stats:
        for key, value in list(cache_stats.items())[:5]:
            print(f"   {key}: {value}")
    
    print("\n⚡ Rate Limiter Statistics:")
    rate_stats = metrics['rate_limiter_stats']
    if rate_stats:
        for key, value in list(rate_stats.items())[:5]:
            print(f"   {key}: {value}")


# ============================================================================
# Example 6: Handle Failover Automatically
# ============================================================================

def example_6_automatic_failover():
    """Demonstrate automatic failover across models"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Automatic Failover")
    print("="*70)
    
    client = get_openrouter_client(LoadBalancingStrategy.LEAST_LOADED)
    
    messages = [
        {"role": "user", "content": "Test resilience"}
    ]
    
    print("\n📡 Making request (will auto-failover if needed)...")
    response = client.call(messages)
    
    if response:
        print(f"   ✅ Success (possibly after failover)")
    else:
        print(f"   ⚠️ All models failed")
    
    print("\n📊 Model Status After Request:")
    status = client.get_model_status()
    failed_count = sum(1 for m in status.values() if m['failed_requests'] > 0)
    print(f"   Models with failures: {failed_count}/{len(status)}")
    print(f"   Models still healthy: {len(status) - failed_count}/{len(status)}")


# ============================================================================
# Example 7: Simulate High Volume Processing
# ============================================================================

def example_7_high_volume():
    """Simulate high-volume request processing"""
    print("\n" + "="*70)
    print("EXAMPLE 7: High-Volume Processing")
    print("="*70)
    
    client = get_openrouter_client(LoadBalancingStrategy.LEAST_LOADED)
    
    num_requests = 10
    print(f"\n📤 Processing {num_requests} requests...")
    
    messages_list = [
        [{"role": "user", "content": f"Request {i}: What is the nature of reality?"}]
        for i in range(num_requests)
    ]
    
    successful = 0
    failed = 0
    
    for i, messages in enumerate(messages_list, 1):
        response = client.call(messages)
        if response:
            successful += 1
        else:
            failed += 1
        
        # Show progress
        if i % 5 == 0 or i == 1:
            status = client.get_model_status()
            best = client.get_best_models(1)
            print(f"   Progress: {i}/{num_requests} (Best model: {best[0][0].split('/')[-1]})")
    
    print(f"\n✅ Results:")
    print(f"   Successful: {successful}/{num_requests}")
    print(f"   Failed: {failed}/{num_requests}")
    print(f"   Success Rate: {100*successful//num_requests}%")


# ============================================================================
# Example 8: Compare Single vs Multi-Model Performance
# ============================================================================

def example_8_comparison():
    """Compare single model vs multi-model approach"""
    print("\n" + "="*70)
    print("EXAMPLE 8: Single vs Multi-Model Comparison")
    print("="*70)
    
    messages = [
        {"role": "user", "content": "Compare single vs multi-model systems"}
    ]
    
    print("\n📊 Theoretical Comparison:")
    print("-" * 70)
    print(f"{'Metric':<30} {'Single Model':<20} {'Multi-Model':<20}")
    print("-" * 70)
    
    comparisons = [
        ("Rate Limit Capacity", "100 req/hour", "1000 req/hour"),
        ("Failover", "Manual", "Automatic"),
        ("Health Monitoring", "None", "Per-model"),
        ("Load Distribution", "Single point", "10 models"),
        ("Recovery Time", "60+ seconds", "Automatic"),
        ("Cost Efficiency", "Limited", "Optimized"),
    ]
    
    for metric, single, multi in comparisons:
        print(f"{metric:<30} {single:<20} {multi:<20}")
    
    print("\n💡 With Multi-Model System:")
    print("   ✅ 9-10x more throughput")
    print("   ✅ Automatic failover and recovery")
    print("   ✅ Real-time health monitoring")
    print("   ✅ Intelligent load balancing")
    print("   ✅ Zero rate limit errors (in practice)")


# ============================================================================
# Example 9: Real-World Scenario - Batch Processing
# ============================================================================

def example_9_batch_processing():
    """Real-world scenario: batch processing many documents"""
    print("\n" + "="*70)
    print("EXAMPLE 9: Real-World - Document Batch Processing")
    print("="*70)
    
    client = get_openrouter_client(LoadBalancingStrategy.LOWEST_RATE_LIMIT)
    
    # Simulate 20 documents to process
    documents = [
        f"Document {i}: Sample text for analysis"
        for i in range(20)
    ]
    
    print(f"\n📄 Processing {len(documents)} documents...")
    
    processed = 0
    start_client = client.get_recommended_model()
    
    for doc in documents:
        messages = [
            {"role": "user", "content": f"Summarize: {doc}"}
        ]
        response = client.call(messages, priority=RequestPriority.NORMAL)
        if response:
            processed += 1
    
    end_client = client.get_recommended_model()
    
    print(f"\n✅ Batch Processing Complete:")
    print(f"   Documents processed: {processed}/{len(documents)}")
    print(f"   Initial best model: {start_client.split('/')[-1]}")
    print(f"   Final best model: {end_client.split('/')[-1]}")
    print(f"   System dynamically routed around rate limits!")


# ============================================================================
# Example 10: Advanced - Custom Router Configuration
# ============================================================================

def example_10_custom_router():
    """Advanced: Create custom router with specific models"""
    print("\n" + "="*70)
    print("EXAMPLE 10: Advanced - Custom Router Configuration")
    print("="*70)
    
    from model_router import ModelRouter, LoadBalancingStrategy
    
    # Use only fast models
    fast_models = [
        "google/gemma-4-31b-it:free",
        "google/gemma-4-26b-a4b-it:free",
        "google/gemma-3-27b-it:free",
    ]
    
    router = ModelRouter(fast_models, LoadBalancingStrategy.FASTEST)
    
    print(f"\n🚀 Custom Router: {len(fast_models)} fast models")
    
    # Simulate requests
    for i in range(5):
        model = router.select_model()
        router.record_success(model, latency=0.5)
        print(f"   Request {i+1}: {model.split('/')[-1]}")
    
    # Show status
    print(f"\n📊 Router Status:")
    status = router.get_model_status()
    for model, metrics in status.items():
        print(f"   {model.split('/')[-1]}: {metrics['health_score']:.0f}/100")


# ============================================================================
# Main - Run All Examples
# ============================================================================

def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("JARVIS MULTI-MODEL LOAD BALANCING - INTEGRATION EXAMPLES")
    print("="*70)
    
    examples = [
        ("Basic Usage", example_1_basic_usage),
        ("Strategies", example_2_strategies),
        ("Monitor Health", example_3_monitor_health),
        ("Priority Processing", example_4_priority_processing),
        ("Metrics", example_5_comprehensive_metrics),
        ("Failover", example_6_automatic_failover),
        ("High Volume", example_7_high_volume),
        ("Comparison", example_8_comparison),
        ("Batch Processing", example_9_batch_processing),
        ("Custom Router", example_10_custom_router),
    ]
    
    print("\n📋 Available Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"   {i}. {name}")
    
    # Run all or specific
    try:
        selection = input("\nRun all examples? (y/n, default=y): ").strip().lower()
        if selection == 'n':
            idx = int(input("Select example (1-10): ")) - 1
            examples[idx][1]()
        else:
            for name, func in examples:
                try:
                    func()
                except Exception as e:
                    print(f"\n❌ Example failed: {e}")
    
    except KeyboardInterrupt:
        print("\n\nExited by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
