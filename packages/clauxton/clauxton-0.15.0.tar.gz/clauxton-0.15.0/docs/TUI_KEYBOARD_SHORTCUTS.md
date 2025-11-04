# Clauxton TUI Keyboard Shortcuts

**Quick Reference Card** - v0.14.0

Print this page for a handy reference while using Clauxton TUI.

---

## General Navigation

| Key | Action | Scope |
|-----|--------|-------|
| `Tab` | Focus next widget | Global |
| `Shift+Tab` | Focus previous widget | Global |
| `↑` / `k` | Move up | Global |
| `↓` / `j` | Move down | Global |
| `←` / `h` | Move left / Focus left panel | Global |
| `→` / `l` | Move right / Focus right panel | Global |
| `Home` / `gg` | Jump to top | Global |
| `End` / `G` | Jump to bottom | Global |
| `Page Up` | Scroll up by page | Global |
| `Page Down` | Scroll down by page | Global |

---

## Application Control

| Key | Action | Scope |
|-----|--------|-------|
| `q` | Quit application | Global |
| `Ctrl+C` | Force quit | Global |
| `r` | Refresh current view | Global |
| `F1` / `?` | Show help modal | Global |
| `Esc` | Close modal / Cancel action | Global |

---

## Search & Query

| Key | Action | Scope |
|-----|--------|-------|
| `/` | Open query modal (Normal mode) | Global |
| `Ctrl+F` | Open query modal (Normal mode) | Global |
| `Ctrl+A` | Switch to AI mode | Query Modal |
| `Ctrl+P` | Switch to File mode | Query Modal |
| `Ctrl+S` | Switch to Symbol mode | Query Modal |
| `Enter` | Execute search / Select result | Query Modal |
| `Tab` | Next autocomplete suggestion | Query Modal |
| `Shift+Tab` | Previous autocomplete suggestion | Query Modal |
| `Esc` | Close query modal | Query Modal |

---

## Quick Actions

| Key | Action | Scope |
|-----|--------|-------|
| `a` | Ask AI (open query in AI mode) | Dashboard |
| `s` | Show/hide AI suggestions panel | Dashboard |
| `n` | New task (future feature) | Dashboard |
| `e` | New KB entry (future feature) | Dashboard |

---

## Knowledge Base Browser

| Key | Action | Scope |
|-----|--------|-------|
| `Enter` | Expand/collapse category or view entry | KB Browser |
| `Space` | Expand/collapse category | KB Browser |
| `→` | Expand category | KB Browser |
| `←` | Collapse category | KB Browser |
| `r` | Refresh KB entries | KB Browser |

---

## Content Viewer

| Key | Action | Scope |
|-----|--------|-------|
| `↑` / `k` | Scroll up | Content Viewer |
| `↓` / `j` | Scroll down | Content Viewer |
| `Page Up` | Scroll up by page | Content Viewer |
| `Page Down` | Scroll down by page | Content Viewer |
| `Home` | Jump to top | Content Viewer |
| `End` | Jump to bottom | Content Viewer |

---

## AI Suggestions Panel

| Key | Action | Scope |
|-----|--------|-------|
| `s` | Toggle panel visibility | Dashboard |
| `r` | Refresh suggestions | Suggestions Panel |
| `Enter` | Act on selected suggestion | Suggestions Panel |
| `↑` / `k` | Navigate up | Suggestions Panel |
| `↓` / `j` | Navigate down | Suggestions Panel |

---

## Vim-Style Navigation (Optional)

| Key | Action | Scope |
|-----|--------|-------|
| `h` | Focus left panel | Global |
| `l` | Focus right panel | Global |
| `j` | Move down | Global |
| `k` | Move up | Global |
| `gg` | Jump to top | Global |
| `G` | Jump to bottom | Global |
| `w` | Next word (future) | Global |
| `b` | Previous word (future) | Global |

---

## Help Modal

| Key | Action | Scope |
|-----|--------|-------|
| `F1` | Show help | Global |
| `?` | Show help | Global |
| `Esc` | Close help | Help Modal |
| `q` | Close help | Help Modal |
| `↑/↓` | Scroll help | Help Modal |

---

## Query Modes

