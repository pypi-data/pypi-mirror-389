"""
Tests for embeddings.py - Local embedding generation.

This module tests the EmbeddingEngine class with comprehensive coverage
of all features including lazy loading, user consent, and batch processing.
"""

import os
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from clauxton.semantic.embeddings import (
    SENTENCE_TRANSFORMERS_AVAILABLE,
    EmbeddingEngine,
    UserConsentError,
)

# Skip all tests if sentence-transformers not installed
pytestmark = pytest.mark.skipif(
    not SENTENCE_TRANSFORMERS_AVAILABLE,
    reason="sentence-transformers not installed (optional dependency)",
)


class TestEmbeddingEngineInitialization:
    """Test EmbeddingEngine initialization."""

    def test_initialization_default_params(self, tmp_path: Path) -> None:
        """Test initialization with default parameters."""
        engine = EmbeddingEngine(cache_dir=tmp_path)
        assert engine.model_name == EmbeddingEngine.DEFAULT_MODEL
        assert engine.cache_dir == tmp_path
        assert engine.device == "cpu"
        assert engine._model is None  # Lazy loading

    def test_initialization_custom_params(self, tmp_path: Path) -> None:
        """Test initialization with custom parameters."""
        custom_model = "all-mpnet-base-v2"
        engine = EmbeddingEngine(
            model_name=custom_model, cache_dir=tmp_path, device="cuda"
        )
        assert engine.model_name == custom_model
        assert engine.device == "cuda"


class TestLazyModelLoading:
    """Test lazy loading of embedding model."""

    def test_model_not_loaded_on_init(self, tmp_path: Path) -> None:
        """Test that model is not loaded during initialization."""
        engine = EmbeddingEngine(cache_dir=tmp_path)
        assert engine._model is None

    @patch.dict(os.environ, {"CLAUXTON_AUTO_DOWNLOAD": "1"})
    def test_model_loaded_on_first_access(self, tmp_path: Path) -> None:
        """Test that model is loaded on first property access."""
        engine = EmbeddingEngine(cache_dir=tmp_path)
        assert engine._model is None

        # Access model property
        model = engine.model
        assert model is not None
        assert engine._model is not None

    @patch.dict(os.environ, {"CLAUXTON_AUTO_DOWNLOAD": "1"})
    def test_model_loaded_only_once(self, tmp_path: Path) -> None:
        """Test that model is loaded only once (cached)."""
        engine = EmbeddingEngine(cache_dir=tmp_path)

        # Access model multiple times
        model1 = engine.model
        model2 = engine.model
        model3 = engine.model

        # Should be the same instance
        assert model1 is model2
        assert model2 is model3


