"""
Response filters for AI Code Tools server.

Includes guardrails to handle extremely large tool outputs safely.
"""

import os
import re
import time
from typing import Dict, Any
import logging

# Use a shared, named logger so server and filters log consistently
logger = logging.getLogger("aicodetools")

# Lazy, singleton tiktoken encoder to avoid re-instantiation overhead
try:
    import tiktoken  # type: ignore
    HAS_TIKTOKEN = True
except ImportError:
    tiktoken = None  # type: ignore
    HAS_TIKTOKEN = False

_ENCODING = None
_ENCODING_NAME = "o200k_base"
_ENCODING_TRIED = False

class SimpleWordEncoder:
    """Fallback encoder that splits text into 4-character tokens.

    - Ensures robust behavior even if the input has no word characters.
    - encode(text) -> List[str] of 4-char chunks
    - decode(tokens) -> Original text reconstructed by concatenation

    This simplified approximation is used when tiktoken is unavailable
    or fails to initialize. It favors speed and simplicity.
    """

    def encode(self, text: str):
        return [text[i : i + 4] for i in range(0, len(text), 4)]

    def decode(self, tokens):
        return "".join(tokens)


def _get_token_encoder(encoding_name: str = _ENCODING_NAME):
    """Return a cached encoder (tiktoken or fallback), initializing once lazily."""
    global _ENCODING, _ENCODING_TRIED, _ENCODING_NAME
    # If tiktoken is not available, provide a singleton fallback encoder
    if not HAS_TIKTOKEN:
        if _ENCODING is None or not isinstance(_ENCODING, SimpleWordEncoder):
            _ENCODING = SimpleWordEncoder()
            _ENCODING_NAME = "simple_word_encoder"
            _ENCODING_TRIED = True
            logger.info("Guardrail encoder: using fallback 'simple_word_encoder' (tiktoken unavailable)")
        return _ENCODING
    # Return cached encoder if name matches
    if _ENCODING is not None and _ENCODING_NAME == encoding_name:
        return _ENCODING
    # Initialize or reinitialize if name changes
    if (not _ENCODING_TRIED) or (_ENCODING_NAME != encoding_name):
        try:
            _ENCODING = tiktoken.get_encoding(encoding_name)
            _ENCODING_NAME = encoding_name
            logger.info(f"Guardrail encoder: initialized tiktoken '{encoding_name}'")
        except Exception:
            # Fallback to words-as-tokens encoder on failure
            _ENCODING = SimpleWordEncoder()
            _ENCODING_NAME = "simple_word_encoder"
            logger.warning(f"Guardrail encoder: failed to init tiktoken '{encoding_name}', using fallback 'simple_word_encoder'")
        _ENCODING_TRIED = True
    return _ENCODING


def guard_large_tool_output(
    payload: Dict[str, Any],
    token_threshold: int = 40000,
    head_tokens: int = 5000,
    output_dir: str = "tool_runs",
    encoding_name: str = "o200k_base",
) -> Dict[str, Any]:
    """
    Guard against excessively large tool outputs by storing them to a file
    and replacing the response output with a summary + preview.

    - Counts tokens using tiktoken for accurate measurement.
    - If token count exceeds `token_threshold`, writes full output to a file under `output_dir`.
    - Returns the payload with `output` replaced by a message + top 2.5k tokens,
      an ellipsis line, and bottom 2.5k tokens (total preview ≈ 5k tokens).

    Args:
        payload: Response dict potentially containing an `output` string.
        token_threshold: Maximum allowed token count before storing output.
        head_tokens: Number of tokens to include in the returned preview.
        output_dir: Directory to store large outputs.

    Returns:
        Modified payload dict if large output detected, otherwise original payload.
    """
    try:
        output = payload.get("output")
        if not isinstance(output, str):
            return payload

        top_snippet_text = None
        bottom_snippet_text = None
        token_count = 0

        encoding = _get_token_encoder(encoding_name)

        # Encode full output and count tokens (tiktoken or fallback)
        encoded = encoding.encode(output)
        token_count = len(encoded)
        if token_count <= token_threshold:
            return payload

        # Decode preview: top 2.5k and bottom 2.5k tokens
        top_n = max(0, min(head_tokens // 2, token_count))
        bottom_n = max(0, min(head_tokens // 2, token_count))
        top_snippet_text = encoding.decode(encoded[:top_n])
        bottom_snippet_text = encoding.decode(encoded[-bottom_n:])

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Save the full output to a timestamped file
        ts = int(time.time())
        filename = f"large_output_{ts}.txt"
        filepath = os.path.abspath(os.path.join(output_dir, filename))
        with open(filepath, "w", encoding="utf-8", errors="ignore") as f:
            f.write(output)

        # Log guardrail activation with saved path for traceability
        logger.info(
            f"Guardrail: exceeded token limit; output saved to '{filepath}' (≈{token_count} tokens)"
        )

        # Prepare preview snippets (already computed via tiktoken or regex)
        if not top_snippet_text:
            top_snippet_text = output[: min(len(output), 8192 * 5)]
        if not bottom_snippet_text:
            bottom_snippet_text = output[max(0, len(output) - 8192 * 5) :]

        # Replace the output with message + actionable guidance + top/bottom preview
        summary = (
            f"Large tool output exceeded 40k tokens (≈{token_count}). Full output saved to '{filepath}'.\n"
            f"Use the saved file to Query the output.\n"
            f"Avoid loading the entire file at once; use chunked reads, line ranges, or regex filters.\n\n"
            f"How to query without loading the entire file:\n"
            f"- read tool: set 'file_path' and use 'regex' or 'lines_start'/'lines_end'\n"
            f"- grep (Linux/macOS): grep -n 'pattern' '{filepath}' | head -n 100\n"
            f"Top preview (first 2.5k tokens)\n"
        )
        payload["output"] = (
            summary
            + top_snippet_text
            + "\n----- Truncated -----\n"
            + "Bottom preview (last 2.5k tokens)\n"
            + bottom_snippet_text
        )
        return payload

    except Exception:
        # Fail open: if filter encounters an error, return original payload
        return payload


def init_tokenizer(encoding_name: str = _ENCODING_NAME) -> bool:
    """Initialize the module's tokenizer once at server startup.

    Returns True if initialized (including fallback), False on unexpected error.
    """
    try:
        _get_token_encoder(encoding_name)
        # _get_token_encoder logs which encoder was chosen
        return True
    except Exception as e:
        # Should not normally happen; keep server resilient
        logger.warning(f"Tokenizer init encountered an error: {e}")
        return False
