"""Standard alphabet constants for base encodings.

This module defines the alphabet constants used by preset encoders.
All alphabets are defined here to avoid duplication across the codebase.
"""

# RFC 4648 Standard Encodings
BASE64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
BASE32_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
BASE16_ALPHABET = "0123456789ABCDEF"

# Cryptocurrency and Human-Readable Encodings
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BASE57_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BASE56_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz"

__all__ = [
    "BASE64_ALPHABET",
    "BASE32_ALPHABET",
    "BASE16_ALPHABET",
    "BASE58_ALPHABET",
    "BASE57_ALPHABET",
    "BASE56_ALPHABET",
]
