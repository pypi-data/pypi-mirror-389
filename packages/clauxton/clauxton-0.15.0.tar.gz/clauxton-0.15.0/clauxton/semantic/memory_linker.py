"""
Memory relationship detection for Clauxton v0.15.0.

This module provides automatic relationship detection between memories using:
- Content similarity (TF-IDF cosine similarity)
- Tag similarity (Jaccard index)
- Category matching
- Temporal proximity
- Weighted scoring for relationship detection
- Merge candidate detection for duplicate memories

Key Features:
- Multi-signal relationship detection with weighted scoring
- Automatic linking of related memories
- Duplicate/similar memory detection for merging
- Fallback support when scikit-learn is unavailable
- Performance optimized for large memory sets

Example:
    >>> from pathlib import Path
    >>> from clauxton.semantic.memory_linker import MemoryLinker
    >>> linker = MemoryLinker(Path("."))
    >>> # Find relationships for a specific memory
    >>> relationships = linker.find_relationships(entry, threshold=0.3)
    >>> # Auto-link all memories
    >>> links_created = linker.auto_link_all(threshold=0.3)
    >>> # Find merge candidates
    >>> candidates = linker.suggest_merge_candidates(threshold=0.8)
"""

from pathlib import Path
from typing import List, Optional, Tuple

from clauxton.core.memory import Memory, MemoryEntry

# Optional scikit-learn for TF-IDF
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    TfidfVectorizer = None
    cosine_similarity = None


