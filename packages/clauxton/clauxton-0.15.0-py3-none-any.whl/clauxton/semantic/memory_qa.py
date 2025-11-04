"""
Memory question-answering system for Clauxton v0.15.0.

This module provides question-answering capabilities using memory search:
- Answer questions about project architecture, patterns, and decisions
- TF-IDF based relevance ranking
- Confidence scoring for answer quality
- Source tracking for transparency

Key Features:
- Multi-memory synthesis for comprehensive answers
- Weighted confidence scoring (count, memory confidence, keyword overlap)
- Fallback when scikit-learn is unavailable
- Performance optimized (<500ms target)

Example:
    >>> from pathlib import Path
    >>> from clauxton.semantic.memory_qa import MemoryQA
    >>> qa = MemoryQA(Path("."))
    >>> answer, confidence, sources = qa.answer_question("Why did we switch to PostgreSQL?")
    >>> print(f"Answer: {answer} (confidence: {confidence:.2f})")
    Answer: We switched to PostgreSQL for better performance... (confidence: 0.85)
"""

from pathlib import Path
from typing import List, Tuple

from clauxton.core.memory import Memory, MemoryEntry

# Optional scikit-learn for TF-IDF ranking
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    TfidfVectorizer = None
    cosine_similarity = None


class MemoryQA:
    """
    Answer questions about project using memory search.

    The MemoryQA system answers questions by:
    1. Searching for relevant memories using TF-IDF
    2. Ranking results by contextual relevance to the question
    3. Generating answers from top-ranked memories
    4. Calculating confidence scores based on multiple factors

    Confidence Scoring:
    - Count score (30%): More relevant memories = higher confidence
    - Memory confidence (40%): Average confidence of auto-extracted memories
    - Keyword overlap (30%): Question-answer keyword similarity

    Attributes:
        project_root: Project root directory
        memory: Memory system instance
    """

    # Confidence weights
    COUNT_WEIGHT = 0.3
    MEMORY_CONFIDENCE_WEIGHT = 0.4
    KEYWORD_OVERLAP_WEIGHT = 0.3

    # Search parameters
    DEFAULT_TOP_K = 5
    DEFAULT_MIN_CONFIDENCE = 0.3
    SEARCH_MULTIPLIER = 2  # Search 2x top_k for better ranking

    def __init__(self, project_root: Path | str) -> None:
        """
        Initialize QA system.

        Args:
            project_root: Project root directory (Path or str)

        Example:
            >>> qa = MemoryQA(Path("."))
            >>> qa = MemoryQA(".")  # str also works
        """
        self.project_root: Path = (
            Path(project_root) if isinstance(project_root, str) else project_root
        )
        self.memory = Memory(self.project_root)

    def answer_question(
        self,
        question: str,
        top_k: int = DEFAULT_TOP_K,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    ) -> Tuple[str, float, List[str]]:
        """
        Answer a question using memory search.

        Process:
        1. Search for relevant memories (TF-IDF)
        2. Rank by contextual similarity to question
        3. Generate answer from top-k memories
        4. Calculate confidence score
        5. Return answer with sources

        Args:
            question: Question to answer
            top_k: Number of memories to consider (default: 5)
            min_confidence: Minimum confidence threshold (default: 0.3)

        Returns:
            Tuple of (answer, confidence, source_memory_ids)
            - answer: Generated answer text
            - confidence: Confidence score (0.0-1.0)
            - source_memory_ids: List of source memory IDs

        Examples:
            >>> qa = MemoryQA(Path("."))
            >>> answer, conf, sources = qa.answer_question("Why did we switch to PostgreSQL?")
            >>> print(f"Answer: {answer} (confidence: {conf:.2f})")
            Answer: We switched to PostgreSQL for better performance... (confidence: 0.85)

            >>> answer, conf, sources = qa.answer_question("What authentication method?")
            >>> sources
            ['MEM-20260127-001', 'MEM-20260127-003']
        """
        # Validate question
        if not question or not question.strip():
            return "Question cannot be empty.", 0.0, []

        # 1. Search relevant memories
        relevant_memories = self._search_relevant_memories(
            question, top_k * self.SEARCH_MULTIPLIER
        )

        if not relevant_memories:
            return "No relevant information found.", 0.0, []

        # 2. Rank by context relevance
        ranked = self._rank_by_context(question, relevant_memories)

        # Limit to top_k
        top_memories = ranked[:top_k]

        # 3. Generate answer from top memories
        answer = self._generate_answer(question, top_memories)

        # 4. Calculate confidence
        confidence = self._calculate_confidence(top_memories, question)

        # Apply minimum confidence threshold
        if confidence < min_confidence:
            return (
                f"Low confidence answer (score: {confidence:.2f}). {answer}",
                confidence,
                [mem.id for mem in top_memories],
            )

        # 5. Extract source IDs
        source_ids = [mem.id for mem in top_memories]

        return answer, confidence, source_ids

    def _search_relevant_memories(
        self, question: str, limit: int
    ) -> List[MemoryEntry]:
        """
        Search for memories relevant to the question.

        Uses Memory.search() with TF-IDF for relevance ranking.

        Args:
            question: Question text
            limit: Maximum number of results

        Returns:
            List of relevant memories (sorted by relevance)
        """
        # Use Memory system's TF-IDF search
        results = self.memory.search(query=question, limit=limit)
        return results

    def _rank_by_context(
        self, question: str, memories: List[MemoryEntry]
    ) -> List[MemoryEntry]:
        """
        Rank memories by relevance to question using TF-IDF.

        This re-ranks the search results specifically for the question context,
        using TF-IDF cosine similarity between the question and memory content.

        Args:
            question: Question text
            memories: Candidate memories from search

        Returns:
            Memories sorted by relevance (descending)
        """
        if not memories:
            return []

        # If scikit-learn available, use TF-IDF ranking
        if SKLEARN_AVAILABLE:
            try:
                return self._tfidf_rank(question, memories)
            except Exception:
                # Fall back to original order on error
                pass

        # Fallback: Return as-is (already ranked by search)
        return memories

    def _tfidf_rank(
        self, question: str, memories: List[MemoryEntry]
    ) -> List[MemoryEntry]:
        """
        Rank memories using TF-IDF cosine similarity.

        Args:
            question: Question text
            memories: Memories to rank

        Returns:
            Memories sorted by TF-IDF similarity to question
        """
        if not SKLEARN_AVAILABLE or not memories:
            return memories

        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            stop_words="english",
            lowercase=True,
            max_features=500,
            ngram_range=(1, 2),  # Unigrams and bigrams
        )

        # Create corpus: question + all memory texts
        texts = [question] + [f"{m.title} {m.content}" for m in memories]

        try:
            # Fit and transform
            vectors = vectorizer.fit_transform(texts)

            # Calculate similarity: question vs each memory
            question_vec = vectors[0:1]
            memory_vecs = vectors[1:]
            similarities = cosine_similarity(question_vec, memory_vecs)[0]

            # Sort by similarity (descending)
            ranked_indices = similarities.argsort()[::-1]
            return [memories[i] for i in ranked_indices]

        except ValueError:
            # Empty vocabulary or other error
            return memories

    def _generate_answer(
        self, question: str, memories: List[MemoryEntry]
    ) -> str:
        """
        Generate answer from memories.

        Strategy:
        - Single memory: Return title + content
        - Multiple memories: Combine top 3 with numbered list
        - Simple extraction approach (no LLM synthesis)

        Args:
            question: Question text
            memories: Ranked relevant memories

        Returns:
            Generated answer text
        """
        if not memories:
            return "No relevant information found."

        # Single memory: Direct answer
        if len(memories) == 1:
            mem = memories[0]
            return f"{mem.title}: {mem.content}"

        # Multiple memories: Synthesize from top 3
        parts: List[str] = []
        for i, mem in enumerate(memories[:3], 1):
            # Format each memory contribution
            parts.append(f"{i}. {mem.title}: {mem.content}")

        return "\n\n".join(parts)

    def _calculate_confidence(
        self, memories: List[MemoryEntry], question: str
    ) -> float:
        """
        Calculate confidence score for the answer.

        Confidence Factors:
        1. Count score (30%): More relevant memories = higher confidence
           - Cap at 5 memories (1.0 score)
        2. Memory confidence (40%): Average confidence of memories
           - Uses confidence field from auto-extracted memories
           - Defaults to 0.5 for manual memories
        3. Keyword overlap (30%): Question-answer keyword similarity
           - Jaccard index of question words vs memory words

        Args:
            memories: Relevant memories used for answer
            question: Original question text

        Returns:
            Confidence score (0.0-1.0)
        """
        if not memories:
            return 0.0

        # Factor 1: Count score (more memories = higher confidence)
        # Cap at 5 memories for 1.0 score
        count_score = min(len(memories) / 5.0, 1.0)

        # Factor 2: Average memory confidence
        # Use confidence field if available, else default to 0.5
        confidences = [
            m.confidence for m in memories if m.confidence is not None
        ]
        avg_confidence = (
            sum(confidences) / len(confidences) if confidences else 0.5
        )

        # Factor 3: Keyword overlap (Jaccard index)
        question_words = set(question.lower().split())
        overlap_scores: List[float] = []

        for mem in memories:
            mem_words = set(f"{mem.title} {mem.content}".lower().split())
            if mem_words:
                # Jaccard index: intersection / union
                intersection = len(question_words & mem_words)
                union = len(question_words | mem_words)
                overlap = intersection / union if union > 0 else 0.0
                overlap_scores.append(overlap)

        avg_overlap = (
            sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0.0
        )

        # Weighted average
        confidence = (
            count_score * self.COUNT_WEIGHT
            + avg_confidence * self.MEMORY_CONFIDENCE_WEIGHT
            + avg_overlap * self.KEYWORD_OVERLAP_WEIGHT
        )

        # Ensure confidence is in [0.0, 1.0]
        return min(max(confidence, 0.0), 1.0)
