"""
Author: Preston Harrison
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠿⠿⠿⠿⠿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠻⠿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⡀⠀⢀⠀⠙⣿⣿
⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⣠⣴⣶⣶⣶⣶⣿⣿⣿⣿⣿⣿⣿⣷⡌⣿⣿
⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⣴⣿⣿⣿⣿⣿⣿⣻⣿⣿⣿⡿⣿⣿⣿⣿⡜⣿
⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⣷⢿⣿⣿⣇⣿⣿⣿⣿⣧⣿
⣿⣿⣿⣿⣿⣿⣿⡇⡆⠀⠀⣸⣿⣯⡉⠙⠛⠿⣿⣿⢺⣿⣿⡇⢿⡿⠿⠛⠉⣿
⣿⣿⣿⣿⣿⣿⣿⢁⡟⣀⣘⣛⣛⡛⢩⣤⣤⣤⣤⣀⠻⠿⠿⡇⢊⣀⣐⣚⡃⢻
⣿⣿⣿⣿⣿⣿⣿⠸⣧⣽⣿⣿⣿⡇⢼⠰⠀⠈⠙⣻⠆⣾⣷⡆⢘⡋⠉⣽⡇⢸
⣿⣿⣿⣿⣿⣿⣿⡅⣿⣿⣿⣿⣿⣧⣬⣉⣂⣚⣛⢋⣠⣿⣿⣿⢀⡐⢀⢛⡃⣸
⣿⣿⣿⣿⣿⣿⣿⣧⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢸⣿⣿⣿⣿⡘⣿⣿⣿⡇⣿
⣿⣿⣿⣿⣿⣿⣿⣿⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⠩⡿⠛⢿⠿⢃⣿⣿⡿⢣⣿
⣿⣿⣿⣿⣿⣿⣿⣿⢸⣿⣿⡿⣿⣿⣿⣿⣿⡿⣸⡷⠾⠿⣿⢶⡇⣿⡿⣡⣿⣿
⣿⣿⣿⣿⣿⣿⣿⡿⢸⣿⣿⡇⣿⣿⣿⣿⣿⢣⣁⠬⣽⣿⣒⠓⣁⠿⣡⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⠇⣿⣿⣿⣵⣿⣿⣿⣿⣿⣿⣿⣷⢖⣉⢱⣾⡟⣴⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⢏⣾⣿⣿⢟⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⣋⣭⣾⣿⣿⣿⣿⣿
⣿⣿⡿⢟⣛⣁⣾⣿⣟⣣⣿⣿⣿⣿⣿⣿⣿⣿⣯⣯⣥⣿⣬⣝⣛⣛⣛⣛⡻⠿
⣶⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣭⣝⠻⠟⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿

Filesystem MCP Server (fs_mcp.py)

Start with:
    uv run fs_mcp.py /allowed/dir1 /allowed/dir2 ...

If no directories are passed, the current working directory is the sole allowed root.

Every tool guarantees that all paths stay within the allowed roots (resolved via
Path.resolve(), preventing traversal or symlink escapes).  Errors are captured
and returned as human-readable strings so the LLM sees messages instead of stack
traces.

Requires:
    fastmcp   -  pip install fastmcp
    pathspec  -  pip install pathspec
"""

from __future__ import annotations

import argparse
import difflib
import fnmatch
from itertools import islice
import json
import os
import re
from pathlib import Path
import sys
from typing import Dict, List, Optional

from fastmcp import FastMCP
import pathspec

mcp = FastMCP("Filesystem MCP")

# --------------------------------------------------------------------------- #
#  Configuration and allowed-directory handling
# --------------------------------------------------------------------------- #

ALLOWED_DIRS: List[Path] = []
READ_ONLY_MODE: bool = False


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filesystem MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="If no directories are specified, the current working directory is used.",
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        help="Enable read-only mode (disables write operations like create, delete, move, edit)",
    )
    parser.add_argument(
        "directories",
        nargs="*",
        help="Allowed directory roots for filesystem operations",
    )
    return parser.parse_args()


