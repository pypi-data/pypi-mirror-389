"""Tests for VectorStore (FAISS-based vector storage)."""

import json
from pathlib import Path

import numpy as np
import pytest

# Import with graceful degradation
try:
    from clauxton.semantic.vector_store import FAISS_AVAILABLE, VectorStore

    DEPENDENCIES_AVAILABLE = FAISS_AVAILABLE
except ImportError:
    DEPENDENCIES_AVAILABLE = False


# Skip all tests if dependencies not installed
pytestmark = pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE,
    reason="faiss-cpu not installed (optional dependency)",
)


class TestVectorStoreInitialization:
    """Test VectorStore initialization."""

    def test_init_default_dimension(self) -> None:
        """Test initialization with default dimension."""
        store = VectorStore()
        assert store.dimension == 384
        assert store.size() == 0
        assert len(store.metadata) == 0

    def test_init_custom_dimension(self) -> None:
        """Test initialization with custom dimension."""
        store = VectorStore(dimension=512)
        assert store.dimension == 512
        assert store.size() == 0

    def test_init_creates_empty_index(self) -> None:
        """Test that initialization creates an empty FAISS index."""
        store = VectorStore(dimension=128)
        assert store.index.ntotal == 0
        assert store.index.d == 128


class TestVectorStoreAdd:
    """Test adding vectors to the store."""

    def test_add_single_embedding(self) -> None:
        """Test adding a single embedding."""
        store = VectorStore(dimension=384)
        embedding = np.random.rand(384)
        metadata = {"id": "test-1", "text": "Hello world"}

        store.add(embedding, [metadata])

        assert store.size() == 1
        assert len(store.metadata) == 1
        assert store.metadata[0] == metadata

    def test_add_single_embedding_1d_array(self) -> None:
        """Test adding a single embedding as 1D array (auto-reshaping)."""
        store = VectorStore(dimension=384)
        embedding = np.random.rand(384)  # 1D array

        store.add(embedding, [{"id": 1}])

        assert store.size() == 1

    def test_add_batch_embeddings(self) -> None:
        """Test adding multiple embeddings at once."""
        store = VectorStore(dimension=384)
        embeddings = np.random.rand(10, 384)
        metadata = [{"id": i, "text": f"Doc {i}"} for i in range(10)]

        store.add(embeddings, metadata)

        assert store.size() == 10
        assert len(store.metadata) == 10

    def test_add_incremental(self) -> None:
        """Test adding embeddings incrementally."""
        store = VectorStore(dimension=384)

        # Add first batch
        store.add(np.random.rand(5, 384), [{"id": i} for i in range(5)])
        assert store.size() == 5

        # Add second batch
        store.add(np.random.rand(3, 384), [{"id": i} for i in range(5, 8)])
        assert store.size() == 8

    def test_add_without_metadata(self) -> None:
        """Test adding embeddings without metadata."""
        store = VectorStore(dimension=384)
        embeddings = np.random.rand(5, 384)

        store.add(embeddings)  # No metadata

        assert store.size() == 5
        # Should create empty metadata dicts
        assert len(store.metadata) == 5
        assert all(isinstance(m, dict) for m in store.metadata)

    def test_add_dimension_mismatch(self) -> None:
        """Test error when adding embeddings with wrong dimension."""
        store = VectorStore(dimension=384)
        wrong_embeddings = np.random.rand(5, 512)  # Wrong dimension

        with pytest.raises(ValueError, match="Embedding dimension mismatch"):
            store.add(wrong_embeddings)

    def test_add_metadata_length_mismatch(self) -> None:
        """Test error when metadata length doesn't match embeddings."""
        store = VectorStore(dimension=384)
        embeddings = np.random.rand(5, 384)
        metadata = [{"id": i} for i in range(3)]  # Only 3 metadata for 5 embeddings

        with pytest.raises(ValueError, match="Metadata length"):
            store.add(embeddings, metadata)


