# Quality Review Prompts for SubAgent Development

**Purpose**: Phase完了後の品質レビュー用の最適化されたプロンプト集
**Target**: v0.15.0 Unified Memory Model 開発
**Last Updated**: 2025-11-03

---

## プロンプト改善の原則

### 元のプロンプトの課題

**元のプロンプト1**: "コードをレビュー/改善して。"
- ❌ 曖昧で具体性に欠ける
- ❌ 対象範囲が不明確
- ❌ 期待する成果物が不明確
- ❌ 改善の実行計画がない

**元のプロンプト2**: "パフォーマンスは最適化されておりパフォーマンステストできていますか？テストの **観点** 、カバレッジ、Lintチェック、シナリオテスト、セキュリティテストに不足はありませんか？また、ドキュメントの追加や修正は必要ないですか？"
- ❌ 質問形式で答えにくい
- ❌ チェック項目が列挙されているが構造化されていない
- ❌ 改善タスクの作成が不明確
- ❌ 優先順位付けがない

### 改善の方針

1. **コンテキストを明確にする** - Phase、対象ファイル、完了条件
2. **期待する成果物を明示する** - レポート形式、改善タスクリスト
3. **チェック項目を構造化する** - カテゴリ別、優先度別
4. **実行可能性を高める** - 具体的な改善タスク、工数見積もり
5. **SubAgent実行に最適化する** - Task tool で実行しやすい形式

---

## 改善版プロンプト集

### Prompt 1: 包括的品質レビュー（標準）

**使用タイミング**: 各Phase完了後（Day 12, 24, 30, 36）

**改善版プロンプト**:

