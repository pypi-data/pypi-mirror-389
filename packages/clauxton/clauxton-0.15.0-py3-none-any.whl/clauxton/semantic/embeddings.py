"""
Local embedding generation using sentence-transformers.

This module provides text embedding capabilities using local models,
with no external API calls. All processing happens on the user's machine.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

import numpy as np

# Optional import - graceful degradation if not installed
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    if TYPE_CHECKING:
        from sentence_transformers import SentenceTransformer


class UserConsentError(Exception):
    """Raised when user declines model download."""

    pass


class EmbeddingEngine:
    """
    Generate embeddings for text using local models.

    Model: all-MiniLM-L6-v2
    - Dimensions: 384
    - Size: ~90MB
    - Speed: ~500 sentences/second on CPU
    - Quality: Good for semantic similarity

    Features:
    - Lazy loading: Model loaded only on first use
    - User consent: Explicit approval for model download
    - CPU-first: Optimized for systems without GPU
    - Caching: Model cached locally to avoid re-downloads
    - Batch processing: Efficient encoding of multiple texts

    Example:
        >>> engine = EmbeddingEngine()
        >>> embeddings = engine.encode(["Hello world", "Good morning"])
        >>> embeddings.shape
        (2, 384)
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"
    DEFAULT_CACHE_DIR = Path.home() / ".cache" / "clauxton" / "models"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        cache_dir: Optional[Path] = None,
        device: str = "cpu",
    ):
        """
        Initialize embedding engine.

        Args:
            model_name: HuggingFace model identifier
            cache_dir: Where to cache the model (~/.cache/clauxton/models/)
            device: "cpu" or "cuda" for GPU

        Note: First run downloads ~90MB model (with user consent)
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for semantic search. "
                "Install with: pip install clauxton[semantic]"
            )

        self.model_name = model_name
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.device = device
        self._model: Optional["SentenceTransformer"] = None

    @property
    def model(self) -> "SentenceTransformer":
        """
        Lazy-load model on first use.

        Returns:
            Loaded SentenceTransformer model

        Raises:
            UserConsentError: If user declines model download
        """
        if self._model is None:
            self._model = self._load_model()
        return self._model

    def _load_model(self) -> "SentenceTransformer":
        """
        Load model with user consent.

        Returns:
            Loaded SentenceTransformer model

        Raises:
            UserConsentError: If user declines model download
        """
        # Check if model is already cached
        if not self._is_model_cached():
            # Prompt user for consent
            if not self._get_user_consent():
                raise UserConsentError(
                    f"Semantic search requires downloading a ~90MB model ({self.model_name}). "
                    "Set CLAUXTON_AUTO_DOWNLOAD=1 environment variable or use --allow-download flag"
                )

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load model
        return SentenceTransformer(
            self.model_name, cache_folder=str(self.cache_dir), device=self.device
        )

    def _is_model_cached(self) -> bool:
        """
        Check if model is already downloaded.

        Returns:
            True if model exists in cache, False otherwise
        """
        # SentenceTransformer uses a specific directory structure
        # Format: cache_dir/sentence_transformers_{model_name_sanitized}/
        model_path = self.cache_dir / f"sentence_transformers_{self.model_name}"

        # Alternative: Check for any model files
        if not model_path.exists():
            # Also check the parent cache directory for any downloaded models
            if not self.cache_dir.exists():
                return False

            # Search for model files
            for item in self.cache_dir.iterdir():
                if item.is_dir() and self.model_name.replace("/", "_") in item.name:
                    return True
            return False

        return True

    def _get_user_consent(self) -> bool:
        """
        Get user consent for model download.

        Checks (in order):
        1. CLAUXTON_AUTO_DOWNLOAD environment variable
        2. CLAUXTON_SEMANTIC_ENABLED environment variable
        3. Interactive prompt (if TTY available)

        Returns:
            True if user consents, False otherwise
        """
        # Check auto-download flag
        if os.environ.get("CLAUXTON_AUTO_DOWNLOAD", "").lower() in ("1", "true", "yes"):
            return True

        # Check semantic enabled flag
        if os.environ.get("CLAUXTON_SEMANTIC_ENABLED", "").lower() in (
            "1",
            "true",
            "yes",
        ):
            return True

        # Interactive prompt (only if TTY available)
        if os.isatty(0):  # stdin is a terminal
            try:
                response = input(
                    f"\nSemantic search requires downloading a ~90MB model ({self.model_name}).\n"
                    "This is a one-time download and will be cached locally.\n"
                    "Download now? [Y/n]: "
                )
                return response.strip().lower() in ("", "y", "yes")
            except (EOFError, KeyboardInterrupt):
                return False

        # Non-interactive mode: deny by default
        return False

    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize_embeddings: bool = False,
    ) -> np.ndarray:
        """
        Generate embeddings for texts.

        Args:
            texts: List of text strings to embed
            batch_size: Process in batches for efficiency
            show_progress: Show progress bar (useful for large batches)
            normalize_embeddings: Normalize to unit vectors (useful for cosine similarity)

        Returns:
            numpy array of shape (len(texts), 384)

        Example:
            >>> engine = EmbeddingEngine()
            >>> texts = ["Hello", "World"]
            >>> embeddings = engine.encode(texts)
            >>> embeddings.shape
            (2, 384)
        """
        if not texts:
            # Return empty array with correct shape
            return np.array([]).reshape(0, 384)

        result: np.ndarray = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=normalize_embeddings,
        )
        return result

    def encode_single(self, text: str, normalize: bool = False) -> np.ndarray:
        """
        Convenience method for encoding a single text.

        Args:
            text: Text string to embed
            normalize: Normalize to unit vector

        Returns:
            numpy array of shape (384,)

        Example:
            >>> engine = EmbeddingEngine()
            >>> embedding = engine.encode_single("Hello world")
            >>> embedding.shape
            (384,)
        """
        result = self.encode([text], normalize_embeddings=normalize)
        single_result: np.ndarray = result[0]
        return single_result

    def get_dimension(self) -> int:
        """
        Get embedding dimension for the current model.

        Returns:
            Embedding dimension (384 for all-MiniLM-L6-v2)
        """
        # For all-MiniLM-L6-v2, dimension is always 384
        # We could also query the model, but that would trigger loading
        if self.model_name == self.DEFAULT_MODEL:
            return 384

        # For other models, we need to load to get dimension
        dimension = self.model.get_sentence_embedding_dimension()
        return dimension if dimension is not None else 384