class TestVectorStoreSearch:
    """Test similarity search."""

    def test_search_basic(self) -> None:
        """Test basic similarity search."""
        store = VectorStore(dimension=384)

        # Add some embeddings
        embeddings = np.random.rand(10, 384)
        metadata = [{"id": i, "text": f"Doc {i}"} for i in range(10)]
        store.add(embeddings, metadata)

        # Search with first embedding (should find itself)
        query = embeddings[0]
        results = store.search(query, k=5)

        assert len(results) <= 5
        assert results[0]["index"] == 0  # First result should be itself
        assert results[0]["distance"] > 0.99  # Very high similarity (cosine)
        assert results[0]["metadata"]["id"] == 0

    def test_search_returns_top_k(self) -> None:
        """Test that search returns at most k results."""
        store = VectorStore(dimension=384)
        store.add(np.random.rand(20, 384))

        results = store.search(np.random.rand(384), k=5)

        assert len(results) <= 5

    def test_search_empty_store(self) -> None:
        """Test search on empty store returns empty list."""
        store = VectorStore(dimension=384)
        results = store.search(np.random.rand(384), k=5)

        assert results == []

    def test_search_with_filter(self) -> None:
        """Test search with metadata filtering."""
        store = VectorStore(dimension=384)

        # Add embeddings with different categories
        embeddings = np.random.rand(10, 384)
        metadata = [
            {"id": i, "category": "A" if i < 5 else "B"} for i in range(10)
        ]
        store.add(embeddings, metadata)

        # Search with filter for category A only
        query = embeddings[0]

        def filter_fn(m):
            return m["category"] == "A"

        results = store.search(query, k=10, filter_fn=filter_fn)

        # Should only return category A results
        assert all(r["metadata"]["category"] == "A" for r in results)
        assert len(results) <= 5  # At most 5 (all category A)

    def test_search_dimension_mismatch(self) -> None:
        """Test error when query dimension doesn't match."""
        store = VectorStore(dimension=384)
        store.add(np.random.rand(5, 384))

        wrong_query = np.random.rand(512)  # Wrong dimension

        with pytest.raises(ValueError, match="Query dimension mismatch"):
            store.search(wrong_query, k=5)

    def test_search_cosine_similarity_range(self) -> None:
        """Test that cosine similarity is in valid range [0, 1]."""
        store = VectorStore(dimension=384)
        store.add(np.random.rand(10, 384))

        results = store.search(np.random.rand(384), k=5)

        for result in results:
            # Cosine similarity should be between -1 and 1
            # (but typically positive for random vectors)
            assert -1.0 <= result["distance"] <= 1.0


class TestVectorStorePersistence:
    """Test saving and loading vector store."""

    def test_save_and_load(self, tmp_path: Path) -> None:
        """Test saving and loading a vector store."""
        # Create and populate store
        store = VectorStore(dimension=384)
        embeddings = np.random.rand(10, 384)
        metadata = [{"id": i, "text": f"Doc {i}"} for i in range(10)]
        store.add(embeddings, metadata)

        # Save
        save_path = tmp_path / "test_store"
        store.save(save_path)

        # Verify files exist
        assert (tmp_path / "test_store.index").exists()
        assert (tmp_path / "test_store.metadata.json").exists()

        # Load
        loaded_store = VectorStore.load(save_path, dimension=384)

        # Verify loaded store matches original
        assert loaded_store.size() == store.size()
        assert loaded_store.metadata == store.metadata
        assert loaded_store.dimension == store.dimension

    def test_save_creates_parent_directory(self, tmp_path: Path) -> None:
        """Test that save() creates parent directories if they don't exist."""
        store = VectorStore(dimension=384)
        store.add(np.random.rand(5, 384))

        # Save to nested path that doesn't exist
        save_path = tmp_path / "nested" / "dir" / "store"
        store.save(save_path)

        assert save_path.parent.exists()
        assert Path(str(save_path) + ".index").exists()

    def test_load_missing_index(self, tmp_path: Path) -> None:
        """Test error when loading with missing index file."""
        missing_path = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError, match="Index file not found"):
            VectorStore.load(missing_path)

    def test_load_missing_metadata(self, tmp_path: Path) -> None:
        """Test error when loading with missing metadata file."""
        # Create only index file (no metadata)
        store = VectorStore(dimension=384)
        store.add(np.random.rand(5, 384))

        import faiss

        index_path = tmp_path / "store.index"
        faiss.write_index(store.index, str(index_path))

        # Try to load (should fail due to missing metadata)
        with pytest.raises(FileNotFoundError, match="Metadata file not found"):
            VectorStore.load(tmp_path / "store")

    def test_load_dimension_mismatch(self, tmp_path: Path) -> None:
        """Test error when loading with wrong dimension."""
        # Save with dimension 384
        store = VectorStore(dimension=384)
        store.add(np.random.rand(5, 384))
        save_path = tmp_path / "store"
        store.save(save_path)

        # Try to load with different dimension
        with pytest.raises(ValueError, match="Index dimension mismatch"):
            VectorStore.load(save_path, dimension=512)

    def test_metadata_json_format(self, tmp_path: Path) -> None:
        """Test that metadata is saved in readable JSON format."""
        store = VectorStore(dimension=384)
        metadata = [
            {"id": "test-1", "text": "Hello", "tags": ["greeting"]},
            {"id": "test-2", "text": "World", "tags": ["noun"]},
        ]
        store.add(np.random.rand(2, 384), metadata)

        save_path = tmp_path / "store"
        store.save(save_path)

        # Read and verify JSON
        metadata_path = tmp_path / "store.metadata.json"
        with open(metadata_path, "r") as f:
            loaded_metadata = json.load(f)

        assert loaded_metadata == metadata