```
# Comprehensive Quality Review: Phase [N] Completion

## Context
- **Phase**: Phase [N] - [Phase Name]
- **Completion Date**: [YYYY-MM-DD]
- **Deliverables**:
  - [List of files/components completed]
  - [Number of tests added]
  - [Number of lines of code]

## Review Scope

### Target Files
```
[List all files to review]
clauxton/core/memory.py
clauxton/core/memory_store.py
clauxton/core/knowledge_base_compat.py
tests/core/test_memory.py
tests/core/test_compatibility.py
... (complete list)
```

### Existing Metrics (Baseline)
- Test count: [N] tests
- Coverage: [N]%
- mypy: [Pass/Fail]
- ruff: [N warnings]

## Review Checklist

### 1. Code Quality Analysis ⭐ Priority: HIGH
**Objective**: Identify code smells, violations of principles, maintainability issues

Check:
- [ ] **DRY (Don't Repeat Yourself)**: No code duplication >5 lines
- [ ] **SOLID Principles**: Single Responsibility, Open-Closed, etc.
- [ ] **Naming Conventions**: Clear, consistent, self-documenting names
- [ ] **Function Complexity**: Cyclomatic complexity <10 per function
- [ ] **Code Style**: Consistent with CLAUDE.md and existing codebase
- [ ] **Error Handling**: Consistent exception handling, no bare except
- [ ] **Type Safety**: No use of `Any`, proper type hints

Tools to use:
- `ruff check` for linting
- Manual code inspection
- Compare with existing patterns in codebase

**Deliverable**: Code quality report with specific issues and line numbers

---

### 2. Performance Analysis ⭐ Priority: HIGH
**Objective**: Identify performance bottlenecks and optimization opportunities

Check:
- [ ] **Critical Path Profiling**: Profile main workflows (add, search, migrate)
- [ ] **Algorithmic Complexity**: No O(n²) where O(n log n) is possible
- [ ] **Memory Usage**: No memory leaks, efficient data structures
- [ ] **Caching Opportunities**: Identify repeated computations
- [ ] **I/O Optimization**: Batch operations, async where beneficial
- [ ] **Benchmark Existence**: Performance tests for critical operations

Performance Targets:
- Memory.search(): <100ms for 1,000 entries
- Memory.add(): <50ms
- Migration: <1s for 1,000 entries

Tools to use:
- `pytest --benchmark` for benchmarking
- `cProfile` for profiling
- `memory_profiler` for memory analysis

**Deliverable**:
1. Performance benchmark results (current vs. target)
2. Bottleneck identification with specific functions
3. Optimization recommendations with estimated impact

---

### 3. Test Quality Review ⭐ Priority: CRITICAL
**Objective**: Ensure comprehensive test coverage and quality

#### 3.1 Test Observation Points (テスト観点)
Check all critical observation points are tested:

- [ ] **Functional Correctness**: Core functionality works as specified
- [ ] **Edge Cases**: Boundary values (0, 1, max, empty, None, Unicode)
- [ ] **Error Conditions**: Invalid input, exceptions, edge failures
- [ ] **Concurrency**: Thread safety, race conditions (if applicable)
- [ ] **Integration**: Component interaction, data flow between modules
- [ ] **Regression**: Breaking changes, backward compatibility
- [ ] **State Transitions**: Valid and invalid state changes

#### 3.2 Coverage Analysis
- [ ] **Line Coverage**: >95% (target: 95-98%)
- [ ] **Branch Coverage**: >90%
- [ ] **Path Coverage**: Critical paths tested
- [ ] **Missing Scenarios**: Identify untested scenarios

Run:
```bash
pytest --cov=clauxton/core --cov-report=html --cov-report=term-missing
```

#### 3.3 Test Types Presence
- [ ] **Unit Tests**: Isolated component testing
- [ ] **Integration Tests**: Multi-component workflows
- [ ] **Performance Tests**: Benchmarks for critical operations
- [ ] **Security Tests**: Injection, validation, boundary checks
- [ ] **Scenario Tests**: End-to-end user workflows

#### 3.4 Test Quality
- [ ] **Test Naming**: Descriptive, follows pattern `test_<what>_<condition>_<expected>`
- [ ] **Arrange-Act-Assert**: Clear test structure
- [ ] **No Flaky Tests**: Deterministic, no random failures
- [ ] **Fast Execution**: Total test suite <5s for unit tests
- [ ] **Test Data**: Realistic, edge cases covered
- [ ] **Assertions**: Specific, meaningful error messages

Tools to use:
- `pytest -v` for test execution
- `pytest --cov` for coverage
- `pytest-benchmark` for performance tests

**Deliverable**:
1. Test gap analysis (missing scenarios, coverage gaps)
2. Test quality issues (flaky, slow, unclear)
3. Recommended additional tests with priority

---

### 4. Security Audit ⭐ Priority: HIGH
**Objective**: Identify security vulnerabilities and risks

Check:
- [ ] **Input Validation**: All user inputs validated (type, range, format)
- [ ] **Injection Risks**: SQL injection, command injection, path traversal
- [ ] **YAML Safety**: Using `yaml.safe_load` (not `yaml.load`)
- [ ] **File Operations**: Safe file paths, no arbitrary file access
- [ ] **Authentication/Authorization**: Proper access control (if applicable)
- [ ] **Sensitive Data**: No hardcoded secrets, proper data handling
- [ ] **Dependencies**: No known vulnerabilities in dependencies

Run:
```bash
bandit -r clauxton/core
safety check
```

**Deliverable**:
1. Security vulnerabilities found (severity: Critical/High/Medium/Low)
2. Risk assessment for each vulnerability
3. Mitigation recommendations with implementation priority

---

### 5. Lint & Type Check ⭐ Priority: MEDIUM
**Objective**: Ensure code quality standards

Check:
- [ ] **mypy --strict**: No type errors
- [ ] **ruff check**: No warnings
- [ ] **No Suppressions**: All `type: ignore` justified with comments
- [ ] **Type Hints**: 100% coverage for public APIs

Run:
```bash
mypy --strict clauxton/core
ruff check clauxton/core tests/core
```

**Deliverable**: List of lint/type issues with severity and recommended fixes

---

### 6. Documentation Review ⭐ Priority: MEDIUM
**Objective**: Ensure documentation completeness and accuracy

Check:
- [ ] **API Documentation**: All public APIs documented (Google style docstrings)
- [ ] **Code Comments**: Complex logic explained
- [ ] **Usage Examples**: Practical examples in docstrings or separate guide
- [ ] **Migration Guide**: Accurate, tested instructions
- [ ] **Changelog**: Updated with new features/changes
- [ ] **README**: Reflects current state, no outdated information

**Deliverable**:
1. Documentation gaps (missing, unclear, outdated)
2. Recommended documentation additions/improvements
3. Example code needed

---

### 7. Integration Validation ⭐ Priority: HIGH
**Objective**: Ensure components work together correctly

Check:
- [ ] **Component Integration**: All components work together as designed
- [ ] **API Consistency**: No breaking changes to public APIs
- [ ] **Backward Compatibility**: Deprecated APIs still work with warnings
- [ ] **Migration Testing**: Migration script tested with real data
- [ ] **End-to-End Workflows**: Critical user workflows tested

Run integration tests:
```bash
pytest tests/integration/test_memory_workflow.py -v
```

**Deliverable**: Integration issues found and recommended fixes

---

## Expected Deliverables

### 1. Executive Summary Report
```markdown
# Phase [N] Quality Review Summary

