# Next Session: v0.12.0 Implementation

**Date**: TBD
**Goal**: Start implementing semantic search foundation
**Estimated Time**: 4-6 hours

---

## 📋 Session Preparation

### Before You Start

1. **Read the design document**
   - Location: `docs/v0.12.0-design.md`
   - Focus on: Semantic Module design (Section 1)
   - Time: 15-20 minutes

2. **Install dependencies (optional test)**
   ```bash
   pip install sentence-transformers faiss-cpu torch
   ```
   Note: ~500MB download, takes 2-3 minutes

3. **Review current branch**
   ```bash
   git status
   # Should be on: feature/ai-integration-v0.12.0
   ```

---

## 🎯 Week 1, Day 1 Tasks

### Implementation Order (4-6 hours)

#### Task 1: `embeddings.py` (2 hours)

**File**: `clauxton/semantic/embeddings.py`

**Checklist**:
- [ ] Implement `EmbeddingEngine` class
- [ ] Add lazy model loading
- [ ] Implement user consent check
- [ ] Add `encode()` and `encode_single()` methods
- [ ] Handle errors: `UserConsentError`, `ModelLoadError`
- [ ] Add caching logic
- [ ] Write docstrings (Google style)

**Tests to Write** (`tests/semantic/test_embeddings.py`):
- [ ] `test_embedding_engine_initialization`
- [ ] `test_lazy_model_loading`
- [ ] `test_encode_single_text`
- [ ] `test_encode_batch`
- [ ] `test_user_consent_required`
- [ ] `test_model_caching`
- [ ] `test_encode_unicode_text`
- [ ] `test_embedding_dimension_384`

**Success Criteria**:
```python
# This should work:
engine = EmbeddingEngine()
embedding = engine.encode_single("Hello world")
assert embedding.shape == (384,)
```

**Reference**: See `docs/v0.12.0-design.md` Section 1.1

---

#### Task 2: Basic Tests (1 hour)

**File**: `tests/semantic/test_embeddings.py`

**Checklist**:
- [ ] Setup test fixtures
- [ ] Mock model downloads (don't actually download in CI)
- [ ] Test with fake embeddings
- [ ] Test error cases
- [ ] Run tests: `pytest tests/semantic/test_embeddings.py -v`

**Success Criteria**:
- All tests pass ✅
- Coverage >90% for `embeddings.py`

---

#### Task 3: Type Checking & Linting (30 minutes)

**Checklist**:
- [ ] Run mypy: `mypy clauxton/semantic/embeddings.py`
- [ ] Fix type errors
- [ ] Run ruff: `ruff check clauxton/semantic/`
- [ ] Fix linting issues

**Success Criteria**:
- No mypy errors
- No ruff errors

---

#### Task 4: Commit Progress (30 minutes)

**Checklist**:
- [ ] Review changes: `git diff`
- [ ] Stage files: `git add clauxton/semantic/embeddings.py tests/semantic/test_embeddings.py`
- [ ] Commit with descriptive message
- [ ] Push to remote (optional)

**Commit Message Template**:
```
feat(semantic): implement embedding engine with lazy loading

- Add EmbeddingEngine class for local embeddings
- Implement lazy model loading (download on first use)
- Add user consent check for model download (~90MB)
- Support batch and single text encoding
- Add caching for model files
- Write 8 unit tests with 92% coverage

Technical details:
- Model: sentence-transformers/all-MiniLM-L6-v2
- Dimension: 384
- Performance: ~500 texts/sec on CPU
- Cache: ~/.cache/clauxton/models/

Part of v0.12.0: Semantic Intelligence via MCP

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 🔄 If You Have More Time

### Bonus Task: Start `vector_store.py` (2 hours)

**File**: `clauxton/semantic/vector_store.py`

**Checklist**:
- [ ] Implement `VectorStore` class
- [ ] Add FAISS integration
- [ ] Implement `add()` and `search()` methods
- [ ] Add persistence (save/load)
- [ ] Write 5-8 basic tests

**Reference**: See `docs/v0.12.0-design.md` Section 1.2

---

## 📊 Progress Tracking

Update this checklist as you work:

### Week 1 Progress
- [ ] Day 1: `embeddings.py` ✅
- [ ] Day 2: `vector_store.py`
- [ ] Day 3: `indexer.py`
- [ ] Day 4: `search.py`
- [ ] Day 5: MCP tool: `search_knowledge_semantic()`

### Metrics
- Lines of code written: ___
- Tests written: ___
- Test coverage: ___%
- Time spent: ___ hours

---

## 🐛 Troubleshooting

### Issue: Dependencies not installing

**Solution**:
```bash
# Try with specific versions
pip install sentence-transformers==2.3.0 faiss-cpu==1.7.4 torch==2.1.0

# Or use conda (alternative)
conda install -c pytorch faiss-cpu
```

### Issue: Model download fails

**Solution**:
```bash
# Download manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Issue: Tests fail with "CUDA not available"

**Solution**:
```python
# Force CPU in tests
# In test setup:
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
```

### Issue: Import errors

**Solution**:
```bash
# Reinstall in editable mode
pip install -e .
```

---

## 📝 Notes & Ideas

Use this space for notes during implementation:

```
// Your notes here...
```

---

## ✅ Session Complete Checklist

Before ending the session:

- [ ] All code committed
- [ ] All tests passing
- [ ] No mypy/ruff errors
- [ ] Update `NEXT_SESSION.md` with progress
- [ ] Note any blockers or questions

---

**Good luck! 🚀**

Remember:
- Start with tests (TDD)
- Commit frequently
- Ask for help if stuck
- Reference the design doc often
