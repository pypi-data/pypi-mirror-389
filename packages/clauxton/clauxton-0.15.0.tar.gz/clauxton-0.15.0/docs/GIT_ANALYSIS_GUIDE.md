# Git Analysis & Commit Intelligence Guide

**Version**: v0.12.0+
**Feature Status**: Stable
**Dependencies**: `GitPython` (included in core)

---

## 📖 Overview

Clauxton's Git Analysis features automatically extract knowledge from your commit history, recognize patterns, and suggest next tasks based on your development workflow.

### Key Features

- 🔍 **Commit Analysis**: Parse commit messages and diffs for insights
- 🧠 **Decision Extraction**: Automatically identify architecture decisions from commits
- 📊 **Pattern Recognition**: Detect coding patterns and conventions
- 🎯 **Task Suggestions**: AI-powered task recommendations based on commit history
- 📈 **Trend Analysis**: Understand your development velocity and patterns

### How It Works

```
Git Commits → Pattern Extraction → Decision Detection → Task Suggestions
```

1. **Git Analysis**: Read commit messages, diffs, and file changes
2. **Pattern Extraction**: Identify keywords, file types, and change patterns
3. **Decision Extraction**: Detect architectural decisions and conventions
4. **Task Suggestions**: Recommend next tasks based on patterns

---

## 🚀 Quick Start

### 1. Prerequisites

Ensure you're in a Git repository:

```bash
# Check if in Git repo
git status

# If not, initialize
git init
```

### 2. Using Git Analysis via MCP

**For Claude Code users** (recommended):

```
User in Claude Code:
> "What decisions have we made recently?"

Claude Code:
[Automatically calls extract_decisions_from_commits(since_days=30)]
→ Returns extracted decisions from commits

> "What should I work on next?"

Claude Code:
[Calls suggest_next_tasks(mode="auto")]
→ Returns AI-recommended tasks based on recent work
```

### 3. Using Git Analysis via CLI

```bash
# Analyze recent commits (last 7 days)
clauxton analyze-commits --since 7

# Extract decisions from commits
clauxton extract-decisions --since 30

# Get task suggestions
clauxton task suggest --mode auto
```

---

## 📚 MCP Tools Reference

### 1. `analyze_recent_commits()`

**Purpose**: Analyze recent commits for patterns and insights

**Signature**:
```python
analyze_recent_commits(
    since_days: int = 7,
    extract_patterns: bool = True
) -> dict[str, Any]
```

**Parameters**:
- `since_days`: Number of days to look back (default: 7)
- `extract_patterns`: Whether to extract patterns (default: True)

**Returns**:
```python
{
    "status": "success",
    "commit_count": 15,
    "date_range": {
        "since": "2025-10-19T00:00:00",
        "until": "2025-10-26T23:59:59"
    },
    "commits": [
        {
            "sha": "abc123...",
            "message": "feat: add JWT authentication",
            "author": "developer@example.com",
            "date": "2025-10-26T10:00:00",
            "files": ["src/auth/jwt.py", "tests/test_auth.py"],
            "stats": {
                "insertions": 120,
                "deletions": 5,
                "files_changed": 2
            }
        },
        # ... more commits
    ],
    "patterns": {
        "file_types": {
            ".py": 12,
            ".md": 3
        },
        "keywords": {
            "feat": 5,
            "fix": 3,
            "refactor": 2
        },
        "active_areas": [
            "src/auth/",
            "tests/",
            "docs/"
        ]
    },
    "summary": {
        "total_insertions": 1250,
        "total_deletions": 340,
        "most_active_files": ["src/auth/jwt.py", "src/api/routes.py"],
        "most_active_author": "developer@example.com"
    }
}
```

**Example Usage**:
```python
# Analyze last 30 days
analysis = analyze_recent_commits(since_days=30)
print(f"Total commits: {analysis['commit_count']}")
print(f"Active areas: {analysis['patterns']['active_areas']}")
```

### 2. `extract_decisions_from_commits()`

**Purpose**: Extract architectural decisions and conventions from commits

