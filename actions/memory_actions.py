"""
Memory retrieval action for JARVIS
Allows users to ask "What did I say about X?" or "Find our conversation about Y?"
"""

from memory.semantic_search import search, get_search_stats
from memory.conversation_logger import get_conversation_history, get_conversations_by_tag

def memory_search(parameters: dict = None, player=None) -> str:
    """
    Search conversation history by query.
    
    Parameters:
        query (str): What to search for
        limit (int): Max results (default 3)
        by_tag (str): Search by tag instead of semantic search
    
    Returns:
        Formatted string with search results
    """
    if not parameters:
        return "No search query provided."
    
    query = parameters.get('query', '').strip()
    limit = min(int(parameters.get('limit', 3)), 10)
    by_tag = parameters.get('by_tag', '').strip()
    
    try:
        if by_tag:
            # Search by tag
            results = get_conversations_by_tag(by_tag, limit=limit)
            if not results:
                return f"No conversations found with tag: {by_tag}"
            
            output = f"Found {len(results)} conversation(s) tagged with '{by_tag}':\n\n"
            for i, conv in enumerate(results, 1):
                output += f"{i}. You said: {conv['user_text'][:100]}...\n"
                output += f"   I replied: {conv['jarvis_text'][:100]}...\n\n"
            return output.strip()
        
        else:
            # Semantic search
            if not query or len(query) < 3:
                return "Search query must be at least 3 characters."
            
            stats = get_search_stats()
            if not stats['ready']:
                return "Search index is not ready yet. Please try again in a moment."
            
            results = search(query, top_k=limit)
            if not results:
                return f"No relevant conversations found about: {query}"
            
            output = f"Found {len(results)} conversation(s) about '{query}':\n\n"
            for i, result in enumerate(results, 1):
                score = result['similarity_score']
                output += f"{i}. [Relevance: {score:.0%}]\n"
                output += f"   You said: {result['user_text'][:100]}...\n"
                output += f"   I replied: {result['jarvis_text'][:100]}...\n\n"
            return output.strip()
    
    except Exception as e:
        return f"Search failed: {str(e)[:100]}"

def memory_stats(parameters: dict = None, player=None) -> str:
    """
    Get statistics about stored conversations.
    
    Returns:
        Formatted statistics string
    """
    from memory.conversation_logger import get_statistics
    
    try:
        stats = get_statistics()
        search_stats = get_search_stats()
        
        output = f"""
📊 Your Memory Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Total conversations stored: {stats['total_conversations']}
• Memory-relevant entries: {stats['memory_relevant']}
• Indexed for search: {stats['indexed']}
• Database size: {stats['db_size_kb']:.1f} KB
• Search ready: {'Yes ✅' if search_stats['ready'] else 'No ❌'}
• Indexed conversations: {search_stats['indexed_conversations']}
        """.strip()
        
        return output
    
    except Exception as e:
        return f"Stats retrieval failed: {str(e)}"

def memory_recent(parameters: dict = None, player=None) -> str:
    """
    Get recent conversations.
    
    Parameters:
        limit (int): Number of recent conversations to return (default 5)
    
    Returns:
        Formatted string with recent conversations
    """
    try:
        limit = min(int(parameters.get('limit', 5) if parameters else 5), 20)
        conversations = get_conversation_history(limit=limit)
        
        if not conversations:
            return "No conversations found in memory."
        
        output = f"Your last {len(conversations)} conversation(s):\n\n"
        for i, conv in enumerate(conversations, 1):
            timestamp = conv['timestamp'][:16]
            output += f"{i}. [{timestamp}]\n"
            output += f"   You: {conv['user_text'][:80]}...\n"
            output += f"   Me: {conv['jarvis_text'][:80]}...\n\n"
        
        return output.strip()
    
    except Exception as e:
        return f"Failed to retrieve recent conversations: {str(e)}"
