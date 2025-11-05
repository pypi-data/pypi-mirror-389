"""Pure Python implementation of base encoding/decoding.

This module provides the core BaseXEncoder class that handles encoding
and decoding of data in arbitrary base alphabets. It supports two modes:
- DEFAULT: Universal numeric base conversion for any alphabet size
- RFC4648: Bitwise encoding for power-of-2 alphabets with padding

This is the fallback implementation used when compiled Cython extensions
are not available.
"""

from basex.modes import Mode


class BaseXEncoder:
    """Encoder/decoder for arbitrary base alphabets.

    This class provides methods to encode binary data into a custom alphabet
    and decode it back. It supports two encoding modes for different use cases.

    Args:
        alphabet: String containing unique characters for the target base.
                 Length must match the desired base (e.g., 64 chars for base64).
        mode: Encoding mode (Mode.DEFAULT or Mode.RFC4648).

    Raises:
        ValueError: If alphabet contains duplicate characters.

    Examples:
        >>> # Base58 encoding
        >>> b58 = BaseXEncoder("123456789ABC...xyz", Mode.DEFAULT)
        >>> b58.encode("Hello")
        '9Ajdvzr'

        >>> # Base64 encoding with RFC4648 mode
        >>> b64 = BaseXEncoder("ABCD...+/", Mode.RFC4648)
        >>> b64.encode("foo")
        'Zm9v'
    """

    def __init__(self, alphabet: str, mode: Mode = Mode.DEFAULT):
        # Type validation
        if not isinstance(alphabet, str):
            raise TypeError(f"Alphabet must be str, got {type(alphabet).__name__}")

        # Empty alphabet validation
        if not alphabet:
            raise ValueError("Alphabet cannot be empty")

        # Minimum size validation (no base-1)
        if len(alphabet) < 2:
            raise ValueError(
                f"Alphabet must contain at least 2 characters, got {len(alphabet)}"
            )

        # Duplicate character validation
        if len(alphabet) != len(set(alphabet)):
            raise ValueError("Alphabet contains duplicate characters")

        self.alphabet = alphabet
        self.base = len(alphabet)
        self.mode = mode
        self._decode_map = {char: idx for idx, char in enumerate(alphabet)}

    def encode(self, data: str | bytes) -> str:
        """Encode data to the target alphabet.

        Args:
            data: String (UTF-8) or bytes to encode.

        Returns:
            Encoded string in the target alphabet.

        Examples:
            >>> encoder.encode("test")
            '3yZe7d'
            >>> encoder.encode(b"test")
            '3yZe7d'
        """
        # Type validation
        if not isinstance(data, (str, bytes)):
            raise TypeError(f"Data must be str or bytes, got {type(data).__name__}")

        if isinstance(data, str):
            data = data.encode("utf-8")

        if not data:
            return ""

        if self.mode == Mode.RFC4648:
            return self._encode_rfc4648(data)
        return self._encode_numeric(data)

    def decode(self, data: str) -> bytes:
        """Decode data from the target alphabet.

        Args:
            data: Encoded string to decode.

        Returns:
            Decoded bytes.

        Raises:
            ValueError: If data contains characters not in alphabet.

        Examples:
            >>> encoder.decode("3yZe7d")
            b'test'
        """
        # Type validation
        if not isinstance(data, str):
            raise TypeError(f"Data must be str, got {type(data).__name__}")

        if not data:
            return b""

        if self.mode == Mode.RFC4648:
            return self._decode_rfc4648(data)
        return self._decode_numeric(data)

    def max_encoded_length(self, bytes_count: int) -> int:
        """Calculate maximum encoded string length in UTF-8 bytes.

        Returns the worst-case length of the encoded string when encoding
        the specified number of bytes. This accounts for padding in RFC4648
        mode and leading zeros in numeric mode.

        Args:
            bytes_count: Number of bytes to encode.

        Returns:
            Maximum length of encoded string in UTF-8 bytes.

        Examples:
            >>> b64.max_encoded_length(3)  # "foo" -> "Zm9v" (4 chars)
            4
            >>> b32.max_encoded_length(1)  # "f" -> "MY======" (8 chars with padding)
            8
        """
        if bytes_count == 0:
            return 0

        if self.mode == Mode.RFC4648:
            import math

            bits_per_char = int(math.log2(self.base))
            bits = bytes_count * 8
            chars = (bits + bits_per_char - 1) // bits_per_char  # ceil division

            # Add padding to output multiple
            pad_map = {6: 4, 5: 8}
            if bits_per_char in pad_map:
                output_multiple = pad_map[bits_per_char]
                chars = (
                    (chars + output_multiple - 1) // output_multiple
                ) * output_multiple

            # Calculate UTF-8 byte length
            return sum(len(c.encode("utf-8")) for c in self.alphabet[:1]) * chars
        else:
            # Numeric mode: worst case is all 0xFF bytes
            # Maximum value is 256^bytes_count - 1
            # In base N: ceil(log_N(256^bytes_count)) = ceil(bytes_count * log_N(256))
            import math

            if self.base == 1:
                return bytes_count * 8  # Each bit needs a symbol
            max_chars = math.ceil(bytes_count * math.log(256) / math.log(self.base))
            # Account for leading zeros
            max_chars += bytes_count
            # Calculate UTF-8 byte length (worst case: all symbols are max UTF-8 size)
            max_utf8_bytes_per_char = max(len(c.encode("utf-8")) for c in self.alphabet)
            return max_chars * max_utf8_bytes_per_char

    def _encode_numeric(self, data: bytes) -> str:
        """Encode using numeric base conversion.

        This method treats the input bytes as a big-endian integer
        and converts it to the target base using mathematical division.
        Preserves leading zero bytes as leading alphabet[0] characters.
        """
        num = int.from_bytes(data, "big")

        if num == 0:
            return self.alphabet[0]

        result = []
        while num > 0:
            num, remainder = divmod(num, self.base)
            result.append(self.alphabet[remainder])

        leading_zeros = len(data) - len(data.lstrip(b"\x00"))
        return self.alphabet[0] * leading_zeros + "".join(reversed(result))

    def _decode_numeric(self, data: str) -> bytes:
        """Decode using numeric base conversion.

        Reverses the numeric encoding process by converting from
        the target base back to a big-endian integer, then to bytes.
        """
        for char in data:
            if char not in self._decode_map:
                raise ValueError(f"Invalid character: {char}")

        leading_zeros = len(data) - len(data.lstrip(self.alphabet[0]))

        num = 0
        for char in data:
            num = num * self.base + self._decode_map[char]

        if num == 0:
            byte_length = 1
        else:
            byte_length = (num.bit_length() + 7) // 8

        result = num.to_bytes(byte_length, "big")
        return b"\x00" * leading_zeros + result

    def _encode_rfc4648(self, data: bytes) -> str:
        """Encode using RFC 4648 bitwise method.

        Groups input bits according to the alphabet size (must be power of 2)
        and adds padding '=' characters to ensure output length is a multiple
        of the specified value (4 for base64, 8 for base32).
        """
        import math

        bits_per_char = int(math.log2(self.base))
        if 2**bits_per_char != self.base:
            raise ValueError(
                f"RFC4648 mode requires power-of-2 alphabet size, got {self.base}"
            )

        bits = "".join(f"{byte:08b}" for byte in data)
        padding_bits = (bits_per_char - len(bits) % bits_per_char) % bits_per_char
        bits += "0" * padding_bits

        result = []
        for i in range(0, len(bits), bits_per_char):
            chunk = bits[i : i + bits_per_char]
            result.append(self.alphabet[int(chunk, 2)])

        pad_map = {6: 4, 5: 8}
        if bits_per_char in pad_map:
            output_multiple = pad_map[bits_per_char]
            padding_chars = (
                output_multiple - len(result) % output_multiple
            ) % output_multiple
            result.extend("=" * padding_chars)

        return "".join(result)

    def _decode_rfc4648(self, data: str) -> bytes:
        """Decode using RFC 4648 bitwise method.

        Strips padding, converts each character to its bit representation,
        and groups the bits back into bytes.
        """
        data = data.rstrip("=")

        for char in data:
            if char not in self._decode_map:
                raise ValueError(f"Invalid character: {char}")

        import math

        bits_per_char = int(math.log2(self.base))

        bits = "".join(f"{self._decode_map[char]:0{bits_per_char}b}" for char in data)
        valid_bytes = len(bits) // 8
        bits = bits[: valid_bytes * 8]

        result = bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits), 8))
        return result


