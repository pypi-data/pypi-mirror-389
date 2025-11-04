# Workflow Examples

**Real-world workflows using Context Intelligence**

This guide provides practical workflow examples for using Clauxton's Context Intelligence features in your daily development.

---

## Table of Contents

1. [Morning Start](#morning-start)
2. [Feature Development](#feature-development)
3. [Bug Fixing](#bug-fixing)
4. [Code Review](#code-review)
5. [End of Day](#end-of-day)
6. [Team Collaboration](#team-collaboration)

---

## Morning Start

### Scenario: Starting Your Workday

**Goal**: Quickly understand where you left off and plan your day.

**Workflow**:

```bash
# 1. Navigate to project
cd ~/projects/my-app

# 2. Ask Claude Code for context
"Good morning! Where did I leave off yesterday?"
```

**What happens**:
1. Claude Code calls `get_current_context()`
2. Returns:
   - Current branch: `feature/user-auth`
   - Uncommitted changes: 3 files
   - Last activity: Yesterday 6:45 PM
   - Recent commits: "Add login form UI"

**Claude Code response**:
```
Good morning! You're on feature/user-auth branch with 3 uncommitted files:
- src/auth/login.py (modified)
- tests/test_login.py (new)
- docs/auth-flow.md (modified)

Your last commit was "Add login form UI" at 6:42 PM yesterday.

Suggestion: Review uncommitted changes and decide whether to commit or continue work.
```

**Next steps**:
```bash
# Review changes
git diff

# Continue working or commit
git add . && git commit -m "Complete login backend logic"
```

---

## Feature Development

### Scenario: Implementing a New Feature

**Goal**: Develop a feature with intelligent workflow guidance.

**Workflow**:

```bash
# 1. Create feature branch
git checkout -b feature/email-notifications

# 2. Start implementing
# ... edit files for 45 minutes ...

# 3. Ask for session analysis
"How's my work session going?"
```

**What happens**:
1. Claude Code calls `analyze_work_session()`
2. Returns:
   - Duration: 47 minutes
   - Focus score: 0.82 (high)
   - Breaks: 0
   - File switches: 6

**Claude Code response**:
```
Your session: 47 minutes with high focus (0.82).
You've modified 6 files without taking a break.

Files active:
- src/notifications/email.py
- src/notifications/templates/
- tests/test_email.py
- config/email_settings.py

You're in a good flow! Consider taking a short break after 90 minutes.
```

**Continue workflow**:

```bash
# ... work another 45 minutes ...

# 4. Check what to do next
"What should I do before committing?"
```

**What happens**:
1. Claude Code calls `predict_next_action()`
2. Returns: `run_tests` (confidence: 0.85)

**Claude Code response**:
```
Recommendation: Run tests (85% confidence)

Reasoning: You've modified 6 files including implementation and tests,
but haven't run tests yet. Run the test suite to verify your changes.

Command: pytest tests/test_email.py -v
```

**Complete workflow**:
```bash
# Run tests
pytest tests/test_email.py -v
# ✅ All tests pass

# Commit
git add .
git commit -m "feat: add email notification system

- Implement email sending via SMTP
- Add customizable templates
- Add comprehensive tests (15 tests, 100% coverage)

🤖 Generated with Claude Code"
```

---

## Bug Fixing

### Scenario: Quick Bug Fix During Development

**Goal**: Fix a bug without losing context of main work.

**Workflow**:

```bash
# Current: Working on feature branch
# Bug report arrives: "Login fails for users with special characters in email"

# 1. Check current session
"Analyze my current session"
```

**Claude Code response**:
```
Session: 62 minutes, focus: 0.76 (medium-high)
Active work: feature/payment-integration
Files modified: 8 files

You're in the middle of implementing payment integration.
```

**Decision**:
```bash
# 2. Stash current work
git stash save "WIP: payment integration"

# 3. Create bugfix branch
git checkout -b bugfix/email-special-chars

# 4. Fix bug (15 minutes)
# ... edit src/auth/validators.py ...

# 5. Test fix
pytest tests/test_auth.py::test_email_validation -v

# 6. Commit
git add .
git commit -m "fix: handle special characters in email validation"

# 7. Return to feature work
git checkout feature/payment-integration
git stash pop

# 8. Resume
"I'm back. Where was I?"
```

**Claude Code response**:
```
Welcome back! You were working on payment integration (62 minutes before bugfix).

Active files before break:
- src/payments/stripe.py
- src/payments/models.py
- tests/test_payments.py

You're about 70% done based on file changes. Continue with payment webhooks implementation.
```

---

## Code Review

### Scenario: Reviewing a Large Pull Request

**Goal**: Efficiently review changes with context awareness.

**Workflow**:

```bash
# 1. Fetch PR branch
git fetch origin
git checkout pr/user-auth-refactor

# 2. Get context
"Give me context on this branch"
```

**Claude Code response**:
```
Branch: pr/user-auth-refactor
Commits ahead of main: 12
Total changes:
- Files changed: 24
- Additions: 847 lines
- Deletions: 432 lines

Recent commits:
- "Refactor JWT token handling" (2 hours ago)
- "Add refresh token support" (3 hours ago)
- "Update authentication tests" (3 hours ago)

Key areas: Authentication, JWT, Tests
```

**Review process**:

```bash
# 3. Review changes by area
git diff main...HEAD src/auth/

# 4. Ask for analysis
"Analyze changes in the auth module"

# 5. Run tests
pytest tests/test_auth.py -v

# 6. Check prediction
"Based on this PR, what's missing?"
```

**Claude Code response**:
```
Analysis: This PR refactors authentication with JWT tokens.

Changes look good, but I notice:
- ✅ Implementation complete
- ✅ Tests added (23 new tests)
- ⚠️ Documentation not updated (docs/authentication.md)

Recommendation: Update documentation before merging.
```

---

## End of Day

### Scenario: Wrapping Up Your Workday

**Goal**: Commit work, document progress, plan tomorrow.

**Workflow**:

```bash
# 1. Check session summary
"Summarize my work today"
```

**Claude Code response**:
```
Today's Session Summary:
- Duration: 6 hours 12 minutes
- Focus score: 0.74 (medium-high)
- Breaks: 3 (lunch, coffee breaks)
- Files modified: 18 files

Major work areas:
1. Payment integration (4 hours)
   - Stripe API integration
   - Payment models
   - Webhook handling

2. Bug fixes (1.5 hours)
   - Email validation fix
   - Edge case handling

3. Documentation (45 minutes)
   - API documentation updates

Uncommitted changes: 2 files (config/stripe.py, docs/payments.md)
```

**Wrap-up**:

```bash
# 2. Check what to commit
"Should I commit before leaving?"
```

**Claude Code response**:
```
Yes, commit recommended (88% confidence).

You have 2 uncommitted files:
- config/stripe.py (Stripe API keys - ⚠️ check for secrets)
- docs/payments.md (Safe to commit)

Recommendation:
1. Review config/stripe.py for hardcoded secrets
2. Commit both files
3. Push to remote before leaving
```

**Final steps**:

```bash
# 3. Review and commit
git diff config/stripe.py
# ✅ No secrets, only configuration structure

git add .
git commit -m "chore: update Stripe configuration and docs"
git push origin feature/payment-integration

# 4. Plan tomorrow
"What should I work on tomorrow?"
```

**Claude Code response**:
```
Tomorrow's Plan:

Priority 1: Complete payment integration
- Implement error handling for failed payments
- Add retry logic for webhook failures
- Write integration tests

Priority 2: Code review
- Review PR #45 (authentication refactor)

Priority 3: Team meeting
- Prepare demo of payment integration
```

---

## Team Collaboration

### Scenario: Handing Off Work to Teammate

**Goal**: Provide comprehensive handoff with context.

**Workflow**:

```bash
# 1. Get full project context
"I need to hand off my work. Give me full context."
```

**Claude Code response**:
```
Project Handoff Context:

Branch: feature/payment-integration
Status: 70% complete

Completed:
✅ Stripe API integration
✅ Payment models (PaymentIntent, PaymentMethod)
✅ Basic webhook handling
✅ Unit tests (18 tests, 92% coverage)

In Progress:
🚧 Error handling for failed payments (50% done)
🚧 Integration tests (started, 3 tests written)

Pending:
⏳ Retry logic for webhook failures
⏳ Documentation (API docs, user guide)
⏳ Production deployment config

Files to review:
- src/payments/stripe.py (core implementation)
- src/payments/webhooks.py (webhook handlers)
- tests/test_payments.py (test suite)
```

**Create handoff document**:

```bash
# 2. Generate handoff
"Create a handoff document in docs/handoff/payment-integration.md"

# Claude Code creates:
# - Architecture overview
# - Implementation status
# - Remaining tasks
# - Known issues
# - Testing instructions
# - Deployment notes
```

**Share with teammate**:

```bash
# 3. Push branch
git push origin feature/payment-integration

# 4. Create PR (draft)
gh pr create --draft --title "WIP: Payment Integration" \
  --body "See docs/handoff/payment-integration.md for details"

# 5. Notify teammate
# Send message with PR link and handoff doc
```

---

## Tips for Effective Workflows

### Best Practices

1. **Morning check-in**: Always start with `get_current_context()`
2. **Regular analysis**: Check session every 60-90 minutes
3. **Pre-commit check**: Ask "What should I do before committing?"
4. **End-of-day wrap-up**: Summarize work and plan tomorrow
5. **Break reminders**: Take breaks when focus score drops or duration exceeds 90min

### Keyboard Shortcuts

Create bash aliases for common queries:

```bash
# .bash_aliases or .zshrc
alias morning='echo "Good morning! Where did I leave off?" | claude'
alias session='echo "Analyze my work session" | claude'
alias next='echo "What should I do next?" | claude'
alias commit-check='echo "Should I commit now?" | claude'
alias wrap-up='echo "Summarize my work today" | claude'
```

### Integration with Git Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash
# Ask Claude Code before each commit
echo "Checking with Claude Code before committing..."
claude "Should I commit these changes? Any issues to address?"
```

---

## More Examples

See also:
- [Context Intelligence Guide](CONTEXT_INTELLIGENCE_GUIDE.md) - Core concepts
- [Best Practices](BEST_PRACTICES.md) - Optimization tips
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

---

**Master these workflows to maximize your productivity with Context Intelligence!** 🎯
