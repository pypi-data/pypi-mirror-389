# Filesystem MCP Server (v0.1)

A simple MCP server for filesystem operations with directory sandboxing and read-only mode support.

**Early version (0.1) - not thoroughly tested/reviewed, use with caution**

## Quick Start

Install dependencies:
```bash
git clone <repo_url>
uv sync
```

Run the server:
```bash
# Normal mode - full filesystem access
uv run main.py /path/to/allowed/directory

# Read-only mode - no write operations  
uv run main.py --read-only /path/to/allowed/directory
```

## Features

- Directory sandboxing (operations restricted to allowed paths)
- `--read-only` flag disables write operations
- Gitignore support for searches
- Human-readable error messages

## Usage Examples

### Normal Mode
```bash
uv run main.py ~/projects
# Provides: create_file, delete_file, move_file, edit_file, create_directory + read tools
```

### Read-Only Mode  
```bash
uv run main.py --read-only ~/projects
# Provides only: read_text_file, list_directory, search_files, grep, directory_tree
```

### Multiple Directories
```bash
uv run main.py /home/user/docs /tmp/workspace
uv run main.py --read-only /var/log /etc/config
```

## Available Tools

**Read Operations (always available):**
- `read_text_file` - Read file contents
- `list_directory` - List directory contents  
- `directory_tree` - JSON directory structure
- `search_files` - Find files by pattern
- `grep` - Search text in files
- `read_multiple_files` - Bulk file reading

**Write Operations (disabled in `--read-only`):**
- `create_file` - Create new files
- `delete_file` - Delete files
- `move_file` - Move/rename files
- `edit_file` - Edit file contents
- `create_directory` - Create directories

## Dependencies

From `pyproject.toml`:
- `fastmcp>=2.11.2` - MCP framework
- `pathspec>=0.12.1` - Gitignore patterns

## Security Notes

- All paths resolved with `Path.resolve()` to prevent traversal
- Operations restricted to allowed directories only
- Binary files rejected for text operations