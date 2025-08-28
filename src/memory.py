import chromadb
from sentence_transformers import SentenceTransformer
import re
import hashlib
import time
from typing import List
from pathlib import Path

# Paths
ROOT_PATH = Path(__file__).resolve().parent.parent
SRC_PATH = Path(__file__).resolve().parent

# Initialize embedding model
embed_model = SentenceTransformer('all-MiniLM-L6-v2')  # lightweight and free

# Initialize ChromaDB client (persist inside src folder)
client = chromadb.PersistentClient(path=str(SRC_PATH / "chroma_db"))

# Create or get collection
collection_name = "friday_memory"
try:
    collection = client.get_collection(collection_name)
except:
    collection = client.create_collection(collection_name)

# Embedding cache for performance
_EMBED_CACHE = {}

# Working memory (session-scoped) for last 3 user goals
_WORKING_GOALS: List[str] = []
_MAX_WORKING_GOALS = 3

# Patterns for useful memory content
IMPORTANT_PATTERNS = [
    r"\bremember\b", r"\bpreference\b", r"\bI like\b", r"\bdeadline\b",
    r"\bremind me\b", r"\btodo\b|\btask\b", r"\bdecision\b", r"\bgoal\b"
]


def is_useful_for_memory(text: str) -> bool:
    """Filter to only save useful, factual content"""
    if len(text) < 12:
        return False
    if any(re.search(p, text, flags=re.I) for p in IMPORTANT_PATTERNS):
        return True
    # also keep short crisp facts:
    return len(text) <= 200 and text.endswith((".", "!", "?"))


def embed(text: str):
    """Cache embeddings for performance (cuts ~30–60ms)"""
    key = hashlib.md5(text.encode("utf-8")).hexdigest()
    if key in _EMBED_CACHE:
        return _EMBED_CACHE[key]
    v = embed_model.encode(text).tolist()
    _EMBED_CACHE[key] = v
    return v


def push_working_goal(goal_text: str):
    """Push a new user goal to working memory (front), trim to last 3."""
    global _WORKING_GOALS
    goal_text = goal_text.strip()
    if not goal_text:
        return
    # de-dup simple
    _WORKING_GOALS = [g for g in _WORKING_GOALS if g.lower() != goal_text.lower()]
    _WORKING_GOALS.insert(0, goal_text)
    if len(_WORKING_GOALS) > _MAX_WORKING_GOALS:
        _WORKING_GOALS = _WORKING_GOALS[:_MAX_WORKING_GOALS]


def list_working_goals() -> List[str]:
    return list(_WORKING_GOALS)


def clear_working_goals():
    _WORKING_GOALS.clear()


def save_message(role, content):
    """Save a message to ChromaDB memory (filtered for usefulness)"""
    try:
        if not is_useful_for_memory(content):
            return False
        vec = embed(content)
        mid = f"{role}_{int(time.time()*1000)}"
        collection.add(
            documents=[content],
            metadatas=[{"role": role, "ts": time.time()}],
            ids=[mid],
            embeddings=[vec],
        )
        return True
    except Exception as e:
        print("save_message err:", e)
        return False


def retrieve_memory(query, top_k=3):
    """Retrieve relevant past messages with recency + relevance scoring"""
    try:
        qv = embed(query)
        res = collection.query(query_embeddings=[qv], n_results=min(top_k*4, 12))
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        scored = []
        now = time.time()
        for i, d in enumerate(docs):
            age_sec = max(1.0, now - metas[i].get("ts", now))
            recency = 1.0 / (1.0 + age_sec/86400.0)
            brevity = 1.0 / (1 + max(0, len(d) - 160)/160)
            score = 1.0 * recency + 0.3 * brevity
            scored.append((score, metas[i], d))
        scored.sort(key=lambda x: x[0], reverse=True)
        out = [{"role": m.get("role","user"), "content": d} for (s,m,d) in scored[:top_k]]
        return out
    except Exception as e:
        print("retrieve_memory err:", e)
        return []


def get_memory_stats():
    """Get basic stats about stored memory"""
    try:
        count = collection.count()
        return count
    except Exception as e:
        print(f"Error getting memory stats: {e}")
        return 0


