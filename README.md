# ManagerAI

A task management system designed for AI assistants with intelligent deduplication and MCP server integration.

## Directory Structure

```
ManagerAI/
├── core/                    # Reusable system components (public)
│   ├── mcp/                # MCP server implementation
│   │   └── server.py       # Core server with deduplication
│   ├── templates/          # Template files for users
│   │   ├── CLAUDE.md       # AI instruction template
│   │   ├── config.yaml     # Configuration template
│   │   └── gitignore       # Gitignore template
│   └── README.md           # Core system documentation
│
├── examples/               # Example usage and workflows
│   └── (example files)
│
├── Tasks/                  # Your personal tasks (gitignored)
├── CRM/                    # Your contacts (gitignored)
├── BACKLOG.md             # Your backlog (gitignored)
├── CLAUDE.md              # Your customized instructions (gitignored)
└── config.yaml            # Your configuration (gitignored)
```

## Quick Start

### For New Users

1. **Use the setup script**:
   ```bash
   python setup.py
   ```

2. **Or manually setup**:
   ```bash
   # Create personal directories
   mkdir Tasks CRM
   
   # Copy templates
   cp core/templates/CLAUDE.md ./CLAUDE.md
   cp core/templates/config.yaml ./config.yaml
   cp core/templates/gitignore ./.gitignore
   
   # Create backlog
   touch BACKLOG.md
   ```

3. **Start the MCP server**:
   ```bash
   python core/mcp/server.py
   ```

4. **Tell your AI assistant**:
   ```
   "Read CLAUDE.md for task management instructions"
   ```

## What's What

### Core System (`core/`)
- **Public and reusable** - Safe to commit and share
- Generic MCP server with deduplication logic
- Template files for configuration
- No personal information

### Personal Data (root level)
- **Private** - Should be gitignored
- Your actual tasks, contacts, and notes
- Your customized configuration
- Never committed to public repos

### Examples (`examples/`)
- Sample workflows and use cases
- Demo tasks and configurations
- Learning resources

## Features

- 🔍 **Smart Deduplication** - Automatically detects duplicate tasks
- 🤔 **Ambiguity Detection** - Flags vague items for clarification
- 📊 **Task Organization** - Categories, priorities, and status tracking
- 👥 **CRM Integration** - Manage contacts alongside tasks
- 🔧 **MCP Server** - Reliable tool interface for AI assistants
- ⚙️ **Configurable** - Customize for your workflow

## For Contributors

The `core/` directory contains the reusable system. Contributions should:
- Not include personal information
- Be generic and configurable
- Include documentation
- Follow the existing patterns

## For Personal Use

Your personal files stay in the root directory and are gitignored:
- `Tasks/` - Your task files
- `CRM/` - Your contacts
- `BACKLOG.md` - Your notes
- `CLAUDE.md` - Your customized AI instructions
- `config.yaml` - Your configuration

## License

MIT - See LICENSE file for details.