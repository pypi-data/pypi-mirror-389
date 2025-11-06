#!/usr/bin/env python3
"""Command-line interface for line breaker."""

import sys
from pathlib import Path

from linebreaker import process_file


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m linebreaker.cli input_file.md or directory")
        sys.exit(1)

    for arg in sys.argv[1:]:
        path = Path(arg)

        if path.is_file():
            try:
                process_file(str(path))
            except Exception as e:
                print(f"💔 Error processing: {path}")
                print(e)
        elif path.is_dir():
            # Recursively find all matching files
            for file_path in path.rglob("*"):
                if file_path.suffix in {".md", ".qmd", ".tex", ".txt"}:
                    try:
                        process_file(str(file_path))
                    except Exception as e:
                        print(f"💔 Error processing: {file_path}")
                        print(e)
        else:
            print(f"❌ Not found: {path}")

    print("🌟 Processing completed.")


if __name__ == "__main__":
    main()