## Overall Status
✅/⚠️/❌ [PASS / PASS with Issues / FAIL]

## Metrics
- Code Quality: [Score/Grade]
- Performance: [Pass/Fail with details]
- Test Coverage: [N%]
- Security: [Issues found]
- Documentation: [Complete/Incomplete]

## Critical Issues: [N]
[List of blocking issues]

## Major Issues: [N]
[List of high-priority issues]

## Minor Issues: [N]
[List of nice-to-have improvements]

## Recommendations
[Top 3-5 recommendations with priority]
```

### 2. Detailed Findings Report
For each category (Code Quality, Performance, Testing, Security, Lint, Documentation, Integration):
- Issues found (with file:line references)
- Severity (Critical/High/Medium/Low)
- Impact assessment
- Recommended fix

### 3. Improvement Task List
```markdown
## Improvement Tasks (Prioritized)

### Critical (Blocking) - Must fix before Phase completion
1. [CRITICAL] Optimize migration performance
   - Current: 2.5s for 1000 entries
   - Target: <1s
   - Estimated effort: 1 day
   - Suggested approach: Add batch processing, optimize YAML writes

### High Priority - Should fix before next Phase
2. [HIGH] Add concurrency tests
   - Missing: Thread safety tests for Memory.search()
   - Estimated effort: 0.5 day
   - Suggested approach: Use threading.Thread, test concurrent add/search

### Medium Priority - Fix during next Phase
3. [MEDIUM] Enhance documentation examples
   - Missing: Migration guide needs more examples
   - Estimated effort: 0.25 day

### Low Priority - Fix when convenient
4. [LOW] Refactor code duplication
   - Found: 3 instances in memory.py (lines 45-60, 120-135, 180-195)
   - Estimated effort: 0.5 day
```

### 4. Quality Dashboard (Metrics)
```
Phase [N] Quality Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Code Quality:
  ✅ mypy --strict: Pass
  ✅ ruff check: Pass (0 warnings)
  ✅ Complexity: Avg 5.2 (target <10)
  ⚠️ Duplication: 3 instances

Performance:
  ✅ Memory.search(): 85ms (target <100ms)
  ✅ Memory.add(): 42ms (target <50ms)
  ❌ Migration: 2.5s (target <1s) ⬅ NEEDS FIX

Testing:
  ✅ Count: 150 tests (target 100+)
  ✅ Coverage: 96% (target >95%)
  ⚠️ Missing: Concurrency tests
  ✅ Performance: Present
  ✅ Security: Present

Security:
  ✅ Input validation: Complete
  ✅ Injection risks: None found
  ✅ YAML safety: safe_load used
  ✅ Dependencies: No vulnerabilities

Documentation:
  ✅ API docs: Complete
  ✅ Comments: Good
  ⚠️ Migration guide: Needs examples
  ✅ Changelog: Updated

Integration:
  ✅ Components: Work together
  ✅ APIs: No breaking changes
  ✅ Backward compat: Verified
  ✅ Migration: Tested

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall: ✅ PASS with Minor Issues
Critical: 0 | High: 1 | Medium: 2 | Low: 4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Review Execution Instructions

### Step 1: Analyze Code
- Read all target files
- Run static analysis tools (mypy, ruff, bandit)
- Compare against coding standards (CLAUDE.md)

### Step 2: Profile Performance
- Run performance benchmarks
- Profile critical paths
- Identify bottlenecks

### Step 3: Evaluate Tests
- Run test suite with coverage
- Analyze test quality
- Identify gaps

### Step 4: Security Audit
- Check input validation
- Scan for vulnerabilities
- Review dependencies

### Step 5: Generate Reports
- Create all 4 deliverables
- Prioritize issues
- Estimate effort for fixes

### Step 6: Recommend Actions
- Create improvement task list
- Suggest implementation approach
- Estimate timeline

---

## Success Criteria

