"""basex - Fast base encoding/decoding library.

This library provides flexible encoding and decoding for standard base encodings
(base58, base64, base32, base16) and custom base-N alphabets of any size,
with automatic optimization through Cython-compiled extensions when available.

The package automatically selects the best available implementation:
- Cython: High-performance compiled extensions (10-100x faster)
- Python: Pure Python fallback for maximum compatibility

Usage:
    >>> import basex
    >>> basex.b64.encode("foo")
    'Zm9v'
    >>> basex.b58.encode("Hello World!")
    '2NEpo7TZRRrLZSi2U'
"""

from basex._version import __version__

# Attempt to import Cython-compiled extensions for performance
try:
    from basex._basex import Mode, BaseXEncoder, init, encode, decode

    _implementation = "cython"
except ImportError:
    # Fallback to pure Python implementation
    from basex.modes import Mode
    from basex.basex import BaseXEncoder, init, encode, decode

    _implementation = "python"

# Always import presets from the same location
from basex.presets import b64, b32, b16, b58, b57, b56


__all__ = [
    # Version
    "__version__",
    # Core API
    "Mode",
    "BaseXEncoder",
    "init",
    "encode",
    "decode",
    # Presets
    "b64",
    "b32",
    "b16",
    "b58",
    "b57",
    "b56",
]