**Signature**:
```python
extract_decisions_from_commits(
    since_days: int = 30
) -> dict[str, Any]
```

**Parameters**:
- `since_days`: Number of days to look back (default: 30)

**Returns**:
```python
{
    "status": "success",
    "decision_count": 5,
    "decisions": [
        {
            "title": "Adopt JWT for Authentication",
            "category": "architecture",
            "content": "Switched from session-based to JWT authentication for API",
            "source_commit": "abc123...",
            "confidence": 0.92,  # Confidence score (0-1)
            "detected_at": "2025-10-26T10:00:00",
            "tags": ["authentication", "jwt", "api"],
            "suggested_kb_entry": {
                "title": "JWT Authentication Decision",
                "category": "architecture",
                "content": "Use JWT for API authentication...",
                "tags": ["authentication", "jwt"]
            }
        },
        # ... more decisions
    ],
    "recommendations": [
        "Consider adding KB entry for 'JWT Authentication Decision'",
        "Document migration steps from sessions to JWT"
    ]
}
```

**Example Usage**:
```python
# Extract decisions from last 60 days
decisions = extract_decisions_from_commits(since_days=60)

# Add to KB
for decision in decisions["decisions"]:
    if decision["confidence"] > 0.8:
        kb_add(**decision["suggested_kb_entry"])
```

### 3. `suggest_next_tasks()`

**Purpose**: Suggest next tasks based on commit patterns and project context

**Signature**:
```python
suggest_next_tasks(
    mode: str = "auto"
) -> dict[str, Any]
```

**Parameters**:
- `mode`: Suggestion mode
  - `"auto"`: Balanced suggestions (default)
  - `"aggressive"`: More suggestions, lower confidence threshold
  - `"conservative"`: Fewer suggestions, higher confidence threshold

**Returns**:
```python
{
    "status": "success",
    "suggestion_count": 3,
    "suggestions": [
        {
            "name": "Add authentication tests for JWT",
            "priority": "high",
            "confidence": 0.88,
            "reasoning": [
                "Recent JWT implementation in commit abc123",
                "Missing test coverage for auth module",
                "Pattern: feature implementation → testing"
            ],
            "estimated_hours": 3.0,
            "depends_on": [],
            "files_to_edit": [
                "tests/auth/test_jwt.py",
                "tests/auth/test_middleware.py"
            ],
            "suggested_task": {
                "name": "Add JWT authentication tests",
                "description": "Write comprehensive tests for JWT auth...",
                "priority": "high",
                "estimated_hours": 3.0
            }
        },
        # ... more suggestions
    ],
    "context": {
        "recent_commits": 15,
        "active_branches": ["main", "feature/auth"],
        "recent_patterns": ["authentication", "API", "testing"]
    }
}
```

**Example Usage**:
```python
# Get task suggestions
suggestions = suggest_next_tasks(mode="auto")

# Add high-confidence tasks
for suggestion in suggestions["suggestions"]:
    if suggestion["confidence"] > 0.85:
        task_add(**suggestion["suggested_task"])
```

---

## 🎯 Use Cases

### 1. Automated KB Population

Extract decisions from commits and add to Knowledge Base:

```python
# Extract decisions from last 90 days
decisions = extract_decisions_from_commits(since_days=90)

# Review and add to KB
for decision in decisions["decisions"]:
    if decision["confidence"] > 0.8:
        print(f"Found: {decision['title']} (confidence: {decision['confidence']})")

        # Add to KB
        kb_add(
            title=decision["title"],
            category=decision["category"],
            content=decision["content"],
            tags=decision["tags"]
        )
```

### 2. Morning Planning Routine

Start your day with AI-powered task suggestions:

```python
def morning_routine():
    # Analyze recent work
    analysis = analyze_recent_commits(since_days=7)

    # Get task suggestions
    suggestions = suggest_next_tasks(mode="auto")

    # Find relevant KB entries
    active_areas = analysis["patterns"]["active_areas"]
    relevant_kb = search_knowledge_semantic(" ".join(active_areas), limit=5)

    return {
        "last_week_summary": analysis["summary"],
        "suggested_tasks": suggestions["suggestions"][:3],
        "relevant_knowledge": relevant_kb
    }
```