Review is complete when:
- [ ] All 7 review categories completed
- [ ] All 4 deliverables generated
- [ ] Improvement tasks prioritized with effort estimates
- [ ] Dashboard shows overall status
- [ ] Critical issues identified (if any)
- [ ] Recommendations actionable and specific

---

## Execution

Expected duration: 1.5 days
Format: Detailed written reports + actionable task list
Next step: Execute improvement tasks via SubAgents (if issues found)
```

---

### Prompt 2: 特定カテゴリの詳細レビュー

**使用タイミング**: 特定の懸念事項がある場合

**改善版プロンプト**:

```
# Targeted Quality Review: [Category Name]

## Context
- **Phase**: Phase [N]
- **Focus Area**: [Performance / Testing / Security / Documentation]
- **Trigger**: [Specific concern or requirement]
- **Target Files**: [List specific files]

## Specific Review Request

### [Category Name] Deep Dive

**Specific Questions to Answer**:
1. [Question 1 - specific, measurable]
2. [Question 2 - specific, measurable]
3. [Question 3 - specific, measurable]

**Acceptance Criteria**:
- [Criterion 1 with threshold]
- [Criterion 2 with threshold]
- [Criterion 3 with threshold]

**Analysis Required**:
- [Specific analysis 1]
- [Specific analysis 2]

**Deliverables**:
1. [Specific deliverable 1]
2. [Specific deliverable 2]

## Example: Performance Deep Dive

**Specific Questions**:
1. Is Memory.search() optimized and <100ms for 10K entries?
2. Are there performance tests covering 100, 1K, 10K, 100K entries?
3. What are the bottlenecks in the critical path (add → search → update)?

**Acceptance Criteria**:
- Memory.search(): <100ms for 10K entries (p95)
- Memory.add(): <50ms (p95)
- Migration: <1s for 1K entries
- Performance tests: 100% coverage of critical operations

**Analysis Required**:
- Profile Memory.search() with cProfile
- Benchmark with varying data sizes (100, 1K, 10K, 100K)
- Identify O(n²) algorithms
- Check for caching opportunities
- Memory usage profiling

**Deliverables**:
1. Benchmark results table (operation × data size)
2. Profiling report with bottlenecks highlighted
3. Optimization recommendations with estimated impact
4. Missing performance tests list
```

---

### Prompt 3: 改善タスク実行用

**使用タイミング**: Review Agent が問題を発見した後

**改善版プロンプト**:

```
# Code Improvement Task: [Issue Title]

## Issue Context
- **Issue ID**: [Issue number from review]
- **Severity**: [Critical / High / Medium / Low]
- **Category**: [Performance / Testing / Security / Code Quality / Documentation]
- **Discovered in**: Phase [N] Quality Review
- **Affected Files**: [List files]

## Problem Description

### Current State
- **What's wrong**: [Specific problem description]
- **Evidence**: [Benchmark results, test failures, security scan output]
- **Impact**: [User impact, performance impact, security risk]

Example:
```
Current: Migration takes 2.5s for 1,000 entries
Target: <1s for 1,000 entries
Evidence: pytest benchmark shows 2.5s average (pytest-benchmark results attached)
Impact: Poor UX for users with large KB/Task databases (>1000 entries)
```

### Root Cause Analysis
- **Why it happens**: [Technical explanation]
- **Contributing factors**: [Design decisions, algorithmic choices, missing optimizations]

Example:
```
Root cause:
1. Individual YAML write for each entry (no batching)
2. Full file rewrite for each entry (not incremental)
3. No transaction batching

Contributing factors:
- Current design: One write per add() call
- YAML library: No streaming write support used
- No caching layer
```

## Solution Approach

### Proposed Fix
1. [Step 1 with rationale]
2. [Step 2 with rationale]
3. [Step 3 with rationale]

Example:
```
1. Implement batch write mode:
   - Collect multiple entries in memory
   - Write to YAML once
   - Rationale: Reduce I/O overhead

2. Add write buffering:
   - Buffer writes for 100ms or 10 entries (whichever comes first)
   - Flush on explicit flush() or timeout
   - Rationale: Balance performance and data safety

3. Optimize YAML serialization:
   - Use faster YAML library (ruamel.yaml → yaml with C extensions)
   - Rationale: 2-3x faster serialization
```

### Alternative Approaches (Considered but not chosen)
- [Alternative 1]: [Why not chosen]
- [Alternative 2]: [Why not chosen]

