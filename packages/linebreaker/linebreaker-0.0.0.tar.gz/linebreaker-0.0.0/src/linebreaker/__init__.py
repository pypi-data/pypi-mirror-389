"""Line breaker module for formatting text with intelligent line breaks."""

from .core import (
    mask_citations_and_numbers,
    restore_masked_content,
    handle_parentheses_and_footnotes,
    restore_protected_content,
    format_segment,
    split_on_sentence_punctuation,
    split_on_colons,
    split_on_em_dashes,
    split_on_parentheses_end,
    format_line,
    break_text,
    process_file,
)

__all__ = [
    "mask_citations_and_numbers",
    "restore_masked_content",
    "handle_parentheses_and_footnotes",
    "restore_protected_content",
    "format_segment",
    "split_on_sentence_punctuation",
    "split_on_colons",
    "split_on_em_dashes",
    "split_on_parentheses_end",
    "format_line",
    "break_text",
    "process_file",
]

from . import _version

__version__ = _version.get_versions()["version"]