### Normal Mode (Default)
- **Purpose**: Search Knowledge Base and Tasks
- **Usage**: Type query and press Enter
- **Results**: Ranked by TF-IDF relevance
- **Autocomplete**: KB titles, tags, task names

### AI Mode (`Ctrl+A`)
- **Purpose**: Ask questions in natural language
- **Usage**: Type question and press Enter
- **Results**: AI-generated response
- **Context**: Uses KB and project context

### File Mode (`Ctrl+P`)
- **Purpose**: Fast file search
- **Usage**: Type filename or path fragment
- **Results**: Matching files (cached)
- **Autocomplete**: File paths

### Symbol Mode (`Ctrl+S`)
- **Purpose**: Search code symbols
- **Usage**: Type class/function name
- **Results**: Symbol definitions
- **Languages**: Python, JavaScript, TypeScript, etc.

---

## Context-Specific Shortcuts

### When Query Modal is Open
- `Enter` - Execute search or select result
- `Esc` - Close modal
- `Ctrl+A/P/S` - Switch search mode
- `Tab` - Next autocomplete suggestion
- `↑/↓` - Navigate results

### When Help Modal is Open
- `Esc` or `q` - Close help
- `↑/↓` - Scroll help content
- `Page Up/Down` - Scroll by page

### When Focus is on KB Browser
- `Enter` - Expand category or view entry
- `→/←` - Expand/collapse category
- `r` - Refresh KB from disk

---

## Customization

You can customize keybindings by editing:
```
~/.clauxton/keybindings.yml
```

Example custom configuration:
```yaml
keybindings:
  dashboard:
    search: "/"
    ask_ai: "a"
    suggestions: "s"
    new_task: "n"
    new_entry: "e"
    refresh: "r"

  vim_mode:
    enabled: true

  modal:
    close: "escape"
    confirm: "enter"
```

---

## Tips for Efficiency

### 1. Memorize Quick Actions
- `a` - AI query (fastest way to ask questions)
- `s` - Suggestions (quick productivity check)
- `/` - Search (most common action)

### 2. Use Vim Keys
- If you know Vim, enable vim_mode
- `hjkl` navigation is much faster
- Works consistently everywhere

### 3. Master Tab Completion
- Start typing in query modal
- Tab through suggestions
- Much faster than typing full names

### 4. Learn Modal Shortcuts
- `Ctrl+A/P/S` switches search modes instantly
- No need to close and reopen modal
- Saves multiple keystrokes

### 5. Use Focus Navigation
- `h/l` to move between panels
- Tab to cycle through all widgets
- Arrow keys for in-widget navigation

---

## Printable Cheat Sheet

```
┌────────────────────────────────────────────────────────┐
│          CLAUXTON TUI QUICK REFERENCE                 │
├────────────────────────────────────────────────────────┤
│ ESSENTIAL                                              │
│  /        Search         a        Ask AI              │
│  F1 or ?  Help           s        Suggestions         │
│  q        Quit           r        Refresh             │
│  Tab      Focus Next     Esc      Close/Cancel        │
├────────────────────────────────────────────────────────┤
│ NAVIGATION                                             │
│  ↑/↓ or j/k    Move Up/Down                          │
│  ←/→ or h/l    Move Left/Right                       │
│  Home/End      Jump to Start/End                     │
│  Page Up/Down  Scroll by Page                        │
├────────────────────────────────────────────────────────┤
│ QUERY MODAL                                            │
│  Ctrl+A    AI Mode       Enter    Search/Select      │
│  Ctrl+P    File Mode     Esc      Close Modal        │
│  Ctrl+S    Symbol Mode   Tab      Autocomplete       │
├────────────────────────────────────────────────────────┤
│ KB BROWSER                                             │
│  Enter     View Entry    →/←      Expand/Collapse    │
│  Space     Toggle        r        Refresh            │
└────────────────────────────────────────────────────────┘
```

---

## Support

For more details, see:
- **User Guide**: [TUI_USER_GUIDE.md](./TUI_USER_GUIDE.md)
- **Issues**: https://github.com/nakishiyaman/clauxton/issues
- **Docs**: https://github.com/nakishiyaman/clauxton/tree/main/docs

---

**Last Updated**: 2025-10-28 | **Version**: v0.14.0
