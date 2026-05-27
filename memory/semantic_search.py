import numpy as np
import pickle
from pathlib import Path
import sys
from threading import Lock

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    print("[SemanticSearch] ⚠️ Dependencies not installed. Install: pip install sentence-transformers faiss-cpu")

from memory.conversation_logger import (
    get_conversation_history, store_embedding, get_embedding
)

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
CACHE_DIR = BASE_DIR / "memory" / ".semantic_cache"
INDEX_PATH = CACHE_DIR / "faiss_index.bin"
METADATA_PATH = CACHE_DIR / "metadata.pkl"
MODEL_NAME = "all-MiniLM-L6-v2"  # Lightweight, fast, accurate

_model = None
_index = None
_metadata = None
_lock = Lock()

def init_search_engine() -> bool:
    """
    Initialize the semantic search engine.
    Loads model and rebuilds FAISS index if needed.
    
    Returns:
        True if successful, False otherwise
    """
    global _model, _index, _metadata
    
    if not SEMANTIC_AVAILABLE:
        print("[SemanticSearch] ❌ sentence-transformers or faiss-cpu not installed")
        return False
    
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load model
        print(f"[SemanticSearch] 📦 Loading {MODEL_NAME}...")
        import os
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        
        _model = SentenceTransformer(MODEL_NAME, device='cpu')
        print(f"[SemanticSearch] ✅ Model loaded successfully")
        
        # Try to load existing index
        if INDEX_PATH.exists() and METADATA_PATH.exists():
            try:
                print(f"[SemanticSearch] 📂 Loading existing index...")
                _index = faiss.read_index(str(INDEX_PATH))
                with open(METADATA_PATH, 'rb') as f:
                    _metadata = pickle.load(f)
                print(f"[SemanticSearch] ✅ Loaded {len(_metadata)} indexed conversations")
                return True
            except Exception as e:
                print(f"[SemanticSearch] ⚠️ Index load failed, rebuilding: {e}")
                _rebuild_index()
                return True
        else:
            print(f"[SemanticSearch] 🔄 Building new index (no conversations yet)...")
            _rebuild_index()
            return True
            
    except Exception as e:
        print(f"[SemanticSearch] ⚠️ Init failed (non-critical): {e}")
        _model = None
        _index = None
        _metadata = None
        return False

def _rebuild_index() -> None:
    """Rebuild FAISS index from all conversations."""
    global _index, _metadata
    
    if _model is None:
        return
    
    try:
        conversations = get_conversation_history(limit=10000)
        
        if not conversations:
            print("[SemanticSearch] No conversations to index")
            _index = faiss.IndexFlatL2(384)  # dimension of all-MiniLM-L6-v2
            _metadata = []
            return
        
        print(f"[SemanticSearch] 📝 Indexing {len(conversations)} conversations (this may take a moment)...")
        
        texts = []
        metadata = []
        
        for conv in conversations:
            # Combine user + jarvis text for better context
            combined = f"{conv['user_text']} {conv['jarvis_text']}"
            texts.append(combined)
            metadata.append({
                'id': conv['id'],
                'timestamp': conv['timestamp'],
                'user_text': conv['user_text'][:200],
                'jarvis_text': conv['jarvis_text'][:200]
            })
        
        # Embed all texts - disable progress bar and batch processing
        try:
            embeddings = _model.encode(texts, show_progress_bar=False, normalize_embeddings=True, batch_size=32)
            embeddings = embeddings.astype('float32')
            
            # Create FAISS index
            _index = faiss.IndexFlatL2(embeddings.shape[1])
            _index.add(embeddings)
            
            _metadata = metadata
            
            # Save index and metadata
            faiss.write_index(_index, str(INDEX_PATH))
            with open(METADATA_PATH, 'wb') as f:
                pickle.dump(_metadata, f)
            
            print(f"[SemanticSearch] ✅ Indexed {len(metadata)} conversations")
        except Exception as encode_error:
            print(f"[SemanticSearch] ⚠️ Encoding failed (search disabled): {encode_error}")
            # Create empty index as fallback
            _index = faiss.IndexFlatL2(384)
            _metadata = []
    
    except Exception as e:
        print(f"[SemanticSearch] ⚠️ Rebuild failed: {e}")

def embed_text(text: str) -> np.ndarray | None:
    """
    Convert text to embedding vector.
    
    Args:
        text: Text to embed
    
    Returns:
        Embedding array or None
    """
    if _model is None:
        return None
    
    try:
        embedding = _model.encode(text, normalize_embeddings=True)
        return embedding.astype('float32')
    except Exception as e:
        print(f"[SemanticSearch] ⚠️ Embedding failed: {e}")
        return None

def search(query: str, top_k: int = 5) -> list:
    """
    Find conversations similar to the query.
    
    Args:
        query: Search query
        top_k: Number of results to return
    
    Returns:
        List of similar conversations with scores
    """
    if _model is None or _index is None or _metadata is None:
        return []
    
    if not query or len(query.strip()) < 3:
        return []
    
    try:
        # Embed query
        query_embedding = embed_text(query)
        if query_embedding is None:
            return []
        
        query_embedding = np.array([query_embedding])
        
        # Search index
        distances, indices = _index.search(query_embedding, min(top_k, len(_metadata)))
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(_metadata):
                continue
            
            meta = _metadata[idx]
            results.append({
                'id': meta['id'],
                'timestamp': meta['timestamp'],
                'user_text': meta['user_text'],
                'jarvis_text': meta['jarvis_text'],
                'similarity_score': float(1 / (1 + distances[0][i]))  # Convert L2 distance to similarity
            })
        
        return results
    
    except Exception as e:
        print(f"[SemanticSearch] ⚠️ Search failed: {e}")
        return []

def add_to_index(text: str, metadata_entry: dict) -> bool:
    """
    Add a new conversation to the index.
    
    Args:
        text: Combined user + jarvis text
        metadata_entry: Metadata dict with id, timestamp, user_text, jarvis_text
    
    Returns:
        True if successful
    """
    global _index, _metadata
    
    if _model is None or _index is None or _metadata is None:
        return False
    
    try:
        embedding = embed_text(text)
        if embedding is None:
            return False
        
        embedding = np.array([embedding], dtype='float32')
        _index.add(embedding)
        _metadata.append(metadata_entry)
        
        # Save updated index
        faiss.write_index(_index, str(INDEX_PATH))
        with open(METADATA_PATH, 'wb') as f:
            pickle.dump(_metadata, f)
        
        return True
    
    except Exception as e:
        print(f"[SemanticSearch] ⚠️ Add to index failed: {e}")
        return False

def rebuild_index_async() -> None:
    """Rebuild index in background (call this periodically)."""
    with _lock:
        _rebuild_index()

def get_search_stats() -> dict:
    """Get statistics about the search index."""
    return {
        'indexed_conversations': len(_metadata) if _metadata else 0,
        'index_size_mb': INDEX_PATH.stat().st_size / (1024*1024) if INDEX_PATH.exists() else 0,
        'model': MODEL_NAME,
        'ready': _model is not None and _index is not None
    }

def clear_index() -> None:
    """Clear the search index (for debugging/reset)."""
    global _index, _metadata
    try:
        if INDEX_PATH.exists():
            INDEX_PATH.unlink()
        if METADATA_PATH.exists():
            METADATA_PATH.unlink()
        _index = None
        _metadata = None
        print("[SemanticSearch] ✅ Index cleared")
    except Exception as e:
        print(f"[SemanticSearch] ⚠️ Clear failed: {e}")