def get_all_messages(limit=10):
    """Get all stored messages for inspection"""
    try:
        results = collection.get(limit=limit)
        messages = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            messages.append({
                'id': results['ids'][i],
                'content': results['documents'][i],
                'role': metadata['role'],
                'timestamp': metadata.get('ts', metadata.get('timestamp', time.time())),
                'pinned': metadata.get('pinned', False),
                'pin_note': metadata.get('pin_note', '')
            })
        return messages
    except Exception as e:
        print(f"Error getting messages: {e}")
        return []


def generate_tags_for_conversation(conversation_text: str) -> List[str]:
    """Generate tags for conversation using LLM"""
    try:
        tag_prompt = f"Generate 3-5 relevant tags for this conversation (comma-separated):\n{conversation_text[:500]}"
        from .llm_utils import query_ollama
        tags_response = query_ollama(tag_prompt)
        tags = [tag.strip() for tag in tags_response.split(',') if tag.strip()]
        return tags[:5]
    except Exception as e:
        print("generate_tags err:", e)
        return []


def clear_all_memory():
    """Clear all stored memory"""
    try:
        client.delete_collection(collection_name)
        global collection
        collection = client.create_collection(collection_name)
        global _EMBED_CACHE
        _EMBED_CACHE.clear()
        clear_working_goals()
        return True
    except Exception as e:
        print("clear_all_memory err:", e)
        return False


def delete_message_by_id(message_id: str):
    """Delete a specific message by ID"""
    try:
        collection.delete(ids=[message_id])
        return True
    except Exception as e:
        print("delete_message_by_id err:", e)
        return False


def pin_message(message_id: str, pin_note: str = ""):
    """Pin a message with optional note"""
    try:
        result = collection.get(ids=[message_id])
        if not result.get("documents"):
            return False
        collection.update(
            ids=[message_id],
            metadatas=[{
                "role": result["metadatas"][0]["role"],
                "ts": result["metadatas"][0]["ts"],
                "pinned": True,
                "pin_note": pin_note
            }]
        )
        return True
    except Exception as e:
        print("pin_message err:", e)
        return False


def unpin_message(message_id: str):
    """Unpin a message"""
    try:
        result = collection.get(ids=[message_id])
        if not result.get("documents"):
            return False
        metadata = result["metadatas"][0].copy()
        metadata.pop("pinned", None)
        metadata.pop("pin_note", None)
        collection.update(ids=[message_id], metadatas=[metadata])
        return True
    except Exception as e:
        print("unpin_message err:", e)
        return False


def get_pinned_messages():
    """Get all pinned messages"""
    try:
        results = collection.get()
        pinned = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            if metadata.get('pinned'):
                pinned.append({
                    'id': results['ids'][i],
                    'content': results['documents'][i],
                    'role': metadata['role'],
                    'timestamp': metadata.get('ts', time.time()),
                    'pin_note': metadata.get('pin_note', '')
                })
        return pinned
    except Exception as e:
        print("get_pinned_messages err:", e)
        return []


def summarize_and_compact(limit=40):
    """Periodic compaction to keep DB small & fast with smart tagging"""
    try:
        res = collection.get(limit=limit)
        if not res.get("documents"):
            return
        docs = res["documents"]
        if len(docs) < limit:
            return
        conversation_text = "\n".join(docs[-limit:])
        tags = generate_tags_for_conversation(conversation_text)
        points = "\n".join(f"- {d[:140]}" for d in docs[-limit:])
        summary_prompt = f"Summarize these points into 8 crisp bullets of lasting facts:\n{points}\nSummary:"
        from .llm_utils import stream_ollama
        summary = "".join(tok for tok in stream_ollama(summary_prompt))
        collection.add(
            documents=[summary],
            metadatas=[{
                "role":"assistant",
                "ts": time.time(),
                "type":"summary",
                "tags": ",".join(tags)
            }],
            ids=[f"summary_{int(time.time()*1000)}"],
            embeddings=[embed(summary)]
        )
    except Exception as e:
        print("summarize_and_compact err:", e)


def forget_by_text(query_text: str, top_k: int = 5) -> int:
    """Delete up to top_k semantically similar memories to query_text. Returns count deleted."""
    try:
        qv = embed(query_text)
        res = collection.query(query_embeddings=[qv], n_results=top_k)
        ids = res.get('ids', [[]])[0]
        if not ids:
            return 0
        collection.delete(ids=ids)
        return len(ids)
    except Exception as e:
        print("forget_by_text err:", e)
        return 0


