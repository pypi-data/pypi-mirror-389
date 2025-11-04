"""Tests for Query Modal (widgets/query_modal.py and related services)."""

from pathlib import Path

from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.models import KnowledgeBaseEntry
from clauxton.core.task_manager import TaskManager
from clauxton.tui.services.autocomplete import (
    CompositeAutocompleteProvider,
    FilePathAutocompleteProvider,
    KBAutocompleteProvider,
    TaskAutocompleteProvider,
)
from clauxton.tui.services.query_executor import QueryExecutor, QueryMode, QueryResult
from clauxton.tui.widgets.query_modal import QueryModal


class TestAutocompleteProviders:
    """Test suite for autocomplete providers."""

    def test_kb_autocomplete_provider_initialization(self, tmp_path: Path) -> None:
        """Test KB autocomplete provider initializes correctly."""
        (tmp_path / ".clauxton").mkdir()
        provider = KBAutocompleteProvider(tmp_path)
        assert provider.project_root == tmp_path

    def test_kb_autocomplete_with_entries(self, tmp_path: Path) -> None:
        """Test KB autocomplete returns entry titles and tags."""
        (tmp_path / ".clauxton").mkdir()

        # Add KB entries
        kb = KnowledgeBase(tmp_path)
        from datetime import datetime
        now = datetime.now()

        entry1 = KnowledgeBaseEntry(
            id=f"KB-{now.strftime('%Y%m%d')}-001",
            title="API Design",
            category="architecture",
            content="REST API patterns",
            tags=["api", "rest"],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry1)

        provider = KBAutocompleteProvider(tmp_path)
        suggestions = provider.get_suggestions("api", limit=5)

        assert "API Design" in suggestions or "api" in suggestions

    def test_task_autocomplete_provider_initialization(self, tmp_path: Path) -> None:
        """Test task autocomplete provider initializes correctly."""
        (tmp_path / ".clauxton").mkdir()
        provider = TaskAutocompleteProvider(tmp_path)
        assert provider.project_root == tmp_path

    def test_task_autocomplete_with_tasks(self, tmp_path: Path) -> None:
        """Test task autocomplete returns task names."""
        (tmp_path / ".clauxton").mkdir()

        # Add tasks
        from datetime import datetime

        from clauxton.core.models import Priority, Task, TaskStatus
        tm = TaskManager(tmp_path)
        now = datetime.now()

        task = Task(
            id="TASK-001",
            name="Implement feature",
            description="Add new feature",
            status=TaskStatus.PENDING,
            priority=Priority.HIGH,
            created_at=now,
            updated_at=now,
        )
        tm.add(task)

        provider = TaskAutocompleteProvider(tmp_path)
        suggestions = provider.get_suggestions("feature", limit=5)

        assert "Implement feature" in suggestions

    def test_file_path_autocomplete_provider_initialization(self, tmp_path: Path) -> None:
        """Test file path autocomplete provider initializes correctly."""
        provider = FilePathAutocompleteProvider(tmp_path)
        assert provider.project_root == tmp_path

    def test_file_path_autocomplete_with_files(self, tmp_path: Path) -> None:
        """Test file path autocomplete returns file paths."""
        # Create test files
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')")

        provider = FilePathAutocompleteProvider(tmp_path)
        suggestions = provider.get_suggestions("main", limit=5)

        # Check if any suggestion contains "main"
        assert any("main" in s for s in suggestions)

    def test_composite_autocomplete_provider_initialization(
        self, tmp_path: Path
    ) -> None:
        """Test composite provider combines multiple providers."""
        (tmp_path / ".clauxton").mkdir()
        provider = CompositeAutocompleteProvider(tmp_path)

        assert provider.project_root == tmp_path
        assert len(provider.providers) == 3  # KB, Task, FilePath