def _init_config() -> None:
    global READ_ONLY_MODE
    args = _parse_args()
    READ_ONLY_MODE = args.read_only

    roots = args.directories or [os.getcwd()]
    for p in roots:
        root = Path(p).resolve()
        if not root.exists():
            root.mkdir(parents=True, exist_ok=True)
        ALLOWED_DIRS.append(root)


def main():
    """Main entry point for the MCP server."""
    _init_config()

    # Only print debug info to stderr to avoid interfering with MCP protocol
    import sys
    print("Allowed directories:", file=sys.stderr)
    for dir in ALLOWED_DIRS:
        print("- ", dir, file=sys.stderr)

    if READ_ONLY_MODE:
        print("Running in READ-ONLY mode - write operations disabled", file=sys.stderr)

    mcp.run(show_banner=False)

_init_config()


def _resolve(path: str | Path) -> Path:
    """Return an absolute, symlink-resolved Path inside one of ALLOWED_DIRS."""
    p = Path(path)
    if not p.is_absolute():
        # relative paths are resolved against the first allowed root
        p = ALLOWED_DIRS[0] / p
    rp = p.resolve()
    for root in ALLOWED_DIRS:
        try:
            rp.relative_to(root)
            return rp
        except ValueError:
            continue
    raise PermissionError("Path outside allowed directories")


def _is_text(path: Path, sample: int = 2048) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(sample)
        chunk.decode("utf-8")
        return True
    except Exception:
        return False


def _ignore_spec(directory: Path) -> Optional[pathspec.PathSpec]:
    gitignore = directory / ".gitignore"
    if gitignore.exists():
        return pathspec.PathSpec.from_lines(
            "gitwildmatch", gitignore.read_text().splitlines()
        )
    return None


def _skip_ignored(
    file: Path, root: Path, spec_cache: Dict[Path, Optional[pathspec.PathSpec]]
) -> bool:
    """Return True if *file* should be ignored due to a .gitignore in *root*."""
    if root not in spec_cache:
        spec_cache[root] = _ignore_spec(root)
    spec = spec_cache[root]
    if not spec:
        return False
    try:
        rel = file.relative_to(root)
    except ValueError:
        return False

    for pattern in DEFAULT_IGNORE_FILES:
        if rel.match(pattern):
            return True

    return spec.match_file(str(rel))


def _human_error(exc: Exception, action: str) -> str:
    """Convert an exception to a human-readable error message for LLM consumption."""
    error_type = type(exc).__name__
    if isinstance(exc, FileNotFoundError):
        return f"Error {action}: file or directory not found - {exc}"
    elif isinstance(exc, PermissionError):
        return f"Error {action}: permission denied - {exc}"
    elif isinstance(exc, FileExistsError):
        return f"Error {action}: file already exists - {exc}"
    elif isinstance(exc, IsADirectoryError):
        return f"Error {action}: path is a directory, not a file - {exc}"
    elif isinstance(exc, NotADirectoryError):
        return f"Error {action}: path is not a directory - {exc}"
    elif isinstance(exc, OSError):
        return f"Error {action}: system error ({error_type}) - {exc}"
    else:
        return f"Error {action}: {error_type} - {exc}"


GREP_IGNORE_FILES = [
    "*.lock",
    "package-lock.json",
]

DEFAULT_IGNORE_FILES = [".*/"]

# --------------------------------------------------------------------------- #
#  MCP tools
# --------------------------------------------------------------------------- #


@mcp.tool
def list_allowed_directories() -> List[str]:
    """List all allowed directory roots for filesystem operations.

    Returns:
        List[str]: Absolute paths of directories the server can read/write
    """
    return [str(p) for p in ALLOWED_DIRS]


if not READ_ONLY_MODE:

    @mcp.tool
    def create_file(path: str, content: str) -> str:
        """Create a new file with specified content.

        Args:
            path (str): File path to create (absolute or relative to allowed directories)
            content (str): UTF-8 text content to write to the file

        Returns:
            str: Success message with created file path, or error message if failed

        Note:
            - Fails if the file already exists
            - Creates parent directories if they don't exist
            - Path must be within allowed directory roots
        """
        try:
            rp = _resolve(path)
            rp.parent.mkdir(parents=True, exist_ok=True)
            with rp.open("x", encoding="utf-8") as f:
                f.write(content)
            return f"Created {rp}"
        except Exception as e:
            return _human_error(e, "creating file")


