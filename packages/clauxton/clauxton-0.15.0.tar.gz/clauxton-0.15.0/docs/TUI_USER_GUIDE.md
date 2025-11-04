# Clauxton TUI User Guide

**Version**: v0.14.0 (Interactive TUI)
**Last Updated**: 2025-10-28

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Interface Overview](#interface-overview)
3. [Navigation Basics](#navigation-basics)
4. [Features](#features)
5. [Keyboard Shortcuts](#keyboard-shortcuts)
6. [Common Workflows](#common-workflows)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Launch the TUI

```bash
# Launch Clauxton TUI
clauxton tui

# Launch in specific directory
clauxton tui --project-root /path/to/project
```

### First Time Setup

1. **Initialize Clauxton** in your project (if not already done):
   ```bash
   clauxton init
   ```

2. **Add some knowledge entries** to get started:
   ```bash
   clauxton kb add --title "API Design" --category architecture
   ```

3. **Launch the TUI**:
   ```bash
   clauxton tui
   ```

---

## Interface Overview

The TUI is organized into several key areas:

```
┌─────────────────────────────────────────────────────────────┐
│ Header (with clock and project name)                       │
├─────────────────────┬───────────────────────────────────────┤
│                     │                                       │
│  Knowledge Base     │     Content Viewer                   │
│  Browser            │                                       │
│  (Left Panel)       │     (Center Panel)                   │
│                     │                                       │
│  - Categories       │     Shows selected KB entry          │
│  - Entries          │     or task details                  │
│  - Tags             │                                       │
│                     │                                       │
├─────────────────────┴───────────────────────────────────────┤
│                                                             │
│  AI Suggestions Panel                                      │
│  (Bottom Panel)                                            │
│                                                             │
│  - Context-aware suggestions                               │
│  - Auto-refresh every 30s                                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Status Bar: Focus indicator | Stats | Help (F1)           │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Knowledge Base Browser (Left Panel)
- **Tree View**: Hierarchical display of KB entries organized by category
- **Expandable Categories**: Click or press Enter to expand/collapse
- **Entry Selection**: Click or press Enter to view full content
- **Visual Indicators**: Icons for categories and entries

#### 2. Content Viewer (Center Panel)
- **Title Display**: Shows entry/task title
- **Metadata**: Category, tags, timestamps
- **Content**: Full markdown-rendered content
- **Scrollable**: Use arrow keys or mouse wheel

#### 3. AI Suggestions Panel (Bottom Panel)
- **Context-Aware**: Suggestions based on recent activity
- **Auto-Refresh**: Updates every 30 seconds
- **Actionable**: Click to act on suggestions
- **Expandable**: Toggle visibility with `s` key

#### 4. Status Bar (Bottom)
- **Focus Indicator**: Shows current focused widget
- **Statistics**: File count, entry count, task count
- **Help Shortcut**: Press F1 or ? for help

---

## Navigation Basics

### Movement

**Standard Navigation:**
- `↑/↓` or `j/k` - Move up/down in lists
- `←/→` or `h/l` - Move between panels
- `Tab` - Focus next widget
- `Shift+Tab` - Focus previous widget
- `Home/End` - Jump to start/end of list
- `Page Up/Down` - Scroll by page

**Vim-Style Navigation:**
- `h` - Move focus left
- `l` - Move focus right
- `j` - Move down in lists
- `k` - Move up in lists
- `gg` - Jump to top
- `G` - Jump to bottom

### Widget Focus

The TUI uses a focus system to determine which widget receives input:

1. **KB Browser** (default focus on startup)
2. **Content Viewer**
3. **AI Suggestions Panel**

**Focus Indicators:**
- Colored border around focused widget
- Status bar shows "Focus: [Widget Name]"

---

## Features

### 1. Query Modal (Global Search)

**Launch**: Press `/` or `Ctrl+F`

The Query Modal is your primary search interface with multiple modes:

#### Search Modes

**Normal Mode** (default):
- Searches both Knowledge Base and Tasks
- Fast TF-IDF relevance ranking
- Usage: Type query and press Enter

**AI Mode** (`Ctrl+A`):
- AI-powered question answering
- Context-aware responses
- Usage: Ask questions in natural language

**File Mode** (`Ctrl+P`):
- Fast file search with caching
- Searches all indexed files in project
- Usage: Type filename or path fragment

**Symbol Mode** (`Ctrl+S`):
- Code symbol search (classes, functions, variables)
- Multi-language support
- Usage: Type symbol name

#### Query Modal Controls

- `Enter` - Execute search / Select result
- `↑/↓` - Navigate results
- `Esc` - Close modal
- `Ctrl+A` - Switch to AI mode
- `Ctrl+P` - Switch to File mode
- `Ctrl+S` - Switch to Symbol mode
- `Tab` - Cycle through autocomplete suggestions

#### Autocomplete

The query modal provides intelligent autocomplete:

- **KB Entries**: Suggests entry titles and tags
- **Tasks**: Suggests task names
- **Files**: Suggests file paths (cached for speed)
- **Fuzzy Matching**: Case-insensitive substring matching

### 2. Quick Actions

Fast keyboard shortcuts for common tasks:

- `a` - **Ask AI**: Open query modal in AI mode
- `s` - **Show Suggestions**: Toggle AI suggestions panel
- `n` - **New Task**: Create new task (future)
- `e` - **New Entry**: Create new KB entry (future)

### 3. Knowledge Base Browser

**Expand/Collapse**:
- `Enter` or `Space` - Toggle category expansion
- `→` - Expand category
- `←` - Collapse category

**View Entry**:
- Select entry and press `Enter`
- Content appears in center panel

**Refresh**:
- `r` - Reload KB entries from disk

### 4. AI Suggestions

**Features**:
- Context-aware suggestions based on:
  - Recent file changes
  - Open tasks
  - KB entry patterns
  - Git activity
- Auto-refresh every 30 seconds
- Click suggestions to act on them

**Controls**:
- `s` - Toggle panel visibility
- `r` - Manual refresh
- `↑/↓` - Navigate suggestions

### 5. Help System

**Launch**: Press `F1` or `?`

The Help Modal displays:
- All keyboard shortcuts organized by category
- Scope indicators (Global, Dashboard, Modal)
- Quick reference for common actions

**Categories**:
- **General**: Navigation, focus, help
- **Search**: Query modal shortcuts
- **Quick Actions**: Fast command shortcuts
- **Navigation**: Movement shortcuts
- **Vim**: Vim-style keybindings

---

## Keyboard Shortcuts

For a complete keyboard shortcuts reference, see [TUI_KEYBOARD_SHORTCUTS.md](./TUI_KEYBOARD_SHORTCUTS.md).

### Essential Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| `/` | Search | Open query modal |
| `F1` or `?` | Help | Show keyboard shortcuts |
| `q` | Quit | Exit TUI |
| `r` | Refresh | Reload data |
| `a` | Ask AI | Open AI query |
| `s` | Suggestions | Toggle AI panel |
| `h/l` | Navigate | Move left/right |
| `j/k` | Navigate | Move up/down |
| `Tab` | Focus Next | Focus next widget |
| `Esc` | Cancel | Close modal/dialog |

---

## Common Workflows

### Workflow 1: Search and View KB Entry

1. Press `/` to open query modal
2. Type search query (e.g., "api design")
3. Press `Enter` to search
4. Use `↑/↓` to navigate results
5. Press `Enter` to select entry
6. View full content in center panel

### Workflow 2: Ask AI Question

1. Press `a` (or `/` then `Ctrl+A`)
2. Type your question in natural language
3. Press `Enter`
4. View AI response in center panel

### Workflow 3: Find File Quickly

1. Press `/` then `Ctrl+P` to switch to File mode
2. Type filename or path fragment
3. Results update as you type (autocomplete)
4. Press `Enter` to open/view file

### Workflow 4: Browse KB by Category

1. Focus on KB Browser (left panel)
2. Use `↑/↓` or `j/k` to navigate categories
3. Press `Enter` or `→` to expand category
4. Navigate to entry
5. Press `Enter` to view

### Workflow 5: Review AI Suggestions

1. Check AI Suggestions panel (bottom)
2. Review context-aware suggestions
3. Click or press `Enter` on suggestion to act
4. Press `r` to manually refresh suggestions

---

## Configuration

### Theme Customization

Edit `~/.clauxton/tui_config.yml`:

```yaml
theme:
  name: "default"  # or "dark", "light", "custom"
  colors:
    primary: "#0066CC"
    secondary: "#00AA00"
    accent: "#FF6600"
```

### Keybinding Customization

Edit `~/.clauxton/keybindings.yml`:

```yaml
keybindings:
  dashboard:
    search: "/"
    ask_ai: "a"
    refresh: "r"
  vim_mode:
    enabled: true
```

### Performance Settings

```yaml
performance:
  file_cache_ttl: 300  # seconds (5 minutes)
  suggestions_refresh: 30  # seconds
  max_results: 50
```

### Autocomplete Settings

```yaml
autocomplete:
  enabled: true
  providers:
    - kb
    - tasks
    - files
  limit: 10
```

---

## Troubleshooting

### TUI Won't Launch

**Problem**: `clauxton tui` fails to start

**Solutions**:
1. Ensure Clauxton is initialized:
   ```bash
   clauxton init
   ```

2. Check Python version (3.10+ required):
   ```bash
   python --version
   ```

3. Reinstall Clauxton:
   ```bash
   pip install --upgrade clauxton
   ```

### Slow Performance

**Problem**: TUI is slow, especially file search

**Solutions**:
1. Check file cache settings (should be enabled by default)
2. Exclude large directories in `.clauxton/config.yml`:
   ```yaml
   exclude_dirs:
     - node_modules
     - .venv
     - dist
     - build
   ```

3. Reduce file cache TTL if using very large projects:
   ```yaml
   performance:
     file_cache_ttl: 600  # 10 minutes
   ```

### Keyboard Shortcuts Not Working

**Problem**: Key presses don't trigger actions

**Solutions**:
1. Check if modal is open (Esc to close)
2. Verify focus is on correct widget (Tab to cycle)
3. Check for key conflicts in `~/.clauxton/keybindings.yml`
4. Reset to default keybindings:
   ```bash
   rm ~/.clauxton/keybindings.yml
   clauxton tui
   ```

### Empty KB Browser

**Problem**: No entries shown in KB Browser

**Solutions**:
1. Add KB entries:
   ```bash
   clauxton kb add
   ```

2. Check `.clauxton/knowledge-base.yml` exists:
   ```bash
   ls -la .clauxton/
   ```

3. Manually refresh:
   - Press `r` in TUI
   - Restart TUI

### AI Suggestions Not Appearing

**Problem**: Suggestions panel is empty

**Solutions**:
1. Ensure project has Git history and KB entries
2. Wait for auto-refresh (30 seconds)
3. Manually refresh with `r` key
4. Check logs:
   ```bash
   tail -f ~/.clauxton/logs/tui.log
   ```

### Unicode/Emoji Display Issues

**Problem**: Special characters display as boxes

**Solutions**:
1. Ensure terminal supports UTF-8:
   ```bash
   echo $LANG  # Should show UTF-8
   export LANG=en_US.UTF-8
   ```

2. Use a modern terminal emulator:
   - iTerm2 (macOS)
   - Windows Terminal (Windows)
   - GNOME Terminal (Linux)

3. Install a font with good Unicode support:
   - Cascadia Code
   - JetBrains Mono
   - Fira Code

---

## Advanced Features

### Custom Themes (Coming Soon)

Future versions will support:
- Custom color schemes
- Layout customization
- Widget positioning

### Plugins (Planned)

Future plugin system will allow:
- Custom widgets
- Custom search providers
- Custom autocomplete sources
- Integration with external tools

---

## Tips and Best Practices

### 1. Organize Your Knowledge Base

- Use consistent category naming
- Tag entries liberally for better search
- Keep entry titles concise and descriptive
- Update entries regularly

### 2. Leverage Autocomplete

- Start typing immediately after opening query modal
- Use Tab to cycle through suggestions
- Autocomplete works with partial matches

### 3. Use Quick Actions

- Memorize quick action keys (a, s, n, e)
- Much faster than menu navigation
- Context-aware (work in relevant screens)

### 4. Master Vim Navigation (Optional)

- If you're a Vim user, enable vim_mode
- Much faster than arrow keys
- Works consistently across all widgets

### 5. Monitor AI Suggestions

- Check suggestions regularly
- Act on high-priority suggestions
- Dismiss irrelevant ones to improve future suggestions

### 6. Keep Cache Fresh

- Refresh manually after major changes (r key)
- Restart TUI after adding many files
- Cache automatically refreshes based on TTL

---

## Feedback and Support

- **Issues**: https://github.com/nakishiyaman/clauxton/issues
- **Discussions**: https://github.com/nakishiyaman/clauxton/discussions
- **Documentation**: https://github.com/nakishiyaman/clauxton/tree/main/docs

---

## What's Next?

**Upcoming Features (v0.15.0 - Web Dashboard)**:
- Browser-based interface
- Real-time collaboration
- Advanced visualizations
- Mobile-friendly design

**Stay Updated**:
```bash
# Check for updates
pip install --upgrade clauxton

# View changelog
clauxton changelog
```