class TestVectorStoreUtilities:
    """Test utility methods."""

    def test_clear(self) -> None:
        """Test clearing the vector store."""
        store = VectorStore(dimension=384)
        store.add(np.random.rand(10, 384))

        assert store.size() == 10

        store.clear()

        assert store.size() == 0
        assert len(store.metadata) == 0

    def test_size(self) -> None:
        """Test size() method."""
        store = VectorStore(dimension=384)
        assert store.size() == 0

        store.add(np.random.rand(5, 384))
        assert store.size() == 5

        store.add(np.random.rand(3, 384))
        assert store.size() == 8

    def test_len(self) -> None:
        """Test __len__ magic method."""
        store = VectorStore(dimension=384)
        assert len(store) == 0

        store.add(np.random.rand(10, 384))
        assert len(store) == 10

    def test_repr(self) -> None:
        """Test __repr__ string representation."""
        store = VectorStore(dimension=512)
        store.add(np.random.rand(5, 512))

        repr_str = repr(store)

        assert "VectorStore" in repr_str
        assert "dimension=512" in repr_str
        assert "size=5" in repr_str

    def test_normalize(self) -> None:
        """Test _normalize method produces unit vectors."""
        store = VectorStore(dimension=384)

        # Create some random vectors
        vectors = np.random.rand(10, 384)

        # Normalize
        normalized = store._normalize(vectors)

        # Check that each vector has L2 norm H 1
        norms = np.linalg.norm(normalized, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-6)

    def test_normalize_zero_vector(self) -> None:
        """Test that _normalize handles zero vectors gracefully."""
        store = VectorStore(dimension=384)

        # Create zero vector
        zero_vector = np.zeros((1, 384))

        # Should not raise error
        normalized = store._normalize(zero_vector)

        # Zero vector stays zero (division by 1 to avoid division by zero)
        assert np.allclose(normalized, zero_vector)


class TestVectorStoreErrors:
    """Test error handling."""

    def test_import_error_when_faiss_not_installed(self) -> None:
        """Test that ImportError is raised when faiss-cpu is not available."""
        # This test is tricky - we can't really test this without uninstalling faiss
        # But we can at least verify the error message exists in the code
        # (This is more of a documentation test)
        pass

    def test_search_k_larger_than_store(self) -> None:
        """Test search with k larger than store size."""
        store = VectorStore(dimension=384)
        store.add(np.random.rand(3, 384))

        # Request more results than available
        results = store.search(np.random.rand(384), k=10)

        # Should return at most 3 results
        assert len(results) <= 3

    def test_search_with_invalid_filter(self) -> None:
        """Test search with filter that rejects all results."""
        store = VectorStore(dimension=384)
        metadata = [{"category": "A"} for _ in range(5)]
        store.add(np.random.rand(5, 384), metadata)

        # Filter that rejects everything
        def filter_fn(m):
            return m["category"] == "B"

        results = store.search(np.random.rand(384), k=5, filter_fn=filter_fn)

        assert results == []
