# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from .._types import FileTypes

__all__ = ["FileExtractTextParams"]


class FileExtractTextParams(TypedDict, total=False):
    file: Required[FileTypes]
    """The file to upload."""

    clean_text: bool
    """Whether to clean and normalize the extracted text. When enabled (true):

    - For HTML content: Removes script, style, and other non-text elements before
      extraction
    - Normalizes whitespace (collapses multiple spaces/tabs, normalizes newlines)
    - Removes empty lines and trims leading/trailing whitespace
    - Normalizes Unicode characters (NFC)
    - For JSON content: Only minimal cleaning to preserve structure When disabled
      (false): Returns raw extracted text without any processing.
    """
