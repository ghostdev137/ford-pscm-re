#!/usr/bin/env python3
"""
Script to identify docstring formatting issues in Python files.

Checks for:
1. Bullet lists (lines starting with *, -, +) without blank line before them
2. Numbered lists (lines starting with digits and .) without blank line before them
3. Code blocks (lines starting with >>>) without blank line before them
4. reStructuredText directives (lines starting with ..) without blank line before them

These are common reStructuredText/Sphinx formatting issues that can cause
documentation to render incorrectly.

The script attempts to avoid false positives by:
- Skipping content inside literal blocks (after :: markers)
- Ignoring items that follow Sphinx field markers (:param:, :Example:, etc.)
- Handling Python interactive session output (lines between >>> prompts)
- Recognizing indented continuations

Known limitations:
- May flag some valid trailing >>> prompts in code examples
- Line numbers are approximate (offset from docstring start)
- Some complex nested structures may not be handled perfectly

Usage:
  python check_docstring_formatting.py [paths...]
  python check_docstring_formatting.py -v [paths...]

If no paths are specified, defaults to ../python relative to this script.
"""

import argparse
import os
import re
import ast
import sys
from pathlib import Path


def get_docstrings_from_file_regex(filepath, content):
    """
    Fallback docstring extraction using regex when AST parsing fails.
    This handles files with Python 3.10+ syntax like match statements.
    """
    docstrings = []
    lines = content.split('\n')

    # Find triple-quoted strings that appear after def/class or at module level
    in_docstring = False
    docstring_lines = []
    docstring_start = 0
    quote_style = None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not in_docstring:
            # Check for start of a docstring (triple quotes)
            for quote in ['"""', "'''"]:
                if quote in stripped:
                    # Check if it's the start of a docstring
                    idx = stripped.find(quote)
                    # Make sure it's not inside a comment or after code
                    before = stripped[:idx].strip()
                    if before == '' or before.endswith(':'):
                        in_docstring = True
                        quote_style = quote
                        docstring_start = i + 1
                        # Check if docstring ends on same line
                        after_start = stripped[idx + 3:]
                        if quote in after_start:
                            # Single line docstring
                            end_idx = after_start.find(quote)
                            docstring_content = after_start[:end_idx]
                            if docstring_content.strip():
                                docstrings.append((docstring_start, docstring_content, 'Unknown'))
                            in_docstring = False
                            quote_style = None
                        else:
                            docstring_lines = [after_start]
                        break
        else:
            # We're inside a docstring, look for the end
            if quote_style in stripped:
                # Found end of docstring
                end_idx = line.find(quote_style)
                docstring_lines.append(line[:end_idx])
                full_docstring = '\n'.join(docstring_lines)
                if full_docstring.strip():
                    docstrings.append((docstring_start, full_docstring, 'Unknown'))
                in_docstring = False
                docstring_lines = []
                quote_style = None
            else:
                docstring_lines.append(line)
        i += 1

    return docstrings