### Trade-offs
- **Pros**: [Benefits of proposed fix]
- **Cons**: [Downsides, risks]
- **Risks**: [Potential issues]

## Implementation Requirements

### Code Changes
Files to modify:
1. `clauxton/core/memory_store.py`: Add batch write mode
2. `clauxton/core/memory.py`: Update add() to use batch mode
3. `clauxton/utils/migrate_to_memory.py`: Use batch mode for migration

### Testing Requirements
- [ ] Unit tests: Batch write functionality (5 tests)
- [ ] Integration tests: Migration with batch mode (3 tests)
- [ ] Performance tests: Benchmark before/after (3 benchmarks)
- [ ] Regression tests: Existing functionality still works (5 tests)

### Documentation Updates
- [ ] API docs: Document batch write mode
- [ ] Migration guide: Update performance expectations
- [ ] Changelog: Add optimization note

### Validation Criteria
Success = All criteria met:
- [ ] Migration time <1s for 1,000 entries
- [ ] All existing tests pass
- [ ] New tests added and passing
- [ ] No performance regression in other operations
- [ ] Code review passed (mypy, ruff)
- [ ] Documentation updated

## Implementation Plan

### Estimated Effort
- Development: [N hours/days]
- Testing: [N hours/days]
- Documentation: [N hours/days]
- Total: [N hours/days]

### Execution
1. Implement batch write in memory_store.py (4 hours)
2. Update memory.py to use batch mode (2 hours)
3. Modify migration script (2 hours)
4. Write tests (3 hours)
5. Run benchmarks and validate (1 hour)
6. Update documentation (1 hour)
Total: ~13 hours (~1.5 days)

### Deliverables
- [ ] Optimized code (3 files modified)
- [ ] New tests (16 tests added)
- [ ] Performance benchmarks (before/after comparison)
- [ ] Updated documentation
- [ ] Validation report (criteria checklist)

## Execution

Please implement the fix following the solution approach above.
Ensure all validation criteria are met before marking complete.
Provide benchmark comparison (before/after) in the final report.
```

---

## 使用例

### Example 1: Phase 1 完了後の包括的レビュー

```
# User実行
Prompt: Use improved Prompt 1 with Phase 1 context

# SubAgent (Review Agent 1) 実行
→ Read all Phase 1 deliverables
→ Run all 7 review categories
→ Generate 4 deliverables:
  1. Executive Summary
  2. Detailed Findings
  3. Improvement Task List (prioritized)
  4. Quality Dashboard

→ Result: 1 Critical, 2 High, 3 Medium, 5 Low issues found
```

### Example 2: パフォーマンス懸念への対応

```
# User実行
Prompt: Use improved Prompt 2 (Performance Deep Dive) with specific concerns

# SubAgent (Performance Review Agent) 実行
→ Profile Memory.search()
→ Run benchmarks (100, 1K, 10K, 100K entries)
→ Identify bottlenecks
→ Generate optimization recommendations

→ Result: Migration is bottleneck (2.5s for 1K entries)
```

### Example 3: 改善タスクの実行

```
# User実行
Prompt: Use improved Prompt 3 for migration optimization

# SubAgent (Improvement Agent) 実行
→ Implement batch write mode
→ Add tests
→ Run benchmarks
→ Update docs
→ Validate criteria

→ Result: Migration now 0.8s for 1K entries (✅ <1s target met)
```

---

## まとめ

### 改善の効果

| 項目 | 元のプロンプト | 改善版プロンプト |
|------|-------------|---------------|
| **明確性** | ❌ 曖昧 | ✅ 具体的 |
| **コンテキスト** | ❌ 不明確 | ✅ 明示的 |
| **期待成果物** | ❌ 不明確 | ✅ 4種類定義 |
| **実行可能性** | ❌ 低い | ✅ 高い |
| **優先順位** | ❌ なし | ✅ あり |
| **工数見積もり** | ❌ なし | ✅ あり |

### 推奨使用方法

1. **Phase完了後**: Prompt 1 (包括的レビュー)
2. **特定懸念がある場合**: Prompt 2 (カテゴリ別詳細レビュー)
3. **問題発見後**: Prompt 3 (改善タスク実行)

---

**Last Updated**: 2025-11-03
**Status**: ✅ Ready for Use
**Next Action**: Use Prompt 1 after Phase 1 completion (Day 12)
