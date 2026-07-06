"""VOLT OS — Semantic Search via pgvector. RAG retrieval for memory system."""
from sqlalchemy import Column, String, Text, Integer
from pgvector.sqlalchemy import Vector
from src.core.database import Base
import numpy as np


class MemoryEmbedding(Base):
    """Vector embeddings for semantic search over memory entries."""
    __tablename__ = "memory_embeddings"

    id = Column(String(36), primary_key=True)
    memory_entry_id = Column(String(36), nullable=False, index=True)
    content_hash = Column(String(64), nullable=False)  # dedup check
    embedding = Column(Vector(1536))  # text-embedding-3-small dimension
    model = Column(String(50), default="text-embedding-3-small")
    chunk_index = Column(Integer, default=0)
    chunk_text = Column(Text)


class SemanticSearch:
    """Vector similarity search over memory entries."""

    def __init__(self, db):
        self.db = db

    def embed_and_store(self, memory_entry_id: str, text: str, embedding_fn=None):
        """Generate embedding and store for a memory entry."""
        if embedding_fn is None:
            # Placeholder: random vector for testing
            embedding = np.random.rand(1536).tolist()
        else:
            embedding = embedding_fn(text)

        record = MemoryEmbedding(
            id=f"emb-{memory_entry_id}",
            memory_entry_id=memory_entry_id,
            content_hash=str(hash(text)),
            embedding=embedding,
            chunk_text=text[:500],
        )
        self.db.add(record)
        self.db.commit()

    def search(self, query_embedding: list[float], top_k: int = 5, level: str = None) -> list[dict]:
        """Semantic similarity search via pgvector cosine distance."""
        from sqlalchemy import text

        query = text("""
            SELECT me.memory_entry_id, me.chunk_text,
                   1 - (me.embedding <=> :query_vec) as similarity
            FROM memory_embeddings me
            ORDER BY me.embedding <=> :query_vec
            LIMIT :top_k
        """)

        results = self.db.execute(query, {
            "query_vec": str(query_embedding),
            "top_k": top_k,
        }).fetchall()

        return [
            {"memory_entry_id": r[0], "chunk": r[1], "similarity": float(r[2])}
            for r in results
        ]
