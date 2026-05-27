#!/usr/bin/env python
"""Test memory system end-to-end"""

from memory.conversation_logger import log_conversation, get_statistics
from memory.semantic_search import search

print("\n" + "="*60)
print("TESTING MEMORY SYSTEM")
print("="*60 + "\n")

# Test 1: Log a conversation
try:
    log_conversation('Test user input', 'Test response from JARVIS')
    print("[OK] Conversation logged successfully")
except Exception as e:
    print(f"[ERROR] Failed to log: {e}")
    exit(1)

# Test 2: Get statistics
try:
    stats = get_statistics()
    print(f"[OK] Database stats:")
    print(f"     - Total conversations: {stats['total_conversations']}")
    print(f"     - Indexed for search: {stats['indexed']}")
    print(f"     - Database size: {stats['db_size_kb']:.1f} KB")
except Exception as e:
    print(f"[ERROR] Failed to get stats: {e}")
    exit(1)

# Test 3: Search
try:
    results = search('test', top_k=1)
    print(f"[OK] Search returned {len(results)} result(s)")
    if results:
        print(f"     - Top match score: {results[0]['similarity_score']:.0%}")
except Exception as e:
    print(f"[ERROR] Failed to search: {e}")
    exit(1)

print("\n" + "="*60)
print("SUCCESS - MEMORY SYSTEM FULLY OPERATIONAL")
print("="*60 + "\n")