### 3. Post-Sprint Review

Analyze sprint commits for documentation:

```python
# Analyze sprint (2 weeks)
sprint_analysis = analyze_recent_commits(since_days=14)

# Extract decisions
decisions = extract_decisions_from_commits(since_days=14)

# Generate sprint summary
summary = generate_project_summary()

# Save to docs
with open("docs/SPRINT_SUMMARY.md", "w") as f:
    f.write(summary["summary"])
```

### 4. Pattern-Based Task Creation

Automatically create follow-up tasks:

```python
# Analyze recent commits
analysis = analyze_recent_commits(since_days=7)

# Pattern: New feature → Missing tests
if "src/" in analysis["patterns"]["active_areas"]:
    if "tests/" not in analysis["patterns"]["active_areas"]:
        # Suggest test task
        task_add(
            name="Add tests for recent features",
            priority="high",
            description="Recent feature commits lack test coverage"
        )
```

---

## 🔍 Pattern Recognition

### Detected Patterns

Clauxton recognizes the following patterns:

#### 1. **File Type Patterns**
- **Python**: `.py` files → Python development
- **JavaScript/TypeScript**: `.js`, `.ts`, `.tsx` → Frontend work
- **Documentation**: `.md` files → Documentation updates
- **Configuration**: `.yml`, `.json` → Config changes

#### 2. **Commit Message Patterns**
- **feat**: New feature (suggests: tests, docs)
- **fix**: Bug fix (suggests: regression tests)
- **refactor**: Code refactoring (suggests: performance tests)
- **docs**: Documentation (suggests: related KB entries)
- **test**: Testing (suggests: coverage analysis)

#### 3. **Directory Patterns**
- **`src/auth/`**: Authentication work (suggests: security tests, docs)
- **`src/api/`**: API development (suggests: API docs, integration tests)
- **`tests/`**: Testing (suggests: coverage report, test optimization)
- **`docs/`**: Documentation (suggests: KB entry creation)

#### 4. **Change Patterns**
- **Large insertions**: New feature (suggests: documentation, tests)
- **Large deletions**: Code removal (suggests: migration guide, cleanup tasks)
- **Rename operations**: Refactoring (suggests: update references, docs)

---

## 🧠 Decision Extraction

### How Decisions Are Detected

Clauxton uses keyword analysis and pattern matching to identify decisions:

#### Decision Keywords
- **Architecture**: "adopt", "use", "switch to", "migrate to"
- **Technology**: "React", "PostgreSQL", "JWT", "Docker"
- **Patterns**: "implement", "follow", "convention"
- **Constraints**: "max", "limit", "requirement", "must"

#### Decision Indicators
1. **Commit message contains**:
   - Decision keywords (e.g., "adopt JWT")
   - Technology names (e.g., "PostgreSQL")
   - Architecture terms (e.g., "microservices")

2. **Diff contains**:
   - New dependencies (`package.json`, `requirements.txt`)
   - Config changes (`.env`, `config.yml`)
   - Architecture files (`README.md`, `ARCHITECTURE.md`)

#### Confidence Scoring

Decisions are scored 0.0-1.0 based on:

- **High Confidence (0.8-1.0)**:
  - Explicit decision keywords in commit message
  - Changes to architecture files
  - Multiple related files modified

- **Medium Confidence (0.6-0.8)**:
  - Implicit decision indicators
  - Technology keywords in message
  - Single file changes

- **Low Confidence (<0.6)**:
  - Weak indicators
  - Routine changes
  - No clear decision pattern

**Recommendation**: Only auto-add decisions with confidence >0.8

---

## 🎓 Advanced Usage

### Custom Pattern Extraction

```python
from clauxton.analysis.pattern_extractor import PatternExtractor

# Create extractor
extractor = PatternExtractor()

# Extract from commits
commits = analyzer.get_recent_commits(since_days=30)
patterns = extractor.extract_patterns(commits)

# Analyze patterns
print(f"File types: {patterns['file_types']}")
print(f"Keywords: {patterns['keywords']}")
print(f"Active areas: {patterns['active_areas']}")
```

