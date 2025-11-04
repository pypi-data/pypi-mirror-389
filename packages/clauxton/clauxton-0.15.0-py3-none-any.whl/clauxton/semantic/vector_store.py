"""
FAISS-based vector store for semantic search.

This module provides efficient similarity search using FAISS (Facebook AI Similarity Search).
All data is stored locally with no external dependencies.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

import numpy as np

# Optional import - graceful degradation if not installed
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    if TYPE_CHECKING:
        import faiss


class VectorStore:
    """
    FAISS-based vector storage with metadata support.

    Features:
    - Fast similarity search using FAISS IndexFlatIP (cosine similarity)
    - Metadata storage for each vector
    - Persistent storage (save/load to disk)
    - Incremental indexing (add vectors one by one or in batches)
    - Filtering support (metadata-based filtering)

    Storage Structure:
    - Vectors: FAISS index (binary format)
    - Metadata: JSON file (human-readable)

    Example:
        >>> store = VectorStore(dimension=384)
        >>> embeddings = np.random.rand(10, 384)
        >>> metadata = [{"id": i, "text": f"Doc {i}"} for i in range(10)]
        >>> store.add(embeddings, metadata)
        >>> query = np.random.rand(384)
        >>> results = store.search(query, k=5)
        >>> print(results[0]["distance"], results[0]["metadata"])
    """

    def __init__(self, dimension: int = 384):
        """
        Initialize vector store.

        Args:
            dimension: Embedding dimension (default: 384 for all-MiniLM-L6-v2)

        Raises:
            ImportError: If faiss-cpu is not installed
        """
        if not FAISS_AVAILABLE:
            raise ImportError(
                "faiss-cpu is required for semantic search. "
                "Install with: pip install clauxton[semantic]"
            )

        self.dimension = dimension
        # Use IndexFlatIP for cosine similarity (requires normalized vectors)
        # Note: Inner product on normalized vectors = cosine similarity
        self.index: "faiss.IndexFlatIP" = faiss.IndexFlatIP(dimension)
        self.metadata: List[Dict[str, Any]] = []

    def add(
        self,
        embeddings: np.ndarray,
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Add embeddings to the vector store.

        Args:
            embeddings: numpy array of shape (n, dimension) or (dimension,)
            metadata: Optional list of metadata dicts (one per embedding)

        Raises:
            ValueError: If embedding dimension mismatch
            ValueError: If metadata length doesn't match embeddings

        Example:
            >>> store = VectorStore(dimension=384)
            >>> embeddings = np.random.rand(5, 384)
            >>> metadata = [{"id": i} for i in range(5)]
            >>> store.add(embeddings, metadata)
        """
        # Handle single embedding (1D array)
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        # Validate dimension
        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, "
                f"got {embeddings.shape[1]}"
            )

        # Validate metadata
        if metadata is not None:
            if len(metadata) != len(embeddings):
                raise ValueError(
                    f"Metadata length ({len(metadata)}) must match "
                    f"embeddings count ({len(embeddings)})"
                )
        else:
            # Create empty metadata for each embedding
            metadata = [{} for _ in range(len(embeddings))]

        # Normalize embeddings for cosine similarity
        # (IndexFlatIP with normalized vectors = cosine similarity)
        normalized_embeddings = self._normalize(embeddings)

        # Add to FAISS index
        self.index.add(normalized_embeddings.astype(np.float32))

        # Store metadata
        self.metadata.extend(metadata)

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            query_embedding: Query vector (1D array of shape (dimension,))
            k: Number of results to return
            filter_fn: Optional filter function (takes metadata dict, returns bool)

        Returns:
            List of result dicts with keys:
                - distance: Cosine similarity (0-1, higher = more similar)
                - metadata: Metadata dict
                - index: Index in the store

        Example:
            >>> query = np.random.rand(384)
            >>> results = store.search(query, k=5)
            >>> top_result = results[0]
            >>> print(f"Similarity: {top_result['distance']:.3f}")
            >>> print(f"Metadata: {top_result['metadata']}")
        """
        # Handle empty index
        if self.index.ntotal == 0:
            return []

        # Ensure query is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # Validate dimension
        if query_embedding.shape[1] != self.dimension:
            raise ValueError(
                f"Query dimension mismatch: expected {self.dimension}, "
                f"got {query_embedding.shape[1]}"
            )

        # Normalize query for cosine similarity
        normalized_query = self._normalize(query_embedding)

        # Search FAISS index
        # For IndexFlatIP, distance is inner product (cosine similarity if normalized)
        distances, indices = self.index.search(
            normalized_query.astype(np.float32), min(k, self.index.ntotal)
        )

        # Build results
        results: List[Dict[str, Any]] = []
        for distance, idx in zip(distances[0], indices[0]):
            # Skip invalid indices (FAISS returns -1 for missing results)
            if idx < 0:
                continue

            metadata = self.metadata[idx]

            # Apply filter if provided
            if filter_fn is not None and not filter_fn(metadata):
                continue

            results.append(
                {
                    "distance": float(distance),  # Cosine similarity (0-1)
                    "metadata": metadata,
                    "index": int(idx),
                }
            )

            # Stop if we have enough filtered results
            if len(results) >= k:
                break

        return results

    def save(self, path: Path) -> None:
        """
        Save vector store to disk.

        Saves two files:
        - {path}.index: FAISS index (binary)
        - {path}.metadata.json: Metadata (JSON)

        Args:
            path: Base path for saving (without extension)

        Example:
            >>> store.save(Path(".clauxton/vectors/kb"))
            # Creates:
            # - .clauxton/vectors/kb.index
            # - .clauxton/vectors/kb.metadata.json
        """
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        index_path = str(path) + ".index"
        faiss.write_index(self.index, index_path)

        # Save metadata as JSON
        metadata_path = str(path) + ".metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: Path, dimension: int = 384) -> "VectorStore":
        """
        Load vector store from disk.

        Args:
            path: Base path (without extension)
            dimension: Expected embedding dimension

        Returns:
            Loaded VectorStore instance

        Raises:
            FileNotFoundError: If index or metadata file is missing
            ValueError: If loaded index dimension doesn't match

        Example:
            >>> store = VectorStore.load(Path(".clauxton/vectors/kb"))
        """
        # Load FAISS index
        index_path = str(path) + ".index"
        if not Path(index_path).exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")

        index = faiss.read_index(index_path)

        # Validate dimension
        if index.d != dimension:
            raise ValueError(
                f"Index dimension mismatch: expected {dimension}, got {index.d}"
            )

        # Load metadata
        metadata_path = str(path) + ".metadata.json"
        if not Path(metadata_path).exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Create instance
        store = cls(dimension=dimension)
        store.index = index
        store.metadata = metadata

        return store

    def clear(self) -> None:
        """
        Clear all vectors and metadata.

        Example:
            >>> store.clear()
            >>> store.size()
            0
        """
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []

    def size(self) -> int:
        """
        Get number of vectors in the store.

        Returns:
            Number of stored vectors

        Example:
            >>> store.size()
            100
        """
        return int(self.index.ntotal)

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Normalize embeddings to unit vectors.

        Args:
            embeddings: numpy array of shape (n, dimension)

        Returns:
            Normalized array (each row has L2 norm = 1)
        """
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        # Avoid division by zero
        norms = np.where(norms == 0, 1, norms)
        normalized: np.ndarray = embeddings / norms
        return normalized

    def __len__(self) -> int:
        """Get number of vectors (supports len(store))."""
        return self.size()

    def __repr__(self) -> str:
        """String representation."""
        return f"VectorStore(dimension={self.dimension}, size={self.size()})"
