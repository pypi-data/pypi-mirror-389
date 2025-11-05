"""Preset encoder instances for common base encodings.

This module provides pre-configured encoder instances for widely-used
base encoding schemes. These instances are ready to use and follow
established standards (RFC 4648 for base64/32/16, Bitcoin for base58).

All presets are module-level singletons that can be imported and used directly:
    >>> from basex import b64
    >>> b64.encode("test")
    'dGVzdA=='
"""

try:
    from basex._basex import BaseXEncoder
except ImportError:
    from basex.basex import BaseXEncoder

from basex.modes import Mode
from basex.constants import (
    BASE64_ALPHABET,
    BASE32_ALPHABET,
    BASE16_ALPHABET,
    BASE58_ALPHABET,
    BASE57_ALPHABET,
    BASE56_ALPHABET,
)


# RFC 4648 Standard Encodings

b64 = BaseXEncoder(BASE64_ALPHABET, Mode.RFC4648)
"""Base64 encoder following RFC 4648 standard.

Uses the standard Base64 alphabet with automatic padding.
Compatible with Python's base64 module and all standard implementations.

Examples:
    >>> b64.encode("foo")
    'Zm9v'
    >>> b64.decode("Zm9v")
    b'foo'
"""

b32 = BaseXEncoder(BASE32_ALPHABET, Mode.RFC4648)
"""Base32 encoder following RFC 4648 standard.

Uses uppercase letters A-Z and digits 2-7.
Includes automatic padding to 8-character boundaries.

Examples:
    >>> b32.encode("foo")
    'MZXW6==='
"""

b16 = BaseXEncoder(BASE16_ALPHABET, Mode.RFC4648)
"""Base16 (hexadecimal) encoder following RFC 4648 standard.

Standard hex encoding using uppercase letters.
No padding required due to 2-character boundaries.

Examples:
    >>> b16.encode("foo")
    '666F6F'
"""


# Cryptocurrency and Human-Readable Encodings

b58 = BaseXEncoder(BASE58_ALPHABET, Mode.DEFAULT)
"""Base58 encoder following Bitcoin standard.

Excludes visually similar characters: 0 (zero), O (capital o),
I (capital i), and l (lowercase L). No padding.

Commonly used for cryptocurrency addresses and short URLs.

Examples:
    >>> b58.encode("Hello World!")
    '2NEpo7TZRRrLZSi2U'
"""

b57 = BaseXEncoder(BASE57_ALPHABET, Mode.DEFAULT)
"""Base57 encoder (Base58 without '1').

Removes '1' in addition to 0OIl to further reduce visual confusion.
Useful for contexts where '1' might be confused with 'I' or 'l'.

Examples:
    >>> b57.encode("Hello World!")
    '3orqLftwyK9mqMwUd'
"""

b56 = BaseXEncoder(BASE56_ALPHABET, Mode.DEFAULT)
"""Base56 encoder (Base58 without '1' and 'o').

Most conservative alphabet for human readability.
Removes: 0, O, I, l, 1, o - all commonly confused characters.

Examples:
    >>> b56.encode("Hello World!")
    '4Q9SNpVv4JrdwvjKj'
"""


__all__ = ["b64", "b32", "b16", "b58", "b57", "b56"]