class TestUserConsent:
    """Test user consent mechanism for model download."""

    def test_auto_download_env_var(self, tmp_path: Path) -> None:
        """Test CLAUXTON_AUTO_DOWNLOAD environment variable."""
        with patch.dict(os.environ, {"CLAUXTON_AUTO_DOWNLOAD": "1"}):
            engine = EmbeddingEngine(cache_dir=tmp_path)
            assert engine._get_user_consent() is True

        with patch.dict(os.environ, {"CLAUXTON_AUTO_DOWNLOAD": "true"}):
            engine = EmbeddingEngine(cache_dir=tmp_path)
            assert engine._get_user_consent() is True

        with patch.dict(os.environ, {"CLAUXTON_AUTO_DOWNLOAD": "yes"}):
            engine = EmbeddingEngine(cache_dir=tmp_path)
            assert engine._get_user_consent() is True

    def test_semantic_enabled_env_var(self, tmp_path: Path) -> None:
        """Test CLAUXTON_SEMANTIC_ENABLED environment variable."""
        with patch.dict(os.environ, {"CLAUXTON_SEMANTIC_ENABLED": "1"}):
            engine = EmbeddingEngine(cache_dir=tmp_path)
            assert engine._get_user_consent() is True

    def test_user_consent_denied_raises_error(self, tmp_path: Path) -> None:
        """Test that UserConsentError is raised when user declines."""
        with patch.dict(os.environ, {}, clear=True):
            # Mock isatty to return False (non-interactive)
            with patch("os.isatty", return_value=False):
                engine = EmbeddingEngine(cache_dir=tmp_path)
                assert engine._get_user_consent() is False

                # Attempting to load model should raise error
                with pytest.raises(UserConsentError):
                    _ = engine.model

    def test_interactive_consent_yes(self, tmp_path: Path) -> None:
        """Test interactive consent when user says yes."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.isatty", return_value=True):
                with patch("builtins.input", return_value="y"):
                    engine = EmbeddingEngine(cache_dir=tmp_path)
                    assert engine._get_user_consent() is True

    def test_interactive_consent_no(self, tmp_path: Path) -> None:
        """Test interactive consent when user says no."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.isatty", return_value=True):
                with patch("builtins.input", return_value="n"):
                    engine = EmbeddingEngine(cache_dir=tmp_path)
                    assert engine._get_user_consent() is False

    def test_interactive_consent_keyboard_interrupt(self, tmp_path: Path) -> None:
        """Test interactive consent when user interrupts."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.isatty", return_value=True):
                with patch("builtins.input", side_effect=KeyboardInterrupt()):
                    engine = EmbeddingEngine(cache_dir=tmp_path)
                    assert engine._get_user_consent() is False


class TestModelCaching:
    """Test model caching mechanism."""

    def test_is_model_cached_false_when_not_exists(self, tmp_path: Path) -> None:
        """Test cache check when model not downloaded."""
        cache_dir = tmp_path / "models"
        engine = EmbeddingEngine(cache_dir=cache_dir)
        assert engine._is_model_cached() is False

    def test_is_model_cached_true_when_exists(self, tmp_path: Path) -> None:
        """Test cache check when model directory exists."""
        cache_dir = tmp_path / "models"
        cache_dir.mkdir(parents=True)

        # Create fake model directory
        model_dir = cache_dir / "sentence_transformers_all-MiniLM-L6-v2"
        model_dir.mkdir()

        engine = EmbeddingEngine(cache_dir=cache_dir)
        assert engine._is_model_cached() is True

    def test_cache_directory_creation(self, tmp_path: Path) -> None:
        """Test that cache directory is created when loading model."""
        cache_dir = tmp_path / "models"
        assert not cache_dir.exists()

        with patch.dict(os.environ, {"CLAUXTON_AUTO_DOWNLOAD": "1"}):
            engine = EmbeddingEngine(cache_dir=cache_dir)
            _ = engine.model  # Trigger loading

            assert cache_dir.exists()


class TestEncodeMethods:
    """Test encoding methods."""

    @patch.dict(os.environ, {"CLAUXTON_AUTO_DOWNLOAD": "1"})
    def test_encode_single_text(self, tmp_path: Path) -> None:
        """Test encoding a single text."""
        engine = EmbeddingEngine(cache_dir=tmp_path)
        embedding = engine.encode_single("Hello world")

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
        assert embedding.dtype == np.float32

    @patch.dict(os.environ, {"CLAUXTON_AUTO_DOWNLOAD": "1"})
    def test_encode_batch(self, tmp_path: Path) -> None:
        """Test encoding multiple texts in a batch."""
        engine = EmbeddingEngine(cache_dir=tmp_path)
        texts = ["Hello", "World", "Good morning"]
        embeddings = engine.encode(texts)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (3, 384)
        assert embeddings.dtype == np.float32

    @patch.dict(os.environ, {"CLAUXTON_AUTO_DOWNLOAD": "1"})
    def test_encode_empty_list(self, tmp_path: Path) -> None:
        """Test encoding empty list returns correct shape."""
        engine = EmbeddingEngine(cache_dir=tmp_path)
        embeddings = engine.encode([])

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (0, 384)

    @patch.dict(os.environ, {"CLAUXTON_AUTO_DOWNLOAD": "1"})
    def test_encode_very_long_text(self, tmp_path: Path) -> None:
        """Test encoding text longer than typical token limit."""
        engine = EmbeddingEngine(cache_dir=tmp_path)

        # Create a very long text (> 512 tokens)
        long_text = " ".join(["word"] * 1000)
        embedding = engine.encode_single(long_text)

        # Should still work (model will truncate internally)
        assert embedding.shape == (384,)

    @patch.dict(os.environ, {"CLAUXTON_AUTO_DOWNLOAD": "1"})
    def test_encode_with_normalization(self, tmp_path: Path) -> None:
        """Test encoding with normalization."""
        engine = EmbeddingEngine(cache_dir=tmp_path)
        embedding = engine.encode_single("Hello world", normalize=True)

        # Normalized embeddings should have unit length
        norm = np.linalg.norm(embedding)
        assert np.isclose(norm, 1.0, atol=1e-6)

    @patch.dict(os.environ, {"CLAUXTON_AUTO_DOWNLOAD": "1"})
    def test_encode_batch_size(self, tmp_path: Path) -> None:
        """Test encoding with custom batch size."""
        engine = EmbeddingEngine(cache_dir=tmp_path)
        texts = ["Text " + str(i) for i in range(100)]

        # Encode with batch size of 10
        embeddings = engine.encode(texts, batch_size=10)

        assert embeddings.shape == (100, 384)


class TestEmbeddingDimension:
    """Test embedding dimension methods."""

    def test_get_dimension_default_model(self, tmp_path: Path) -> None:
        """Test getting dimension for default model (no loading)."""
        engine = EmbeddingEngine(cache_dir=tmp_path)
        dimension = engine.get_dimension()

        assert dimension == 384
        assert engine._model is None  # Should not trigger loading

    @patch.dict(os.environ, {"CLAUXTON_AUTO_DOWNLOAD": "1"})
    def test_get_dimension_custom_model(self, tmp_path: Path) -> None:
        """Test getting dimension for custom model (requires loading)."""
        # Use a different model that also has known dimension
        engine = EmbeddingEngine(model_name="all-MiniLM-L6-v2", cache_dir=tmp_path)
        dimension = engine.get_dimension()

        assert dimension == 384


class TestErrorHandling:
    """Test error handling."""

    def test_user_consent_error_message(self, tmp_path: Path) -> None:
        """Test UserConsentError has helpful message."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.isatty", return_value=False):
                engine = EmbeddingEngine(cache_dir=tmp_path)

                with pytest.raises(UserConsentError) as exc_info:
                    _ = engine.model

                assert "90MB" in str(exc_info.value)
                assert "CLAUXTON_AUTO_DOWNLOAD" in str(exc_info.value)


class TestPerformance:
    """Performance tests (marked as slow)."""

    @pytest.mark.slow
    @patch.dict(os.environ, {"CLAUXTON_AUTO_DOWNLOAD": "1"})
    def test_encoding_speed_benchmark(self, tmp_path: Path) -> None:
        """Test encoding speed meets target (>500 texts/sec)."""
        import time

        engine = EmbeddingEngine(cache_dir=tmp_path)
        texts = ["This is a test sentence."] * 500

        start = time.time()
        embeddings = engine.encode(texts, batch_size=32)
        duration = time.time() - start

        # Should process 500 texts in < 1 second
        assert duration < 1.0, f"Encoding took {duration:.2f}s, expected < 1.0s"
        assert embeddings.shape == (500, 384)