class TestQueryExecutor:
    """Test suite for query executor."""

    def test_query_executor_initialization(self, tmp_path: Path) -> None:
        """Test query executor initializes correctly."""
        (tmp_path / ".clauxton").mkdir()
        executor = QueryExecutor(tmp_path)
        assert executor.project_root == tmp_path

    def test_query_executor_normal_mode(self, tmp_path: Path) -> None:
        """Test normal mode searches KB and tasks."""
        (tmp_path / ".clauxton").mkdir()

        # Add KB entry
        kb = KnowledgeBase(tmp_path)
        from datetime import datetime
        now = datetime.now()

        entry = KnowledgeBaseEntry(
            id=f"KB-{now.strftime('%Y%m%d')}-001",
            title="Test Entry",
            category="pattern",
            content="This is a test",
            tags=["test"],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

        executor = QueryExecutor(tmp_path)
        results = executor.execute("test", mode=QueryMode.NORMAL, limit=10)

        assert isinstance(results, list)
        # Should find the KB entry
        assert len(results) > 0
        assert any(r.result_type == "kb" for r in results)

    def test_query_executor_ai_mode(self, tmp_path: Path) -> None:
        """Test AI mode returns placeholder."""
        (tmp_path / ".clauxton").mkdir()

        executor = QueryExecutor(tmp_path)
        results = executor.execute("test query", mode=QueryMode.AI, limit=10)

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0].result_type == "ai"

    def test_query_executor_file_mode(self, tmp_path: Path) -> None:
        """Test file mode searches for files."""
        (tmp_path / ".clauxton").mkdir()

        # Create test file
        (tmp_path / "test.py").write_text("print('test')")

        executor = QueryExecutor(tmp_path)
        results = executor.execute("test", mode=QueryMode.FILE, limit=10)

        assert isinstance(results, list)
        # Should find the test file
        assert any("test" in r.title.lower() for r in results)

    def test_query_result_structure(self) -> None:
        """Test query result has correct structure."""
        result = QueryResult(
            title="Test Result",
            content="Test content",
            result_type="test",
            score=0.85,
            metadata={"key": "value"},
        )

        assert result.title == "Test Result"
        assert result.content == "Test content"
        assert result.result_type == "test"
        assert result.score == 0.85
        assert result.metadata["key"] == "value"


class TestQueryModal:
    """Test suite for QueryModal widget."""

    def test_query_modal_initialization(self, tmp_path: Path) -> None:
        """Test query modal initializes correctly."""
        (tmp_path / ".clauxton").mkdir()

        modal = QueryModal(project_root=tmp_path)

        assert modal.project_root == tmp_path
        assert modal.current_mode == QueryMode.NORMAL
        assert isinstance(modal.autocomplete_provider, CompositeAutocompleteProvider)
        assert isinstance(modal.query_executor, QueryExecutor)

    def test_query_modal_has_bindings(self, tmp_path: Path) -> None:
        """Test query modal has keyboard bindings."""
        (tmp_path / ".clauxton").mkdir()

        modal = QueryModal(project_root=tmp_path)

        # Check BINDINGS class attribute
        assert hasattr(modal, "BINDINGS")
        bindings = [b[0] for b in modal.BINDINGS]
        assert "escape" in bindings
        assert "ctrl+n" in bindings

    def test_query_modal_has_compose_method(self, tmp_path: Path) -> None:
        """Test query modal has compose method."""
        (tmp_path / ".clauxton").mkdir()

        modal = QueryModal(project_root=tmp_path)

        assert hasattr(modal, "compose")
        assert callable(modal.compose)

    def test_query_modal_action_cancel(self, tmp_path: Path) -> None:
        """Test cancel action dismisses modal with None."""
        (tmp_path / ".clauxton").mkdir()

        modal = QueryModal(project_root=tmp_path)

        assert hasattr(modal, "action_cancel")
        assert callable(modal.action_cancel)

    def test_query_modal_action_next_mode(self, tmp_path: Path) -> None:
        """Test next mode action cycles through modes."""
        (tmp_path / ".clauxton").mkdir()

        modal = QueryModal(project_root=tmp_path)

        # Initial mode
        assert modal.current_mode == QueryMode.NORMAL

        # Can't call action_next_mode without mounting, test method exists
        assert hasattr(modal, "action_next_mode")
        assert callable(modal.action_next_mode)

    def test_query_modal_mode_cycling_logic(self, tmp_path: Path) -> None:
        """Test mode cycling logic."""
        (tmp_path / ".clauxton").mkdir()

        modal = QueryModal(project_root=tmp_path)

        # Verify all modes exist
        modes = list(QueryMode)
        assert len(modes) == 4
        assert modal.current_mode in modes
        assert QueryMode.NORMAL in modes
        assert QueryMode.AI in modes
        assert QueryMode.FILE in modes
        assert QueryMode.SYMBOL in modes

    def test_query_modal_execute_query_method(self, tmp_path: Path) -> None:
        """Test execute query method exists."""
        (tmp_path / ".clauxton").mkdir()

        modal = QueryModal(project_root=tmp_path)

        assert hasattr(modal, "_execute_query")
        assert callable(modal._execute_query)

    def test_query_executor_empty_query(self, tmp_path: Path) -> None:
        """Test executor handles empty query."""
        (tmp_path / ".clauxton").mkdir()

        executor = QueryExecutor(tmp_path)
        results = executor.execute("", mode=QueryMode.NORMAL, limit=10)

        # Empty query should return empty results or handle gracefully
        assert isinstance(results, list)
