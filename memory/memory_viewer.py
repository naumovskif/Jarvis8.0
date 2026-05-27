"""
Memory Viewer & Dashboard
Simple CLI tool to inspect and manage conversation history
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

sys.path.insert(0, str(get_base_dir()))

from memory.conversation_logger import (
    get_conversation_history, get_all_tags, get_conversations_by_tag,
    get_statistics, search_by_date, get_conversation_count
)
from memory.semantic_search import search, get_search_stats, init_search_engine

def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_stats():
    """Display database statistics."""
    print_header("📊 MEMORY STATISTICS")
    
    stats = get_statistics()
    print(f"✅ Total conversations:     {stats['total_conversations']}")
    print(f"💡 Memory-relevant:         {stats['memory_relevant']}")
    print(f"🔍 Indexed for search:      {stats['indexed']}")
    print(f"🏷️  Unique tags:            {stats['unique_tags']}")
    print(f"💾 Database size:           {stats['db_size_kb']:.1f} KB")
    
    search_stats = get_search_stats()
    print(f"\n🔎 Search Index:")
    print(f"   Conversations indexed:  {search_stats['indexed_conversations']}")
    print(f"   Index size:             {search_stats['index_size_mb']:.1f} MB")
    print(f"   Model:                  {search_stats['model']}")
    print(f"   Ready:                  {'✅ Yes' if search_stats['ready'] else '❌ No'}")

def print_recent(limit: int = 10):
    """Display recent conversations."""
    print_header(f"📝 RECENT CONVERSATIONS (Last {limit})")
    
    conversations = get_conversation_history(limit=limit)
    if not conversations:
        print("No conversations found.")
        return
    
    for i, conv in enumerate(conversations, 1):
        timestamp = conv['timestamp'][:16]  # YYYY-MM-DD HH:MM
        user = conv['user_text'][:60].replace('\n', ' ')
        jarvis = conv['jarvis_text'][:60].replace('\n', ' ')
        
        print(f"\n#{conv['id']} | {timestamp}")
        print(f"  You:   {user}{'...' if len(conv['user_text']) > 60 else ''}")
        print(f"  MARK:  {jarvis}{'...' if len(conv['jarvis_text']) > 60 else ''}")

def print_tags():
    """Display all tags used."""
    print_header("🏷️  ALL TAGS")
    
    tags = get_all_tags()
    if not tags:
        print("No tags found.")
        return
    
    for tag in tags:
        count = len(get_conversations_by_tag(tag))
        print(f"  #{tag}: {count} conversations")

def search_memory(query: str):
    """Search for conversations by semantic similarity."""
    print_header(f"🔍 SEARCH RESULTS: '{query}'")
    
    if not query or len(query) < 3:
        print("Query must be at least 3 characters.")
        return
    
    results = search(query, top_k=5)
    if not results:
        print("No relevant conversations found.")
        return
    
    for i, result in enumerate(results, 1):
        score = result['similarity_score']
        timestamp = result['timestamp'][:16]
        user = result['user_text'][:70].replace('\n', ' ')
        jarvis = result['jarvis_text'][:70].replace('\n', ' ')
        
        print(f"\n#{i} | Score: {score:.2f} | {timestamp}")
        print(f"  You:  {user}{'...' if len(result['user_text']) > 70 else ''}")
        print(f"  MARK: {jarvis}{'...' if len(result['jarvis_text']) > 70 else ''}")

def search_by_tag(tag: str):
    """Search for conversations by tag."""
    print_header(f"🏷️  CONVERSATIONS WITH TAG: '{tag}'")
    
    results = get_conversations_by_tag(tag, limit=10)
    if not results:
        print(f"No conversations with tag '{tag}'.")
        return
    
    for i, conv in enumerate(results, 1):
        timestamp = conv['timestamp'][:16]
        user = conv['user_text'][:60].replace('\n', ' ')
        jarvis = conv['jarvis_text'][:60].replace('\n', ' ')
        
        print(f"\n#{i} | {timestamp}")
        print(f"  You:  {user}{'...' if len(conv['user_text']) > 60 else ''}")
        print(f"  MARK: {jarvis}{'...' if len(conv['jarvis_text']) > 60 else ''}")

def search_by_date_range(days: int = 7):
    """Search for conversations from the last N days."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    print_header(f"📅 CONVERSATIONS (Last {days} days)")
    print(f"Date range: {start_date} to {end_date}\n")
    
    results = search_by_date(str(start_date), str(end_date))
    if not results:
        print(f"No conversations from the last {days} days.")
        return
    
    for i, conv in enumerate(results, 1):
        timestamp = conv['timestamp'][:16]
        user = conv['user_text'][:60].replace('\n', ' ')
        jarvis = conv['jarvis_text'][:60].replace('\n', ' ')
        
        print(f"#{i} | {timestamp}")
        print(f"  You:  {user}{'...' if len(conv['user_text']) > 60 else ''}")
        print(f"  MARK: {jarvis}{'...' if len(conv['jarvis_text']) > 60 else ''}\n")

