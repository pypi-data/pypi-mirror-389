#!/usr/bin/env python3
import os
import sys
import argparse
import tempfile
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import re
import uuid


class PMMVError(Exception):
    """Base exception for PMMV errors"""
    pass


class ValidationError(PMMVError):
    """Raised when file validation fails"""
    pass


def validate_separator(sep):
    """Validate that separator is non-empty and non-whitespace"""
    if not sep or sep.isspace():
        raise ValueError("Separator must be non-empty and non-whitespace")
    return sep


def is_valid_path(path, sep):
    """Check if path contains invalid separator usage"""
    # Check for ### in the middle or end of path components
    # Valid: ###/some/path or /some/path
    # Invalid: some###/path, ###abc, abc###

    if path.startswith(sep + '/'):
        # Remove the leading separator for further checking
        check_path = path[len(sep):]
    else:
        check_path = path

    # Check if separator appears anywhere in the remaining path
    if sep in check_path:
        return False

    return True


def get_common_parent(files):
    """Get the common parent directory of all files"""
    if not files:
        return Path.cwd()

    abs_paths = [Path(f).resolve() for f in files]

    if len(abs_paths) == 1:
        return abs_paths[0].parent

    # Find common parent
    common = abs_paths[0].parent
    for p in abs_paths[1:]:
        # Find common ancestor
        while not str(p).startswith(str(common) + os.sep) and p != common:
            common = common.parent
            if common == common.parent:  # reached root
                break

    return common


def expand_path(path, sep, parent_dir):
    """Expand a path that may start with separator token"""
    if path.startswith(sep + '/'):
        # Replace ### with parent directory
        return str(parent_dir / path[len(sep) + 1:])
    return path


