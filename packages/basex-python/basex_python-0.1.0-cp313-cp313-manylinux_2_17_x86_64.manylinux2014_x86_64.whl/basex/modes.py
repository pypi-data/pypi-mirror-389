"""Encoding modes for basex.

This module defines the available encoding modes that control
how data is encoded into the target alphabet.
"""

from enum import Enum


class Mode(Enum):
    """Encoding mode selection.

    Attributes:
        DEFAULT: Universal numeric baseN encoding for any alphabet size.
                 Uses mathematical base conversion. Best for base58, base62, etc.
        RFC4648: Bitwise encoding for power-of-2 alphabet sizes (2, 4, 8, 16, 32, 64).
                 Compatible with RFC 4648 standard (base64, base32, base16).
                 Includes automatic padding with '=' characters.
    """

    DEFAULT = "default"
    RFC4648 = "rfc4648"