def print_full_conversation(conv_id: int):
    """Display full conversation details."""
    conversations = get_conversation_history(limit=10000)
    conv = next((c for c in conversations if c['id'] == conv_id), None)
    
    if not conv:
        print(f"❌ Conversation #{conv_id} not found.")
        return
    
    print_header(f"💬 FULL CONVERSATION #{conv_id}")
    print(f"Timestamp: {conv['timestamp']}")
    print(f"Language: {conv['language']}\n")
    print("─" * 70)
    print("YOU:")
    print(conv['user_text'])
    print("\n" + "─" * 70)
    print("MARK:")
    print(conv['jarvis_text'])
    print("─" * 70)

def show_menu():
    """Display interactive menu."""
    print_header("🧠 JARVIS MEMORY VIEWER")
    print("""
Commands:
  stats          - Show memory statistics
  recent [n]     - Show last N conversations (default: 10)
  tags           - Show all tags
  search <query> - Search by semantic similarity
  tag <tag>      - Search by tag name
  date [n]       - Show conversations from last N days (default: 7)
  view <id>      - Show full conversation by ID
  rebuild        - Rebuild search index
  help           - Show this menu
  exit           - Exit viewer
    """)

def main():
    """Main interactive loop."""
    print_header("🧠 JARVIS CONVERSATION MEMORY VIEWER")
    print("\nInitializing semantic search engine...")
    init_search_engine()
    print("✅ Ready!\n")
    
    show_menu()
    
    while True:
        try:
            user_input = input("\n📌 Enter command: ").strip().lower()
            
            if not user_input:
                continue
            
            parts = user_input.split(maxsplit=1)
            cmd = parts[0]
            arg = parts[1] if len(parts) > 1 else None
            
            if cmd == "exit":
                print("👋 Goodbye!")
                break
            
            elif cmd == "help":
                show_menu()
            
            elif cmd == "stats":
                print_stats()
            
            elif cmd == "recent":
                limit = int(arg) if arg and arg.isdigit() else 10
                print_recent(limit)
            
            elif cmd == "tags":
                print_tags()
            
            elif cmd == "search":
                if arg:
                    search_memory(arg)
                else:
                    print("❌ Usage: search <query>")
            
            elif cmd == "tag":
                if arg:
                    search_by_tag(arg)
                else:
                    print("❌ Usage: tag <tag_name>")
            
            elif cmd == "date":
                days = int(arg) if arg and arg.isdigit() else 7
                search_by_date_range(days)
            
            elif cmd == "view":
                if arg and arg.isdigit():
                    print_full_conversation(int(arg))
                else:
                    print("❌ Usage: view <conversation_id>")
            
            elif cmd == "rebuild":
                print("🔄 Rebuilding search index (this may take a minute)...")
                init_search_engine()
                print("✅ Index rebuilt!")
            
            else:
                print(f"❌ Unknown command: {cmd}")
                print("Type 'help' for available commands.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
