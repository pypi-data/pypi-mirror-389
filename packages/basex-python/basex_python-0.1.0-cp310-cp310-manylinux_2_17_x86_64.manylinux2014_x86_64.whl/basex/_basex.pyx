# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
"""basex - Blazing fast base encoding/decoding library (Cython version)."""

from basex.modes import Mode
from basex._version import __version__


cdef class BaseXEncoder:
    cdef public str alphabet
    cdef public int base
    cdef public object mode
    cdef dict _decode_map

    def __init__(self, object alphabet, mode: Mode = Mode.DEFAULT):
        # Type validation
        if not isinstance(alphabet, str):
            raise TypeError(f"Alphabet must be str, got {type(alphabet).__name__}")

        # Empty alphabet validation
        if not alphabet:
            raise ValueError("Alphabet cannot be empty")

        # Minimum size validation (no base-1)
        if len(alphabet) < 2:
            raise ValueError(f"Alphabet must contain at least 2 characters, got {len(alphabet)}")

        # Duplicate character validation
        if len(alphabet) != len(set(alphabet)):
            raise ValueError("Alphabet contains duplicate characters")

        self.alphabet = alphabet
        self.base = len(alphabet)
        self.mode = mode
        self._decode_map = {char: idx for idx, char in enumerate(alphabet)}

    cpdef str encode(self, object data):
        cdef bytes data_bytes

        # Type validation
        if not isinstance(data, (str, bytes)):
            raise TypeError(f"Data must be str or bytes, got {type(data).__name__}")

        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data

        if not data_bytes:
            return ""

        if self.mode == Mode.RFC4648:
            return self._encode_rfc4648(data_bytes)
        return self._encode_numeric(data_bytes)

    cpdef bytes decode(self, object data):
        # Type validation
        if not isinstance(data, str):
            raise TypeError(f"Data must be str, got {type(data).__name__}")

        if not data:
            return b""

        if self.mode == Mode.RFC4648:
            return self._decode_rfc4648(data)
        return self._decode_numeric(data)

    cpdef int max_encoded_length(self, int bytes_count):
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
        import math
        cdef int bits_per_char, bits, chars, output_multiple
        cdef int max_chars
        cdef int max_utf8_bytes_per_char
        cdef int char_utf8_len

        if bytes_count == 0:
            return 0

        if self.mode == Mode.RFC4648:
            bits_per_char = int(math.log2(self.base))
            bits = bytes_count * 8
            chars = (bits + bits_per_char - 1) // bits_per_char  # ceil division

            # Add padding to output multiple
            if bits_per_char == 6:
                output_multiple = 4
                chars = ((chars + output_multiple - 1) // output_multiple) * output_multiple
            elif bits_per_char == 5:
                output_multiple = 8
                chars = ((chars + output_multiple - 1) // output_multiple) * output_multiple

            # Calculate UTF-8 byte length
            return len(self.alphabet[0].encode('utf-8')) * chars
        else:
            # Numeric mode: worst case is all 0xFF bytes
            # Maximum value is 256^bytes_count - 1
            # In base N: ceil(log_N(256^bytes_count)) = ceil(bytes_count * log_N(256))
            if self.base == 1:
                return bytes_count * 8  # Each bit needs a symbol
            max_chars = <int>math.ceil(bytes_count * math.log(256) / math.log(self.base))
            # Account for leading zeros
            max_chars += bytes_count
            # Calculate UTF-8 byte length (worst case: all symbols are max UTF-8 size)
            # Cannot use generator expression in cpdef, use loop instead
            max_utf8_bytes_per_char = 1
            for c in self.alphabet:
                char_utf8_len = len(c.encode('utf-8'))
                if char_utf8_len > max_utf8_bytes_per_char:
                    max_utf8_bytes_per_char = char_utf8_len
            return max_chars * max_utf8_bytes_per_char

    cdef str _encode_numeric(self, bytes data):
        # Use Python int for arbitrary precision
        cdef object num = int.from_bytes(data, 'big')
        cdef int remainder
        cdef int leading_zeros
        cdef list result

        if num == 0:
            return self.alphabet[0]

        result = []
        while num > 0:
            num, remainder = divmod(num, self.base)
            result.append(self.alphabet[remainder])

        leading_zeros = len(data) - len(data.lstrip(b'\x00'))
        return self.alphabet[0] * leading_zeros + ''.join(reversed(result))

    cdef bytes _decode_numeric(self, str data):
        cdef int leading_zeros
        # Use Python int for arbitrary precision
        cdef object num = 0
        cdef int byte_length
        cdef bytes result

        for char in data:
            if char not in self._decode_map:
                raise ValueError(f"Invalid character: {char}")

        leading_zeros = len(data) - len(data.lstrip(self.alphabet[0]))

        for char in data:
            num = num * self.base + self._decode_map[char]

        if num == 0:
            byte_length = 1
        else:
            byte_length = (num.bit_length() + 7) // 8

        result = num.to_bytes(byte_length, 'big')
        return b'\x00' * leading_zeros + result

    cdef str _encode_rfc4648(self, bytes data):
        import math
        cdef int bits_per_char = int(math.log2(self.base))
        cdef int padding_bits
        cdef str bits
        cdef list result
        cdef int i
        cdef str chunk
        cdef int output_multiple
        cdef int padding_chars

        if 2 ** bits_per_char != self.base:
            raise ValueError(f"RFC4648 mode requires power-of-2 alphabet size, got {self.base}")

        bits = ''.join(f'{byte:08b}' for byte in data)
        padding_bits = (bits_per_char - len(bits) % bits_per_char) % bits_per_char
        bits += '0' * padding_bits

        result = []
        for i in range(0, len(bits), bits_per_char):
            chunk = bits[i:i + bits_per_char]
            result.append(self.alphabet[int(chunk, 2)])

        if bits_per_char == 6:
            output_multiple = 4
        elif bits_per_char == 5:
            output_multiple = 8
        else:
            output_multiple = 0

        if output_multiple > 0:
            padding_chars = (output_multiple - len(result) % output_multiple) % output_multiple
            result.extend('=' * padding_chars)

        return ''.join(result)

    cdef bytes _decode_rfc4648(self, str data):
        import math
        cdef str data_stripped = data.rstrip('=')
        cdef int bits_per_char
        cdef str bits
        cdef int valid_bytes
        cdef bytes result

        for char in data_stripped:
            if char not in self._decode_map:
                raise ValueError(f"Invalid character: {char}")

        bits_per_char = int(math.log2(self.base))

        bits = ''.join(f'{self._decode_map[char]:0{bits_per_char}b}' for char in data_stripped)
        valid_bytes = len(bits) // 8
        bits = bits[:valid_bytes * 8]

        result = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
        return result


def init(str alphabet, mode: Mode = Mode.DEFAULT) -> BaseXEncoder:
    return BaseXEncoder(alphabet, mode)


def encode(object data, str alphabet, mode: Mode = Mode.DEFAULT) -> str:
    return BaseXEncoder(alphabet, mode).encode(data)


def decode(str data, str alphabet, mode: Mode = Mode.DEFAULT) -> bytes:
    return BaseXEncoder(alphabet, mode).decode(data)

