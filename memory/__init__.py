#memory package

# Long-term structured memory
from memory.memory_manager import (
    load_memory,
    update_memory,
    format_memory_for_prompt,
    should_extract_memory,
    extract_memory,
    remember,
    forget,
    get_relevant_context,
)

# Conversation history
from memory.conversation_logger import (
    log_conversation,
    get_conversation_history,
    get_conversations_by_tag,
    add_tags_to_conversation,
    mark_memory_relevant,
    get_conversation_count,
    get_all_tags,
    get_statistics,
)

# Semantic search - lazy import (avoids blocking on model download)
def __getattr__(name):
    if name in ('init_search_engine', 'embed_text', 'search', 'get_search_stats'):
        from memory import semantic_search
        return getattr(semantic_search, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    # Memory management
    'load_memory',
    'update_memory',
    'format_memory_for_prompt',
    'should_extract_memory',
    'extract_memory',
    'remember',
    'forget',
    'get_relevant_context',
    
    # Conversation logging
    'log_conversation',
    'get_conversation_history',
    'get_conversations_by_tag',
    'add_tags_to_conversation',
    'mark_memory_relevant',
    'get_conversation_count',
    'get_all_tags',
    'get_statistics',
    
    # Search (lazy imports)
    'init_search_engine',
    'embed_text',
    'search',
    'get_search_stats',
]