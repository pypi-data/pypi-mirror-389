# Daily Workflow Guide (v0.11.1)

**NEW in v0.11.1**: Streamlined commands for daily productivity tracking and workflow management.

This guide shows you how to use Clauxton's v0.11.1 features to manage your workday from morning to evening.

---

## 🌅 Morning Routine

### Start Your Day with `clauxton morning`

The `morning` command provides an interactive briefing to plan your day:

```bash
clauxton morning
```

**What it does:**
1. Shows yesterday's completed tasks (wins!)
2. Suggests today's tasks based on priority and dependencies
3. Offers to set focus interactively
4. Helps you start the day with clear priorities

**Example Output:**
```
☀️  Good Morning! Let's plan your day.

✅ Yesterday's Wins:
  • Implement authentication API
  • Write unit tests
  • Code review

📋 Suggested Tasks for Today:
  1. [HIGH] Design payment system
  2. [HIGH] Implement payment API
  3. [MEDIUM] Update documentation

Would you like to set focus on one of these? (y/n)
```

---

## 💼 During the Day

### Quick Task Creation with Instant Focus

Create a task and start working immediately:

```bash
clauxton task add --name "Implement payment API" --priority high --estimate 3 --start
```

The `--start` flag:
- Creates the task
- Sets it as your current focus
- Updates status to `in_progress`

All in one command!

### Taking Breaks

Record interruptions and breaks:

```bash
# Quick pause
clauxton pause "Meeting"

# Pause with notes
clauxton pause "Lunch break" --note "Back at 1pm"

# View pause history
clauxton pause --history
```

**Why track pauses?**
- Understand time spent on actual work vs. interruptions
- Identify patterns in your workflow
- Better time estimation

### Resuming Work

Get back on track after a break:

```bash
clauxton resume
```

**What it shows:**
- Your current focus task
- Recent in-progress tasks
- Last activity time
- Suggested next actions

**With yesterday's context:**
```bash
clauxton resume --yesterday
```

Shows yesterday's work too, useful for Monday mornings!

---

## 🔍 Finding Information

### Unified Search

Search across KB, Tasks, and Files in one command:

```bash
# Search everything
clauxton search "authentication"

# Search with filters
clauxton search "API" --kb-only
clauxton search "bug" --tasks-only
clauxton search "function" --files-only

# Custom result limit
clauxton search "test" --limit 10
```

**Use cases:**
- "What did we decide about authentication?" → Searches KB
- "What tasks involve API?" → Searches tasks
- "Where is the authenticate function?" → Searches files

---

## 🌆 End of Day

### Daily Summary

Review your accomplishments:

```bash
clauxton daily
```

**What it shows:**
- ✅ Completed tasks today
- ⏱️  Time tracking (estimated vs. actual)
- 📋 Tasks in progress
- 📚 KB entries created
- 🎯 Tomorrow's priorities

**Example Output:**
```
📅 Daily Summary - Today

✅ Completed Today (3):
  • TASK-001: Implement payment API (3h est, 3.5h actual)
  • TASK-002: Write tests (2h est, 2h actual)
  • TASK-003: Code review (1h est, 0.5h actual)

  ⏱  Time Summary:
     Actual work: 6.0h
     Estimated: 6.0h
     Variance: 0.0h (0%)

📋 In Progress (1):
  • TASK-004: Update documentation

🎯 Tomorrow's Focus:
  • Deploy to staging
  • Performance testing
```

### JSON Output for Integrations

```bash
clauxton daily --json
```

Perfect for:
- Automated reports
- Time tracking systems
- Dashboards
- Slack/Discord bots

---

## 📊 Weekly Review

### Weekly Summary

See your week's progress:

```bash
clauxton weekly

# Last week
clauxton weekly --week -1

# JSON output
clauxton weekly --json
```

**What it shows:**
- 📈 Completed tasks this week
- ⚡ Velocity (tasks/hours per day)
- 📊 Daily breakdown
- 🎯 Trends and patterns