if not READ_ONLY_MODE:

    @mcp.tool
    def delete_file(path: str) -> str:
        """Delete a file from the filesystem.

        Args:
            path (str): File path to delete (absolute or relative to allowed directories)

        Returns:
            str: Success message with deleted file path, or error message if failed

        Note:
            - Path must be within allowed directory roots
            - Fails if file doesn't exist or cannot be deleted
        """
        try:
            rp = _resolve(path)
            rp.unlink()
            return f"Deleted {rp}"
        except Exception as e:
            return _human_error(e, "deleting file")


if not READ_ONLY_MODE:

    @mcp.tool
    def move_file(src: str, dst: str) -> str:
        """Move or rename a file from source to destination.

        Args:
            src (str): Source file path (absolute or relative to allowed directories)
            dst (str): Destination file path (absolute or relative to allowed directories)

        Returns:
            str: Success message with source and destination paths, or error message if failed

        Note:
            - Both paths must be within allowed directory roots
            - Fails if destination already exists
            - Creates parent directories for destination if needed
        """
        try:
            src_p, dst_p = _resolve(src), _resolve(dst)
            if dst_p.exists():
                return f"Error moving file: destination '{dst_p}' already exists"
            dst_p.parent.mkdir(parents=True, exist_ok=True)
            src_p.rename(dst_p)
            return f"Moved {src_p} → {dst_p}"
        except Exception as e:
            return _human_error(e, "moving file")


@mcp.tool
def read_text_file(
    path: str, fromLine: int | None = None, toLine: int | None = None
) -> str:
    """Read the contents of a UTF-8 text file, optionally within a line range.

    Args:
        path (str): File path to read (absolute or relative to allowed directories)
        fromLine (int, optional): Starting line number (1-indexed, inclusive)
        toLine (int, optional): Ending line number (1-indexed, inclusive)

    Returns:
        str: File contents as text, or error message if failed

    Note:
        - Path must be within allowed directory roots
        - Only reads UTF-8 text files (binary files will return error)
        - If line range specified, returns only those lines
        - Line numbers are 1-indexed
    """
    try:
        rp = _resolve(path)
        if not _is_text(rp):
            return f"Error reading file: '{rp}' is not a UTF-8 text file or is binary"
        lines = rp.read_text(encoding="utf-8").splitlines(keepends=False)
        if fromLine is None and toLine is None:
            return "\n".join(lines)
        start = (fromLine or 1) - 1
        end = toLine or len(lines)
        return "\n".join(lines[start:end])
    except Exception as e:
        return _human_error(e, "reading file")


@mcp.tool
def directory_tree(path: str) -> str:
    """Generate a plain text tree structure of a directory.

    Args:
        path (str): Directory path to generate tree for (absolute or relative to allowed directories)

    Returns:
        str: Plain text representation of directory tree, or error message if failed
    """
    try:
        rp = _resolve(path)
        spec_cache: Dict[Path, Optional[pathspec.PathSpec]] = {}
        space =  '    '
        branch = '│   '
        tee =    '├── '
        last =   '└── '

        def tree(dir_path: Path, level: int=-1, limit_to_directories: bool=False, length_limit: int=500):
            """Given a directory Path object print a visual tree structure"""
            result = ""
            dir_path = Path(dir_path) # accept string coerceable to Path
            files = 0
            directories = 0
            def inner(dir_path: Path, prefix: str='', level=-1):
                nonlocal files, directories
                # print(dir_path, _skip_ignored(dir_path, rp, spec_cache), file=sys.stderr)
                if _skip_ignored(dir_path, rp, spec_cache):
                    return
                if not level: 
                    return # 0, stop iterating
                if limit_to_directories:
                    contents = [d for d in dir_path.iterdir() if d.is_dir()]
                else: 
                    contents = list(dir for dir in dir_path.iterdir() )

                pointers = [tee] * (len(contents) - 1) + [last]
                for pointer, path in zip(pointers, contents):
                    if path.is_dir():
                        yield prefix + pointer + path.name
                        directories += 1
                        extension = branch if pointer == tee else space 
                        yield from inner(path, prefix=prefix+extension, level=level-1)
                    elif not limit_to_directories:
                        yield prefix + pointer + path.name
                        files += 1
            result += dir_path.name + "\n"
            iterator = inner(dir_path, level=level)
            for line in islice(iterator, length_limit):
                result += line + "\n"
            if next(iterator, None):
                result += f'... length_limit, {length_limit}, reached, counted:\n'
            result += f'\n{directories} directories' + (f', {files} files' if files else '') + "\n"
            return result

        return tree(rp)
    except Exception as e:
        return _human_error(e, "enumerating directory")


