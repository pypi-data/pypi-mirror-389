# lablog 🐶

Your loyal lab companion - automatically tracking your research workflow so you never lose context.

Research workflow memory system - never lose context when switching between projects.

## What is lablog?

lablog helps researchers track experiments, code changes, and todos across multiple projects. When you return to a project after weeks or months, `lablog recap` instantly reconstructs what you were working on and what's next.

**Powered by Claude Code**: lablog integrates with Claude Code to provide AI-powered script analysis, change summaries, and intelligent insights - all using your existing Claude Code subscription (no extra API costs!).

## Features

- 📝 **Experiment logging**: Track what you're running and why
- 🎯 **Smart todos**: Context-aware task tracking with priority support
- 🤖 **AI-powered analysis**: Automatic Claude enhancement of notes, todos, and recaps
- 🔄 **Seamless integration**: Automatically tracks SLURM jobs (sbatch) and git commits
- 📊 **Intelligent recaps**: AI-enhanced summaries of your recent work
- 🌐 **Cross-project**: Works across multiple repos
- 💾 **Private storage**: Logs stored in `~/.config/lablog/`, not in git

## Installation

```bash
pip install lablog
```

Or install from source:

```bash
git clone https://github.com/Linskii/lablog.git
cd lablog
pip install -e .
```

## Quick Start

### Initial Setup

```bash
lablog init
```

This interactive setup will:
- Detect if Claude Code is available and configure AI features
- Set up shell hooks for automatic logging of sbatch and git commits
- Configure your preferences

### Seamless Workflow

Once set up with hooks, lablog tracks everything automatically:

```bash
# Jobs are logged automatically
sbatch jobs/train.sh

# Git commits are logged automatically with AI analysis
git commit -m "Fix memory leak in data loader"

# Check what you've been working on
lablog recap
```

### Manual Logging

You can also log things explicitly:

```bash
# Add a quick note
lablog note "Baseline achieved 0.85 AUROC"

# Add a todo (optionally with priority)
lablog todo "Check preprocessing against paper"
lablog todo "Fix critical bug in training loop" --priority high

# Interactive todo management
lablog todo -l
```

### Bypass AI Enhancement

Use the `-r` flag to skip AI enhancement when you want raw, unprocessed entries:

```bash
lablog note "Quick observation" -r
lablog todo "Fast task" -r
```

## Usage

### Recap

View your recent activity with AI-enhanced insights:

```bash
lablog recap              # Last 7 days
lablog recap --days 30    # Last 30 days
lablog recap --todos-only # Just show active todos
```

If Claude Code is enabled, recaps automatically include:
- AI summary of what you were working on
- Analysis of code changes and experiments
- Job status with output file checking
- Outstanding todos

### Todo Management

```bash
# Add todos
lablog todo "Implement attention mechanism"
lablog todo "Fix memory leak" --priority high

# Interactive management (arrow keys + space to toggle)
lablog todo -l
```

### Archive Management

Keep your logs clean by archiving old entries:

```bash
# Merge old entries into a summary
lablog merge --from-date 2025-10-01 --to-date 2025-10-31

# Archive entries by date or type
lablog clear
lablog clear --completed-todos-only

# Permanently delete old archives
lablog delete-archive --before-date 2025-09-01
```

### Multi-Project Support

```bash
# List all tracked projects
lablog projects

# View activity across all projects
lablog recap --all-projects
```

## Storage

Logs are stored in `~/.config/lablog/` by default, keeping them private and accessible across projects.

### Storage Structure

```
~/.config/lablog/
├── config.json          # User preferences
└── projects/
    └── <project-hash>/
        ├── metadata.json # Project info
        ├── log.jsonl     # Notes and todos
        ├── jobs.jsonl    # SLURM job entries
        └── archive.jsonl # Archived entries
```

## Claude Code Integration

lablog uses [Claude Code](https://claude.com/claude-code) for AI-powered features:

- ✅ Uses your existing Claude Code subscription
- ✅ No additional API costs
- ✅ Works from the command line
- ✅ Fully automated

### AI Features

When Claude Code is enabled (via `lablog init`):

- **Auto-enhancement**: Notes and todos are automatically clarified and formatted
- **Script analysis**: Job submissions are analyzed for key parameters and configuration
- **Diff analysis**: Git commits are automatically summarized
- **Smart recaps**: Get AI-generated summaries of your recent work
- **Job output analysis**: Automatically check if jobs succeeded or failed

If Claude Code is not installed, lablog works perfectly - you just won't have AI features.

## License

MIT