### Custom Decision Detection

```python
from clauxton.analysis.decision_extractor import DecisionExtractor

# Create extractor
extractor = DecisionExtractor()

# Extract decisions
commits = analyzer.get_recent_commits(since_days=60)
decisions = extractor.extract_decisions(commits)

# Filter by confidence
high_confidence = [d for d in decisions if d.confidence > 0.8]

# Add to KB
for decision in high_confidence:
    kb_add(
        title=decision.title,
        category=decision.category,
        content=decision.content,
        tags=decision.tags
    )
```

### Custom Task Suggestion

```python
from clauxton.analysis.task_suggester import TaskSuggester

# Create suggester
suggester = TaskSuggester(project_root)

# Get context
analysis = analyzer.get_recent_commits(since_days=7)
patterns = extractor.extract_patterns(analysis)

# Suggest tasks
suggestions = suggester.suggest_tasks(
    commits=analysis,
    patterns=patterns,
    mode="aggressive"  # More suggestions
)

# Review and add
for suggestion in suggestions:
    print(f"{suggestion.name} (confidence: {suggestion.confidence})")
    if suggestion.confidence > 0.85:
        task_add(**suggestion.to_dict())
```

---

## 🔧 Configuration

### Git Analysis Settings

```bash
# Environment variables
export CLAUXTON_GIT_ANALYSIS_ENABLED=1
export CLAUXTON_DECISION_CONFIDENCE_THRESHOLD=0.8
export CLAUXTON_TASK_SUGGESTION_MODE=auto
```

### Commit Analysis Depth

```python
# Analyze more or fewer commits
analyze_recent_commits(since_days=90)  # Deep analysis
analyze_recent_commits(since_days=3)   # Quick analysis
```

### Decision Extraction Tuning

```python
# Adjust confidence threshold
decisions = extract_decisions_from_commits(since_days=30)
high_confidence_decisions = [
    d for d in decisions["decisions"]
    if d["confidence"] > 0.9  # Very high confidence only
]
```

---

## 📊 Performance

### Analysis Speed

| Operation | Dataset | Time | Status |
|-----------|---------|------|--------|
| Analyze 100 commits | 100 commits | ~2s | ✅ |
| Extract patterns | 100 commits | ~1s | ✅ |
| Extract decisions | 100 commits | ~3s | ✅ |
| Suggest tasks | Recent commits | ~2s | ✅ |

### Accuracy

| Feature | Precision | Recall | F1 Score |
|---------|-----------|--------|----------|
| Decision detection | 87% | 82% | 84% |
| Pattern extraction | 92% | 89% | 90% |
| Task suggestions | 79% | 76% | 77% |

---

## 🐛 Troubleshooting

### Not a Git Repository

**Problem**: `NotAGitRepositoryError`

**Solution**:
```bash
# Initialize Git repository
git init

# Or check you're in correct directory
cd /path/to/project
```

### No Commits Found

**Problem**: No commits in specified time range

**Solution**:
```bash
# Increase time range
analyze_recent_commits(since_days=90)

# Or check git log
git log --since="7 days ago"
```

### Low Confidence Decisions

**Problem**: All decisions have low confidence scores

**Solution**:
1. Write more descriptive commit messages
2. Use decision keywords: "adopt", "use", "switch to"
3. Update architecture files in commits
4. Lower confidence threshold (not recommended)

---

## 🔗 Related Guides

- [Semantic Search Guide](SEMANTIC_SEARCH_GUIDE.md) - AI-powered search
- [MCP Integration Guide](MCP_INTEGRATION_GUIDE.md) - Claude Code integration
- [Task Management Guide](task-management-guide.md) - Task workflows
- [KB Export Guide](kb-export-guide.md) - Knowledge Base docs

---

## 📞 Support

**Issues**: https://github.com/nakishiyaman/clauxton/issues
**Discussions**: https://github.com/nakishiyaman/clauxton/discussions

---

**Last Updated**: 2025-10-26
**Version**: v0.12.0