if not READ_ONLY_MODE:

    @mcp.tool
    def create_directory(path: str) -> str:
        """Create a directory, including any necessary parent directories.

        Args:
            path (str): Directory path to create (absolute or relative to allowed directories)

        Returns:
            str: Success message with created directory path, or error message if failed

        Note:
            - Path must be within allowed directory roots
            - Creates parent directories if they don't exist
            - No error if directory already exists
        """
        try:
            rp = _resolve(path)
            rp.mkdir(parents=True, exist_ok=True)
            return f"Ensured directory {rp}"
        except Exception as e:
            return _human_error(e, "creating directory")


@mcp.tool
def list_directory(path: str) -> str:
    """List the contents of a directory with type annotations.

    Args:
        path (str): Directory path to list (absolute or relative to allowed directories)

    Returns:
        str: Newline-separated list of entries with '[DIR]' or '[FILE]' prefixes, or error message if failed

    Note:
        - Path must be within allowed directory roots
        - Fails if path is not a directory
        - Entries are sorted alphabetically
        - Format: '[DIR] dirname' or '[FILE] filename'
    """
    try:
        rp = _resolve(path)
        if not rp.is_dir():
            return f"Error listing directory: '{rp}' is not a directory"
        out = []
        for child in sorted(rp.iterdir()):
            tag = "[DIR]" if child.is_dir() else "[FILE]"
            out.append(f"{tag} {child.name}")
        return "\n".join(out)
    except Exception as e:
        return _human_error(e, "listing directory")


@mcp.tool
def read_multiple_files(paths: List[str]) -> Dict[str, str] | str:
    """Read multiple UTF-8 text files at once and return a mapping of paths to contents.

    Args:
        paths (List[str]): List of file paths to read (absolute or relative to allowed directories)

    Returns:
        Dict[str, str] | str: Dictionary mapping absolute file paths to their contents, or error message if any file fails

    Note:
        - All paths must be within allowed directory roots
        - All files must be UTF-8 text files
        - If any file fails to read, entire operation returns error string
        - Returns dictionary for successful reads, string for errors
    """
    result: Dict[str, str] = {}
    try:
        for p in paths:
            rp = _resolve(p)
            if not _is_text(rp):
                return f"Error reading multiple files: '{rp}' is not a UTF-8 text file or is binary"
            result[str(rp)] = rp.read_text(encoding="utf-8")
        return result
    except Exception as e:
        return _human_error(e, "reading multiple files")


@mcp.tool
def search_files(dir: str, pattern: str, exclude: str | None = None) -> List[str] | str:
    """Search for files by name pattern in a directory recursively.

    Args:
        dir (str): Directory to search in (absolute or relative to allowed directories)
        pattern (str): Glob-style pattern to match file names (e.g., '*.py', 'test_*')
        exclude (str, optional): Glob-style pattern to exclude file names

    Returns:
        List[str] | str: List of matching absolute file paths, or error message if failed

    Note:
        - Directory must be within allowed directory roots
        - Searches recursively through subdirectories
        - Respects .gitignore files, and ignores hidden files and folders
        - Returns list for successful searches, string for errors
    """
    try:
        root = _resolve(dir)
        if not root.is_dir():
            return f"Error searching files: '{root}' is not a directory"
        spec_cache: Dict[Path, Optional[pathspec.PathSpec]] = {}
        matches: List[str] = []
        for file in root.rglob("*"):
            if file.is_dir():
                continue
            if exclude and fnmatch.fnmatch(file.name, exclude):
                continue
            if not fnmatch.fnmatch(file.name, pattern):
                continue
            if _skip_ignored(file, root, spec_cache):
                continue
            matches.append(str(file))
        return matches
    except Exception as e:
        return _human_error(e, "searching files")