**Example Output:**
```
📈 Weekly Summary
   Week of Oct 21 - Oct 27, 2025

✅ Completed: 12 tasks (35.5h total)
⚡ Velocity: 2.4 tasks/day, 7.1h/day

📊 Daily Breakdown:
   Mon: 3 tasks (8h)
   Tue: 2 tasks (6h)
   Wed: 3 tasks (9h)
   Thu: 2 tasks (7h)
   Fri: 2 tasks (5.5h)

🎯 Most Productive: Wednesday (3 tasks, 9h)
```

---

## 📉 Trend Analysis

### Productivity Trends

Analyze your productivity over time:

```bash
# Last 30 days (default)
clauxton trends

# Custom period
clauxton trends --days 7
clauxton trends --days 90
```

**What it shows:**
- 📊 Daily task completion trends
- ⏱️  Time investment patterns
- 🎯 Productivity insights
- 📈 Week-over-week comparisons

**Insights you might see:**
- "Peak productivity: Tuesdays and Wednesdays"
- "Velocity increasing: +15% vs. last week"
- "Focus sessions average: 3.2 hours"

---

## 🔄 Complete Daily Workflow Example

Here's a full day using v0.11.1 features:

```bash
# 9:00 AM - Start your day
clauxton morning
# → Select "Design payment system" and set focus

# 9:15 AM - Start working (already focused!)
# ... coding ...

# 10:30 AM - Quick status check
clauxton focus
# → Shows: Working on TASK-005 for 1h 15m

# 12:00 PM - Lunch break
clauxton pause "Lunch"

# 1:00 PM - Resume work
clauxton resume
# → Shows where you left off

# 2:00 PM - New urgent task
clauxton task add --name "Fix production bug" --priority critical --start
# → Switches focus to new task

# 3:30 PM - Meeting
clauxton pause "Team meeting"

# 4:30 PM - Back to work
clauxton resume

# 5:30 PM - End of day review
clauxton daily
# → See what you accomplished

# Friday 5:30 PM - Week review
clauxton weekly
# → Review the whole week
```

---

## 💡 Pro Tips

### 1. Morning Planning

**Set a routine:**
```bash
# Create an alias
alias gm='clauxton morning'

# Use it every morning
gm
```

### 2. Pause Tracking

**Be specific with pause reasons:**
```bash
clauxton pause "Code review with Sarah"
clauxton pause "Production incident"
clauxton pause "1-on-1 with manager"
```

Later, use `--history` to see patterns.

### 3. Search Power

**Use specific queries:**
```bash
# Good
clauxton search "JWT authentication implementation"

# Less effective
clauxton search "auth"
```

### 4. JSON for Automation

**Daily Slack update:**
```bash
daily_summary=$(clauxton daily --json | jq '.summary')
# Post to Slack
```

### 5. Weekly Reflection

**Every Friday:**
```bash
clauxton weekly
clauxton trends --days 7
```

Review trends and plan next week.

---

## 🎯 Workflow Patterns

### Pattern 1: Feature Development

```bash
# Monday morning
clauxton morning  # Plan the week

# Start feature
clauxton task add --name "Implement user profile" --estimate 8 --start

# Track progress
clauxton pause "Design review"
clauxton resume

# Complete
clauxton task update TASK-001 --status completed

# End of week
clauxton weekly
```

### Pattern 2: Bug Fixing

```bash
# Urgent bug
clauxton task add --name "Fix payment bug" --priority critical --start

# Quick search for context
clauxton search "payment"

# After fix
clauxton daily  # Log the work
```

### Pattern 3: Research

```bash
# Document findings
clauxton kb add
# Title: "API Authentication Research"
# Category: decision
# Content: "Evaluated OAuth2 vs JWT..."

# Create follow-up task
clauxton task add --name "Implement chosen auth" --start
```

---

## 🚀 Next Steps

Now that you understand the daily workflow:

1. **Set up your routine**: Use `morning` every day for a week
2. **Track interruptions**: Use `pause` to understand your time
3. **Weekly reviews**: Use `weekly` and `trends` every Friday
4. **Optimize**: Find patterns and improve your workflow

**See also:**
- [Task Management Guide](task-management-guide.md)
- [Configuration Guide](configuration-guide.md)
- [MCP Integration Guide](MCP_INTEGRATION_GUIDE.md)

---

**Questions or feedback?**
Open an issue at: https://github.com/nakishiyaman/clauxton/issues