def init(alphabet: str, mode: Mode = Mode.DEFAULT) -> BaseXEncoder:
    """Create a new encoder instance.

    Args:
        alphabet: String of unique characters for the target base.
        mode: Encoding mode (DEFAULT or RFC4648).

    Returns:
        Configured BaseXEncoder instance.

    Examples:
        >>> b58 = init("123456789ABC...xyz")
        >>> b58.encode("test")
        '3yZe7d'
    """
    return BaseXEncoder(alphabet, mode)


def encode(data: str | bytes, alphabet: str, mode: Mode = Mode.DEFAULT) -> str:
    """Encode data directly without creating an encoder instance.

    Convenience function for one-off encoding operations.

    Args:
        data: String or bytes to encode.
        alphabet: Target alphabet.
        mode: Encoding mode.

    Returns:
        Encoded string.

    Examples:
        >>> encode("test", "123456789ABC...xyz")
        '3yZe7d'
    """
    return BaseXEncoder(alphabet, mode).encode(data)


def decode(data: str, alphabet: str, mode: Mode = Mode.DEFAULT) -> bytes:
    """Decode data directly without creating an encoder instance.

    Convenience function for one-off decoding operations.

    Args:
        data: Encoded string to decode.
        alphabet: Source alphabet.
        mode: Encoding mode.

    Returns:
        Decoded bytes.

    Examples:
        >>> decode("3yZe7d", "123456789ABC...xyz")
        b'test'
    """
    return BaseXEncoder(alphabet, mode).decode(data)