@mcp.tool
def grep(dir: str, pattern: str, exclude: str | None = None) -> str:
    """Search for text patterns inside files using regular expressions.

    Args:
        dir (str): Directory to search in (absolute or relative to allowed directories)
        pattern (str): Regular expression pattern to search for in file contents
        exclude (str, optional): File pattern to exclude from search

    Returns:
        str: Newline-separated matches in format 'path:lineNo:\tline', or error message if failed

    Note:
        - Directory must be within allowed directory roots
        - Searches recursively through subdirectories
        - Only searches UTF-8 text files
        - Respects .gitignore files and skips common lock files
        - Each match shows file path, line number, and the matching line
        - Uses Python regular expression syntax
    """
    try:
        exclude_spec = (
            pathspec.PathSpec(
                (pathspec.patterns.gitwildmatch.GitWildMatchPattern(exclude),)
            )
            if exclude
            else None
        )
        root = _resolve(dir)
        if not root.is_dir():
            return f"Error grepping: '{root}' is not a directory"
        spec_cache: Dict[Path, Optional[pathspec.PathSpec]] = {}
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return (
                f"Error grepping: invalid regular expression pattern '{pattern}' - {e}"
            )
        hits: List[str] = []
        for file in root.rglob("*"):
            if file.is_dir():
                continue

            grep_ignore_spec = pathspec.PathSpec.from_lines(
                pathspec.patterns.gitwildmatch.GitWildMatchPattern, GREP_IGNORE_FILES
            )
            if grep_ignore_spec.match_file(file):
                continue
            if exclude_spec and exclude_spec.match_file(file):
                continue
            if _skip_ignored(file, root, spec_cache):
                continue
            if not _is_text(file):
                continue
            try:
                for idx, line in enumerate(
                    file.read_text(encoding="utf-8", errors="ignore").splitlines(), 1
                ):
                    if regex.search(line):
                        hits.append(f"{file}:{idx}:\t{line}")
            except Exception:
                continue
        return "\n".join(hits)
    except Exception as e:
        return _human_error(e, "grepping")


if not READ_ONLY_MODE:

    @mcp.tool
    def edit_file(path: str, edits: List[Dict[str, str]]) -> str:
        """Apply multiple text replacements to a file and return a unified diff.

        Args:
            path (str): File path to edit (absolute or relative to allowed directories)
            edits (List[Dict[str, str]]): List of edit operations, each with 'oldText' and 'newText' keys

        Returns:
            str: Unified diff showing changes made, or error message if failed

        Note:
            - Path must be within allowed directory roots
            - File must be a UTF-8 text file
            - Edits are applied sequentially in the order provided
            - Each 'oldText' must match exactly (first occurrence is replaced)
            - Returns unified diff format showing before/after changes
            - File is atomically updated using temporary file
            - If no changes made, returns 'No changes made.'
        """
        try:
            rp = _resolve(path)
            if not _is_text(rp):
                return (
                    f"Error editing file: '{rp}' is not a UTF-8 text file or is binary"
                )
            original = rp.read_text(encoding="utf-8")
            modified = original
            for i, edit in enumerate(edits):
                old = edit.get("oldText", "")
                new = edit.get("newText", "")
                if old not in modified:
                    return f"Error editing file: could not find text to replace in edit {i + 1}. Make sure the text matches exactly:\n{old}"
                modified = modified.replace(old, new, 1)

            if modified == original:
                return "No changes made."

            diff = "\n".join(
                difflib.unified_diff(
                    original.splitlines(),
                    modified.splitlines(),
                    fromfile=str(rp),
                    tofile=str(rp),
                    lineterm="",
                )
            )
            tmp = rp.with_suffix(rp.suffix + ".tmp")
            tmp.write_text(modified, encoding="utf-8")
            tmp.replace(rp)
            return diff
        except Exception as e:
            return _human_error(e, "editing file")


# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()
