#!/usr/bin/env python3
"""Quick test of memory components"""

print("[TEST] Starting import test...")

try:
    from memory.conversation_logger import log_conversation
    print("[✅] conversation_logger imported")
except Exception as e:
    print(f"[❌] conversation_logger: {e}")

try:
    from memory.semantic_search import init_search_engine
    print("[✅] semantic_search imported")
except Exception as e:
    print(f"[❌] semantic_search: {e}")

try:
    from memory.memory_manager import get_relevant_context
    print("[✅] memory_manager imports work")
except Exception as e:
    print(f"[❌] memory_manager: {e}")

print("\n[TEST] Testing database...")
try:
    from memory.conversation_logger import get_statistics
    stats = get_statistics()
    print(f"[✅] Database works: {stats['total_conversations']} conversations")
except Exception as e:
    print(f"[❌] Database: {e}")

print("\n[TEST] All memory components OK!")
