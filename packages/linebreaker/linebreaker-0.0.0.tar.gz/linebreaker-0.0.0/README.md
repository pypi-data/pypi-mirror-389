

# Linebreaker

I created this tool because I couldn't find a reliable line breaking utility that works with Quarto markdown without altering headers, lists, or other formatting. This tool is conservative - it preserves your document structure and only adds line breaks when both the preceding and following text segments are sufficiently long.

## Features
Intelligent line breaking for Markdown and text files, with support for:
- Citations in format `[@...]`
- Decimal numbers
- Common abbreviations (Dr., Prof., vs., et al., etc.)
- YAML headers
- Code blocks
- Soft breaks on conjunctions, commas, and/or

## Installation

Install from PyPI using pixi:


```bash
pip install linebreaker
```

```bash
pixi add --pypi linebreaker
```

Or install from source:

```bash
git clone https://github.com/silas/linebreaker.git
cd linebreaker
pixi install
```

## Usage


### As a command-line tool:

```bash
# Process a single file
linebreaker your_file.md

# Process a directory
linebreaker writing/

# For compatibility, you can still use the old script
python -m linebreaker.cli your_file.md
```
> **⚠️ Important**: Only use this tool on files that are tracked by a version control system like Git. Line breaking modifies your files, and having version control ensures you can review and revert changes if needed.


### As a module:

```python
from linebreaker import format_line, break_text

# Format a single line
result = format_line("Your text here...")

# Process entire text with YAML/code blocks
result = break_text(full_text)
```

## Running Tests

```bash
# Run all tests
pytest linebreaker/tests/
```



## Detailed Features

### Hard Breaks (Sentence Boundaries)
- Splits on `.`, `?`, `!` when both before and after have 20+ characters
- Avoids common abbreviations: vs., Dr., Prof., Mr., Mrs., Ms., Ph.D., M.D., Jr., Sr., etc., e.g., i.e., et al., vol., no., pp., fig.

### Medium Breaks (Colons/Semicolons)
- Splits sentences longer than 80 characters at `:` or `;`
- Only if both parts have 20+ characters

### Soft Breaks (Conjunctions)
- Applied when there are 3+ sentences or sentence is >60 characters
- Breaks on: `but`, `such as`, `for example`, `e.g.`, `i.e.` (after 20 chars)
- Breaks on commas (after 40 chars)
- Breaks on `and`, `or` (after 40 chars)

### Smart Masking
- Citations `[@...]` are masked to prevent dots inside from triggering breaks
- Decimal numbers like `0.85` are masked similarly

## Development

To add new abbreviations, edit the `abbreviations` pattern in `core.py`:

```python
abbreviations = r'(?!vs\.|dr\.|prof\.|...|your_abbrev\.)'
```