class MemoryLinker:
    """
    Auto-detect relationships between memories using multiple similarity signals.

    The MemoryLinker uses a weighted scoring system combining:
    1. Content similarity (40%): TF-IDF cosine similarity
    2. Tag similarity (30%): Jaccard index (shared tags / total tags)
    3. Category match (20%): Binary (same category = 0.2, different = 0.0)
    4. Temporal proximity (10%): Decay function (1.0 if within 7 days, else 0.0)

    Attributes:
        memory: Memory system instance
        project_root: Project root directory
    """

    # Similarity weights
    CONTENT_WEIGHT = 0.4
    TAG_WEIGHT = 0.3
    CATEGORY_WEIGHT = 0.2
    TEMPORAL_WEIGHT = 0.1

    # Thresholds
    DEFAULT_RELATIONSHIP_THRESHOLD = 0.3
    DEFAULT_MERGE_THRESHOLD = 0.8
    TEMPORAL_WINDOW_DAYS = 7

    def __init__(self, project_root: Path | str) -> None:
        """
        Initialize MemoryLinker.

        Args:
            project_root: Project root directory (Path or str)

        Example:
            >>> linker = MemoryLinker(Path("."))
            >>> linker = MemoryLinker(".")  # str also works
        """
        self.project_root: Path = (
            Path(project_root) if isinstance(project_root, str) else project_root
        )
        self.memory = Memory(self.project_root)

    def find_relationships(
        self,
        entry: MemoryEntry,
        existing_memories: Optional[List[MemoryEntry]] = None,
        threshold: float = DEFAULT_RELATIONSHIP_THRESHOLD,
    ) -> List[str]:
        """
        Find related memories using multi-signal similarity scoring.

        Combines multiple similarity signals with weighted scoring:
        - Content similarity (40%): TF-IDF cosine similarity
        - Tag similarity (30%): Jaccard index
        - Category match (20%): Binary match
        - Temporal proximity (10%): Time-based decay

        Args:
            entry: MemoryEntry to find relationships for
            existing_memories: Optional list of memories to search in (defaults to all)
            threshold: Minimum similarity score (0.0-1.0, default: 0.3)

        Returns:
            List of related memory IDs (sorted by similarity, highest first)

        Example:
            >>> entry = memory.get("MEM-20260127-001")
            >>> related_ids = linker.find_relationships(entry, threshold=0.3)
            >>> related_ids
            ['MEM-20260127-002', 'MEM-20260126-003']
        """
        if existing_memories is None:
            existing_memories = self.memory.list_all()

        # Filter out the entry itself
        candidates = [m for m in existing_memories if m.id != entry.id]
        if not candidates:
            return []

        # Calculate similarity scores for all candidates
        scores: List[Tuple[str, float]] = []
        for candidate in candidates:
            score = self._calculate_similarity(entry, candidate)
            if score >= threshold:
                scores.append((candidate.id, score))

        # Sort by similarity (descending)
        scores.sort(key=lambda x: x[1], reverse=True)

        return [memory_id for memory_id, _ in scores]

    def auto_link_all(self, threshold: float = DEFAULT_RELATIONSHIP_THRESHOLD) -> int:
        """
        Auto-link all memories in the system.

        Finds relationships between all memories and updates their related_to fields.
        Existing relationships are preserved.

        Args:
            threshold: Minimum similarity score for linking (0.0-1.0, default: 0.3)

        Returns:
            Number of new relationships created

        Example:
            >>> links_created = linker.auto_link_all(threshold=0.3)
            >>> links_created
            42
        """
        all_memories = self.memory.list_all()
        links_created = 0

        for entry in all_memories:
            # Find related memories
            related_ids = self.find_relationships(
                entry, existing_memories=all_memories, threshold=threshold
            )

            # Get existing relationships
            existing_related = set(entry.related_to or [])

            # Add new relationships (avoid duplicates)
            new_related = [rid for rid in related_ids if rid not in existing_related]

            if new_related:
                # Update entry with new relationships
                updated_related = list(existing_related) + new_related
                self.memory.update(entry.id, related_to=updated_related)
                links_created += len(new_related)

        return links_created

    def suggest_merge_candidates(
        self, threshold: float = DEFAULT_MERGE_THRESHOLD
    ) -> List[Tuple[str, str, float]]:
        """
        Find duplicate/similar memories that should be merged.

        Uses high similarity threshold to detect near-duplicates:
        - Title similarity (Levenshtein-based)
        - Content similarity (TF-IDF)
        - Same type and category
        - High overall similarity score (>0.8)

        Args:
            threshold: Minimum similarity for merge candidates (0.0-1.0, default: 0.8)

        Returns:
            List of (memory_id1, memory_id2, similarity_score) tuples

        Example:
            >>> candidates = linker.suggest_merge_candidates(threshold=0.8)
            >>> for id1, id2, score in candidates:
            ...     print(f"{id1} <-> {id2}: {score:.2f}")
            MEM-20260127-001 <-> MEM-20260127-003: 0.92
        """
        all_memories = self.memory.list_all()
        candidates: List[Tuple[str, str, float]] = []

        # Compare all pairs
        for i, mem1 in enumerate(all_memories):
            for mem2 in all_memories[i + 1:]:
                # Calculate merge similarity
                score = self._merge_similarity(mem1, mem2)

                if score >= threshold:
                    candidates.append((mem1.id, mem2.id, score))

        # Sort by similarity (descending)
        candidates.sort(key=lambda x: x[2], reverse=True)

        return candidates

    def _calculate_similarity(self, mem1: MemoryEntry, mem2: MemoryEntry) -> float:
        """
        Calculate overall similarity between two memories.

        Uses weighted scoring:
        - Content similarity (40%)
        - Tag similarity (30%)
        - Category match (20%)
        - Temporal proximity (10%)

        Args:
            mem1: First memory
            mem2: Second memory

        Returns:
            Similarity score (0.0-1.0)
        """
        # Content similarity
        content_sim = self._content_similarity(mem1, mem2)

        # Tag similarity
        tag_sim = self._tag_similarity(mem1, mem2)

        # Category match
        category_sim = 1.0 if mem1.category == mem2.category else 0.0

        # Temporal proximity
        temporal_sim = self._temporal_similarity(mem1, mem2)

        # Weighted sum
        total_score = (
            content_sim * self.CONTENT_WEIGHT
            + tag_sim * self.TAG_WEIGHT
            + category_sim * self.CATEGORY_WEIGHT
            + temporal_sim * self.TEMPORAL_WEIGHT
        )

        return total_score

    def _content_similarity(self, mem1: MemoryEntry, mem2: MemoryEntry) -> float:
        """
        Calculate content similarity using TF-IDF cosine similarity.

        Falls back to simple word overlap if scikit-learn is unavailable.

        Args:
            mem1: First memory
            mem2: Second memory

        Returns:
            Similarity score (0.0-1.0)
        """
        if SKLEARN_AVAILABLE:
            try:
                # Combine title and content for richer context
                text1 = f"{mem1.title} {mem1.content}"
                text2 = f"{mem2.title} {mem2.content}"

                # Create TF-IDF vectorizer
                vectorizer = TfidfVectorizer(
                    stop_words="english",
                    lowercase=True,
                    max_features=500,
                )

                # Compute TF-IDF vectors
                tfidf_matrix = vectorizer.fit_transform([text1, text2])

                # Calculate cosine similarity
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

                return float(similarity)

            except Exception:
                # Fall back to simple word overlap
                pass

        # Fallback: Simple word overlap
        words1 = set(f"{mem1.title} {mem1.content}".lower().split())
        words2 = set(f"{mem2.title} {mem2.content}".lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _tag_similarity(self, mem1: MemoryEntry, mem2: MemoryEntry) -> float:
        """
        Calculate tag similarity using Jaccard index.

        Jaccard index = |intersection| / |union|

        Args:
            mem1: First memory
            mem2: Second memory

        Returns:
            Similarity score (0.0-1.0)
        """
        tags1 = set(mem1.tags or [])
        tags2 = set(mem2.tags or [])

        if not tags1 and not tags2:
            return 0.0

        if not tags1 or not tags2:
            return 0.0

        intersection = len(tags1 & tags2)
        union = len(tags1 | tags2)

        return intersection / union if union > 0 else 0.0

    def _temporal_similarity(self, mem1: MemoryEntry, mem2: MemoryEntry) -> float:
        """
        Calculate temporal similarity based on creation time proximity.

        Uses decay function:
        - Within 7 days: Linear decay from 1.0 to 0.0
        - Beyond 7 days: 0.0

        Args:
            mem1: First memory
            mem2: Second memory

        Returns:
            Similarity score (0.0-1.0)
        """
        time_diff = abs((mem1.created_at - mem2.created_at).days)

        if time_diff <= self.TEMPORAL_WINDOW_DAYS:
            # Linear decay within window
            return 1.0 - (time_diff / self.TEMPORAL_WINDOW_DAYS)
        else:
            return 0.0

    def _merge_similarity(self, mem1: MemoryEntry, mem2: MemoryEntry) -> float:
        """
        Calculate merge similarity for duplicate detection.

        Focuses on:
        - Title similarity (Levenshtein distance)
        - Content similarity (TF-IDF)
        - Type and category match (must be same)

        Args:
            mem1: First memory
            mem2: Second memory

        Returns:
            Merge similarity score (0.0-1.0)
        """
        # Must have same type and category
        if mem1.type != mem2.type or mem1.category != mem2.category:
            return 0.0

        # Title similarity (normalized edit distance)
        title_sim = self._normalized_levenshtein(mem1.title, mem2.title)

        # Content similarity
        content_sim = self._content_similarity(mem1, mem2)

        # Weighted average (title matters more for duplicates)
        merge_score = (title_sim * 0.6) + (content_sim * 0.4)

        return merge_score

    def _normalized_levenshtein(self, s1: str, s2: str) -> float:
        """
        Calculate normalized Levenshtein distance (similarity, not distance).

        Returns similarity score where:
        - 1.0 = identical strings
        - 0.0 = completely different strings

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity score (0.0-1.0)
        """
        if not s1 or not s2:
            return 0.0

        s1_lower = s1.lower()
        s2_lower = s2.lower()

        if s1_lower == s2_lower:
            return 1.0

        # Calculate Levenshtein distance
        m, n = len(s1_lower), len(s2_lower)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1_lower[i - 1] == s2_lower[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],      # deletion
                        dp[i][j - 1],      # insertion
                        dp[i - 1][j - 1],  # substitution
                    )

        distance = dp[m][n]
        max_len = max(m, n)

        # Normalize to similarity (1.0 = identical, 0.0 = completely different)
        similarity = 1.0 - (distance / max_len) if max_len > 0 else 0.0

        return similarity