def create_edit_file(files, sep, short_mode):
    """Create the initial edit file content"""
    abs_files = [Path(f).resolve() for f in files]
    parent_dir = get_common_parent(files) if short_mode else None

    lines = []
    max_left_len = 0

    for f in abs_files:
        abs_path = str(f)

        if short_mode:
            # Create relative path from parent
            try:
                rel_path = f.relative_to(parent_dir)
                left = f"{sep}/{rel_path}"
            except ValueError:
                # Can't make relative, use absolute
                left = abs_path
        else:
            left = abs_path

        right = abs_path
        max_left_len = max(max_left_len, len(left))
        lines.append((left, right))

    # Align to boundary of 2 away from furthest
    alignment = ((max_left_len + 2) // 2 + 1) * 2

    result = []
    for left, right in lines:
        spaces = ' ' * (alignment - len(left))
        result.append(f"{left}{spaces}{sep} {right}")

    return '\n'.join(result) + '\n', parent_dir


def parse_edit_file(content, sep, parent_dir):
    """Parse the edited file and return list of (source, dest) tuples"""
    moves = []

    for line_no, line in enumerate(content.split('\n'), 1):
        line = line.rstrip('\n')
        if not line.strip():
            continue

        # Find separator with at least one space on each side
        pattern = r'\s+' + re.escape(sep) + r'\s+'
        parts = re.split(pattern, line)

        if len(parts) != 2:
            raise ValidationError(f"Line {line_no}: Invalid format, must have exactly one '{sep}' separator with spaces")

        dest_str, src_str = parts
        dest_str = dest_str.strip()
        src_str = src_str.strip()

        # Validate paths don't contain invalid separator usage
        if not is_valid_path(dest_str, sep):
            raise ValidationError(f"Line {line_no}: Invalid separator usage in destination path: {dest_str}")
        if not is_valid_path(src_str, sep):
            raise ValidationError(f"Line {line_no}: Invalid separator usage in source path: {src_str}")

        # Expand paths
        if parent_dir:
            dest_str = expand_path(dest_str, sep, parent_dir)
            src_str = expand_path(src_str, sep, parent_dir)

        # Convert to absolute paths
        src = Path(src_str).resolve()
        dest = Path(dest_str).resolve()

        moves.append((src, dest))

    return moves


def validate_moves(moves, use_git=False):
    """Validate that all moves are possible"""
    # Check that all source files exist
    for src, dest in moves:
        if not src.exists():
            raise ValidationError(f"Source file does not exist: {src}")
        if not src.is_file():
            raise ValidationError(f"Source is not a file: {src}")

    # Check for destination conflicts (multiple sources to same dest)
    dest_map = {}
    for src, dest in moves:
        if src == dest:
            continue  # No-op move

        if dest in dest_map:
            raise ValidationError(
                f"Multiple files being moved to same destination:\n"
                f"  {dest_map[dest]} -> {dest}\n"
                f"  {src} -> {dest}"
            )
        dest_map[dest] = src

    # Check that destinations that exist are being moved elsewhere
    for src, dest in moves:
        if src == dest:
            continue

        if dest.exists():
            # Check if this dest is a source in our moves
            dest_is_source = any(s == dest for s, d in moves)
            if not dest_is_source:
                raise ValidationError(f"Destination already exists and is not being moved: {dest}")

    # Check destination directory permissions
    for src, dest in moves:
        if src == dest:
            continue

        dest_dir = dest.parent
        if not dest_dir.exists():
            # Check if we can create it
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValidationError(f"Cannot create destination directory {dest_dir}: {e}")

        if not os.access(dest_dir, os.W_OK):
            raise ValidationError(f"No write permission for directory: {dest_dir}")

    # Git-specific validation
    if use_git:
        validate_git_moves(moves)


def validate_git_moves(moves):
    """Validate that all files are in git and moves are within same repo"""
    repos = {}

    for src, dest in moves:
        if src == dest:
            continue

        # Check if source is in a git repo
        src_repo = get_git_repo(src)
        if src_repo is None:
            raise ValidationError(f"File is not in a git repository: {src}")

        # Check if destination is in same git repo
        dest_repo = get_git_repo(dest.parent)
        if dest_repo is None:
            raise ValidationError(f"Destination is not in a git repository: {dest}")

        if src_repo != dest_repo:
            raise ValidationError(
                f"Source and destination are in different git repositories:\n"
                f"  {src} (repo: {src_repo})\n"
                f"  {dest} (repo: {dest_repo})"
            )


def get_git_repo(path):
    """Get the git repository root for a path, or None if not in a repo"""
    try:
        result = subprocess.run(
            ['git', '-C', str(path), 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def apply_moves(moves, use_git=False):
    """Apply all moves simultaneously, handling cycles"""
    # Filter out no-op moves
    actual_moves = [(src, dest) for src, dest in moves if src != dest]

    if not actual_moves:
        return

    # Create temporary directory for intermediate files
    temp_dir = Path(tempfile.mkdtemp(prefix='pmmv_'))
    temp_map = {}

    try:
        # Step 1: Move all files to temporary locations
        for src, dest in actual_moves:
            temp_name = temp_dir / str(uuid.uuid4())
            if use_git:
                subprocess.run(['git', 'mv', str(src), str(temp_name)], check=True)
            else:
                shutil.move(str(src), str(temp_name))
            temp_map[temp_name] = dest

        # Step 2: Move all files to final destinations
        for temp_path, dest in temp_map.items():
            # Ensure destination directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)

            if use_git:
                subprocess.run(['git', 'mv', str(temp_path), str(dest)], check=True)
            else:
                shutil.move(str(temp_path), str(dest))

    finally:
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def create_undo_file(moves, sep):
    """Create an undo file with inverted moves"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    undo_filename = f"{timestamp}.undo.pmmv"

    # Filter out no-op moves and invert
    undo_moves = [(dest, src) for src, dest in moves if src != dest]

    if not undo_moves:
        return None

    lines = []
    max_left_len = 0

    for left, right in undo_moves:
        max_left_len = max(max_left_len, len(str(left)))

    alignment = ((max_left_len + 2) // 2 + 1) * 2

    for left, right in undo_moves:
        spaces = ' ' * (alignment - len(str(left)))
        lines.append(f"{left}{spaces}{sep} {right}")

    with open(undo_filename, 'w') as f:
        f.write('\n'.join(lines) + '\n')

    return undo_filename


def get_editor():
    """Get the user's preferred editor"""
    editor = os.environ.get('EDITOR', os.environ.get('VISUAL', 'vi'))
    if editor in ('vi', 'vim', 'nvim'):
        os.environ['VIM_OPTIONS'] = '+set nowrap'

    return editor


def main():
    parser = argparse.ArgumentParser(
        description='PMMV - Python Mass Move: Batch rename/move files interactively'
    )
    parser.add_argument('files', nargs='*', help='Files to move/rename')
    parser.add_argument('--short', action='store_true', help='Use short format with common parent')
    parser.add_argument('--sep', default='###', help='Separator token (default: ###)')
    parser.add_argument('--git', action='store_true', help='Use git mv for moving files')

    args = parser.parse_args()

    try:
        sep = validate_separator(args.sep)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Get files from stdin if not provided as arguments
    if not args.files:
        if not sys.stdin.isatty():
            args.files = [line.strip() for line in sys.stdin if line.strip()]
        else:
            print("Error: No files specified", file=sys.stderr)
            print("Usage: pmmv [--short] [--sep SEP] [--git] <files...>", file=sys.stderr)
            print("   or: find ... | pmmv [--short] [--sep SEP] [--git]", file=sys.stderr)
            return 1

    if not args.files:
        print("Error: No files to process", file=sys.stderr)
        return 1

    # Handle case where a single directory is passed
    if len(args.files) == 1:
        dir_path = Path(args.files[0])
        if dir_path.is_dir():
            # Get all items (files and directories) in the directory
            items_in_dir = []
            for item in dir_path.iterdir():
                items_in_dir.append(str(item))

            # If we found items, use them instead of the directory itself
            if items_in_dir:
                args.files = items_in_dir
            # If no items found, keep the original behavior (treat as single file)

    # Validate files exist
    for f in args.files:
        if not Path(f).exists():
            print(f"Error: File does not exist: {f}", file=sys.stderr)
            return 1

    # Validate that we don't have conflicting paths (e.g., a directory and files inside it)
    # This prevents issues where a directory and its contents are both being moved
    if len(args.files) > 1:
        # Check if we have a mix of directories and files that could conflict
        abs_files = [Path(f).resolve() for f in args.files]

        # Check for any directory that is a parent of another file/directory
        for i, file1 in enumerate(abs_files):
            for j, file2 in enumerate(abs_files):
                if i != j and file1.is_dir() and file2.is_relative_to(file1):
                    print(f"Error: Conflicting paths detected in input files", file=sys.stderr)
                    print(f"  Directory: {file1}", file=sys.stderr)
                    print(f"  File/Directory inside: {file2}", file=sys.stderr)
                    return 1

    # Create edit file
    try:
        content, parent_dir = create_edit_file(args.files, sep, args.short)
    except Exception as e:
        print(f"Error creating edit file: {e}", file=sys.stderr)
        return 1

    # Write to temporary file and open editor
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pmmv', delete=False) as tf:
        tf.write(content)
        temp_path = tf.name

    try:
        editor = get_editor()
        subprocess.run([editor, temp_path], check=True)

        # Read edited content
        with open(temp_path, 'r') as f:
            edited_content = f.read()

        # Parse moves
        moves = parse_edit_file(edited_content, sep, parent_dir)

        # Validate moves
        validate_moves(moves, use_git=args.git)

        # Create undo file before applying changes
        undo_file = create_undo_file(moves, sep)

        # Apply moves
        apply_moves(moves, use_git=args.git)

        # Report results
        actual_moves = [(src, dest) for src, dest in moves if src != dest]
        if actual_moves:
            print(f"Successfully moved {len(actual_moves)} file(s)")
            if undo_file:
                print(f"Undo file created: {undo_file}")
        else:
            print("No changes made")

    except ValidationError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError:
        print("Editor was cancelled or failed", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        # Clean up temp file
        if Path(temp_path).exists():
            Path(temp_path).unlink()

    return 0


if __name__ == '__main__':
    sys.exit(main())