def get_docstrings_from_file(filepath):
    """Extract all docstrings from a Python file with their line numbers."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return []

    # Try AST parsing first
    try:
        tree = ast.parse(content, filename=str(filepath))
        docstrings = []

        for node in ast.walk(tree):
            # Only check nodes that can have docstrings
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                try:
                    docstring = ast.get_docstring(node, clean=False)
                    if docstring:
                        # Get the line number where the docstring starts
                        if isinstance(node, ast.Module):
                            # Module docstring is at the top
                            line_num = 1
                        else:
                            # For functions/classes, it's the first statement
                            line_num = node.body[0].lineno if node.body else node.lineno

                        # Get the name of the function/class/module
                        if isinstance(node, ast.Module):
                            node_name = 'module'
                        else:
                            node_name = node.name
                        docstrings.append((line_num, docstring, node_name))
                except:
                    # Skip if we can't get the docstring
                    pass

        return docstrings
    except SyntaxError:
        # Fall back to regex-based extraction for files with newer Python syntax
        return get_docstrings_from_file_regex(filepath, content)


def check_docstring_formatting(docstring):
    """
    Check for formatting issues in a docstring.

    Returns a list of (line_offset, issue_description) tuples.
    """
    issues = []
    lines = docstring.split('\n')

    # Patterns that should have a blank line before them
    patterns = [
        (r'^\s*[\*\-\+]\s+', 'bullet list item'),
        (r'^\s*\d+\.\s+', 'numbered list item'),
        (r'^\s*>>>', 'code block'),
        (r'^\s*\.\.\s+', 'reStructuredText directive'),
    ]

    # Sphinx field patterns that can contain code blocks or lists
    sphinx_field_pattern = r'^\s*:[A-Za-z_][A-Za-z0-9_]*:'

    # Track if we're in a literal block (started by ::)
    in_literal_block = False
    literal_block_indent = 0

    for i, line in enumerate(lines):
        # Skip the first line (always part of the opening)
        if i == 0:
            continue

        current_indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        # Check if previous line ended with :: (literal block marker)
        if i > 0:
            prev_line = lines[i - 1]
            if prev_line.rstrip().endswith('::'):
                in_literal_block = True
                literal_block_indent = len(prev_line) - len(prev_line.lstrip())

        # If we're in a literal block and dedented, we're out
        if in_literal_block and stripped and current_indent <= literal_block_indent:
            in_literal_block = False

        # Skip checks if we're inside a literal block
        if in_literal_block:
            continue

        # Check each pattern
        for pattern, description in patterns:
            if re.match(pattern, line):
                # Check if previous line is blank or also matches a list pattern
                prev_line = lines[i - 1] if i > 0 else ''

                # If previous line is not blank
                if prev_line.strip() != '':
                    # Check if previous line is also a list item (which is OK)
                    is_prev_list = any(re.match(p[0], prev_line) for p in patterns)

                    # Check if previous line is a Sphinx field (like :Example:, :param:, etc.)
                    is_sphinx_field = re.match(sphinx_field_pattern, prev_line)

                    # Check if we're indented under a previous section
                    # If current line is more indented than previous non-blank line, it's likely continuation
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    is_indented_continuation = current_indent > prev_indent

                    # Special case for code blocks (>>>):
                    if description == 'code block':
                        # In Python interactive sessions, >>> prompts after output or continuations are normal
                        # Skip if: previous line is >>> or ..., OR both lines are indented (in code example)
                        if (prev_line.strip().startswith('...') or
                            prev_line.strip().startswith('>>>') or
                            (prev_indent > 0)):  # Both lines indented = inside code example
                            # Don't report this as an issue
                            break

                    # Special case for bullet/numbered lists:
                    # 1. Check if we're continuing a list (prev line is wrapped text from previous bullet)
                    # 2. Check if we're nested under another list item
                    is_nested_list = False
                    if description in ['bullet list item', 'numbered list item']:
                        # Look back to find context - skip blank lines
                        for j in range(i - 1, max(0, i - 10), -1):
                            check_line = lines[j]
                            if not check_line.strip():
                                continue  # Skip blank lines
                            check_indent = len(check_line) - len(check_line.lstrip())

                            # If we find a line at same indent that's also a list item, we're continuing a list
                            if check_indent == current_indent and any(re.match(p[0], check_line) for p in patterns):
                                is_nested_list = True  # This is a list continuation
                                break

                            # If we find a less-indented line that's also a list item, we're nested
                            if check_indent < current_indent and any(re.match(p[0], check_line) for p in patterns):
                                is_nested_list = True
                                break

                            # If we find a non-list line at current or less indent (intro text), stop looking
                            if check_indent <= current_indent:
                                break

                    if not is_prev_list and not is_sphinx_field and not is_indented_continuation and not is_nested_list:
                        issues.append((i + 1, f"{description} without blank line before it"))
                break  # Only report one issue per line

    return issues


def find_python_files(root_dir):
    """Find all Python files in the given directory."""
    root = Path(root_dir)
    return list(root.rglob('*.py'))


def main():
    parser = argparse.ArgumentParser(
        description='Check Python docstrings for formatting issues.'
    )
    parser.add_argument(
        'paths',
        nargs='*',
        help='Files or directories to check (default: python/ directory)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show all files being checked, not just files with issues'
    )

    args = parser.parse_args()

    # Determine what to check
    if args.paths:
        files_to_check = []
        for path_str in args.paths:
            # Check if path contains glob characters
            if any(c in path_str for c in '*?['):
                matches = list(Path.cwd().glob(path_str))
                if not matches:
                    print(f"Warning: {path_str} did not match any files", file=sys.stderr)
                for path in matches:
                    if path.is_dir():
                        files_to_check.extend(find_python_files(path))
                    elif path.is_file() and path.suffix == '.py':
                        files_to_check.append(path)
            else:
                path = Path(path_str)
                if path.is_dir():
                    files_to_check.extend(find_python_files(path))
                elif path.is_file() and path.suffix == '.py':
                    files_to_check.append(path)
                else:
                    print(f"Warning: {path_str} is not a valid Python file or directory", file=sys.stderr)
    else:
        # Default to checking the python directory relative to this script
        script_dir = Path(__file__).parent
        python_dir = script_dir.parent / 'python'

        if not python_dir.exists():
            print(f"Error: Directory {python_dir} does not exist", file=sys.stderr)
            sys.exit(1)

        # Exclude examples subfolder when running with default path
        files_to_check = [f for f in find_python_files(python_dir)
                         if 'examples' not in f.parts]

    if args.verbose:
        print(f"Checking Python files...")
        print("=" * 80)

    files_with_issues = 0
    total_issues = 0

    for py_file in sorted(files_to_check):
        if args.verbose:
            print(f"Checking {py_file}...", end='', flush=True)

        docstrings = get_docstrings_from_file(py_file)
        file_issues = []

        for doc_line_num, docstring, node_type in docstrings:
            issues = check_docstring_formatting(docstring)
            if issues:
                for line_offset, issue_desc in issues:
                    # Calculate absolute line number in file
                    # This is approximate since we don't have exact positions
                    abs_line = doc_line_num + line_offset
                    file_issues.append((abs_line, issue_desc, node_type))

        if file_issues:
            files_with_issues += 1
            total_issues += len(file_issues)

            if args.verbose:
                print(f" {len(file_issues)} issue(s) found")
            else:
                print(f"{py_file}: {len(file_issues)} issue(s) found")

            for line_num, issue_desc, node_type in sorted(file_issues):
                print(f"  Line ~{line_num} ({node_type}): {issue_desc}")
        else:
            if args.verbose:
                print(" OK")

    if total_issues > 0:
        if args.verbose:
            print("=" * 80)
        print(f"\nFound {total_issues} issue(s) in {files_with_issues} file(s)")
        return 1
    else:
        if args.verbose:
            print("=" * 80)
            print("No issues found!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
