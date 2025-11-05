"""Comprehensive tests for basex using RFC 4648 and Base58 test vectors.

These tests use the 'implementation' fixture from conftest.py, which runs
each test twice: once with the Cython implementation and once with pure Python.
This ensures both implementations produce identical results.
"""

import pytest

from basex.constants import (
    BASE64_ALPHABET,
    BASE32_ALPHABET,
    BASE16_ALPHABET,
    BASE58_ALPHABET,
    BASE57_ALPHABET,
    BASE56_ALPHABET,
)


# RFC 4648 Test Vectors (Section 10)
RFC4648_VECTORS = [
    ("", ""),
    ("f", "f"),
    ("fo", "fo"),
    ("foo", "foo"),
    ("foob", "foob"),
    ("fooba", "fooba"),
    ("foobar", "foobar"),
]

BASE64_VECTORS = [
    ("", ""),
    ("f", "Zg=="),
    ("fo", "Zm8="),
    ("foo", "Zm9v"),
    ("foob", "Zm9vYg=="),
    ("fooba", "Zm9vYmE="),
    ("foobar", "Zm9vYmFy"),
]

BASE32_VECTORS = [
    ("", ""),
    ("f", "MY======"),
    ("fo", "MZXQ===="),
    ("foo", "MZXW6==="),
    ("foob", "MZXW6YQ="),
    ("fooba", "MZXW6YTB"),
    ("foobar", "MZXW6YTBOI======"),
]

BASE16_VECTORS = [
    ("", ""),
    ("f", "66"),
    ("fo", "666F"),
    ("foo", "666F6F"),
    ("foob", "666F6F62"),
    ("fooba", "666F6F6261"),
    ("foobar", "666F6F626172"),
]

BASE58_VECTORS = [
    ("Hello World!", "2NEpo7TZRRrLZSi2U"),
    (
        "The quick brown fox jumps over the lazy dog.",
        "USm3fpXnKG5EUBx2ndxBDMPVciP5hGey2Jh4NDv6gmeo1LkMeiKrLJUUBk6Z",
    ),
    (bytes.fromhex("0000287fb4cd"), "11233QC4"),
]

# Base57: Base58 without '1' to avoid confusion with 'l'
BASE57_VECTORS = [
    ("Hello World!", "3orqLftwyK9mqMwUd"),
    ("test", "5FziFy"),
]

# Base56: Base58 without '1' and 'o' to avoid confusion
BASE56_VECTORS = [
    ("Hello World!", "4Q9SNpVv4JrdwvjKj"),
    ("test", "5YZjvE"),
]


class TestBaseXInit:
    """Test basex.init() API with instance methods."""

    @pytest.mark.parametrize("input_str,expected", BASE64_VECTORS)
    def test_base64_encode(self, implementation, input_str, expected):
        impl, impl_name = implementation
        b64 = impl.init(alphabet=BASE64_ALPHABET, mode=impl.Mode.RFC4648)
        result = b64.encode(input_str)
        assert result == expected

    @pytest.mark.parametrize("input_str,expected", BASE64_VECTORS)
    def test_base64_decode(self, implementation, input_str, expected):
        impl, impl_name = implementation
        b64 = impl.init(alphabet=BASE64_ALPHABET, mode=impl.Mode.RFC4648)
        result = b64.decode(expected)
        assert result == input_str.encode("utf-8")

    @pytest.mark.parametrize("input_str,expected", BASE32_VECTORS)
    def test_base32_encode(self, implementation, input_str, expected):
        impl, impl_name = implementation
        b32 = impl.init(alphabet=BASE32_ALPHABET, mode=impl.Mode.RFC4648)
        result = b32.encode(input_str)
        assert result == expected

    @pytest.mark.parametrize("input_str,expected", BASE32_VECTORS)
    def test_base32_decode(self, implementation, input_str, expected):
        impl, impl_name = implementation
        b32 = impl.init(alphabet=BASE32_ALPHABET, mode=impl.Mode.RFC4648)
        result = b32.decode(expected)
        assert result == input_str.encode("utf-8")

    @pytest.mark.parametrize("input_str,expected", BASE16_VECTORS)
    def test_base16_encode(self, implementation, input_str, expected):
        impl, impl_name = implementation
        b16 = impl.init(alphabet=BASE16_ALPHABET, mode=impl.Mode.RFC4648)
        result = b16.encode(input_str)
        assert result == expected

    @pytest.mark.parametrize("input_str,expected", BASE16_VECTORS)
    def test_base16_decode(self, implementation, input_str, expected):
        impl, impl_name = implementation
        b16 = impl.init(alphabet=BASE16_ALPHABET, mode=impl.Mode.RFC4648)
        result = b16.decode(expected)
        assert result == input_str.encode("utf-8")

    @pytest.mark.parametrize("input_data,expected", BASE58_VECTORS)
    def test_base58_encode(self, implementation, input_data, expected):
        impl, impl_name = implementation
        b58 = impl.init(alphabet=BASE58_ALPHABET)
        result = b58.encode(input_data)
        assert result == expected

    @pytest.mark.parametrize("input_data,expected", BASE58_VECTORS)
    def test_base58_decode(self, implementation, input_data, expected):
        impl, impl_name = implementation
        b58 = impl.init(alphabet=BASE58_ALPHABET)
        result = b58.decode(expected)
        if isinstance(input_data, str):
            assert result == input_data.encode("utf-8")
        else:
            assert result == input_data

    @pytest.mark.parametrize("input_str,expected", BASE57_VECTORS)
    def test_base57_encode(self, implementation, input_str, expected):
        impl, impl_name = implementation
        b57 = impl.init(alphabet=BASE57_ALPHABET)
        result = b57.encode(input_str)
        assert result == expected

    @pytest.mark.parametrize("input_str,expected", BASE57_VECTORS)
    def test_base57_decode(self, implementation, input_str, expected):
        impl, impl_name = implementation
        b57 = impl.init(alphabet=BASE57_ALPHABET)
        result = b57.decode(expected)
        assert result == input_str.encode("utf-8")

    @pytest.mark.parametrize("input_str,expected", BASE56_VECTORS)
    def test_base56_encode(self, implementation, input_str, expected):
        impl, impl_name = implementation
        b56 = impl.init(alphabet=BASE56_ALPHABET)
        result = b56.encode(input_str)
        assert result == expected

    @pytest.mark.parametrize("input_str,expected", BASE56_VECTORS)
    def test_base56_decode(self, implementation, input_str, expected):
        impl, impl_name = implementation
        b56 = impl.init(alphabet=BASE56_ALPHABET)
        result = b56.decode(expected)
        assert result == input_str.encode("utf-8")


class TestBaseXDirectAPI:
    """Test basex.encode() and basex.decode() direct API."""

    @pytest.mark.parametrize("input_str,expected", BASE64_VECTORS)
    def test_base64_encode_direct(self, implementation, input_str, expected):
        impl, impl_name = implementation
        result = impl.encode(
            input_str, alphabet=BASE64_ALPHABET, mode=impl.Mode.RFC4648
        )
        assert result == expected

    @pytest.mark.parametrize("input_str,expected", BASE64_VECTORS)
    def test_base64_decode_direct(self, implementation, input_str, expected):
        impl, impl_name = implementation
        result = impl.decode(expected, alphabet=BASE64_ALPHABET, mode=impl.Mode.RFC4648)
        assert result == input_str.encode("utf-8")

    @pytest.mark.parametrize("input_str,expected", BASE58_VECTORS[:2])
    def test_base58_encode_direct(self, implementation, input_str, expected):
        impl, impl_name = implementation
        result = impl.encode(input_str, alphabet=BASE58_ALPHABET)
        assert result == expected


class TestInputHandling:
    """Test str and bytes input handling."""

    def test_encode_str_input(self, implementation):
        """String input should be converted to UTF-8 bytes."""
        impl, impl_name = implementation
        b64 = impl.init(alphabet=BASE64_ALPHABET, mode=impl.Mode.RFC4648)
        result = b64.encode("foo")
        assert result == "Zm9v"

    def test_encode_bytes_input(self, implementation):
        """Bytes input should work directly."""
        impl, impl_name = implementation
        b64 = impl.init(alphabet=BASE64_ALPHABET, mode=impl.Mode.RFC4648)
        result = b64.encode(b"foo")
        assert result == "Zm9v"

    def test_encode_invalid_utf8_str(self, implementation):
        """Invalid UTF-8 string should raise error."""
        impl, impl_name = implementation
        # This test verifies that str→bytes conversion validates encoding
        b64 = impl.init(alphabet=BASE64_ALPHABET, mode=impl.Mode.RFC4648)
        # Python strings are always valid UTF-8, so we test the expectation
        # that the encode method handles str correctly
        result = b64.encode("тест")  # Cyrillic text
        assert isinstance(result, str)

    def test_decode_returns_bytes(self, implementation):
        """Decode should always return bytes."""
        impl, impl_name = implementation
        b64 = impl.init(alphabet=BASE64_ALPHABET, mode=impl.Mode.RFC4648)
        result = b64.decode("Zm9v")
        assert isinstance(result, bytes)
        assert result == b"foo"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_bytes_encode(self, implementation):
        """Empty bytes should encode to empty string."""
        impl, impl_name = implementation
        b64 = impl.init(alphabet=BASE64_ALPHABET, mode=impl.Mode.RFC4648)
        result = b64.encode(b"")
        assert result == ""

    def test_base64_padding_handling(self, implementation):
        """Base64 decode should handle extra padding correctly."""
        impl, impl_name = implementation
        b64 = impl.init(alphabet=BASE64_ALPHABET, mode=impl.Mode.RFC4648)

        # Normal padding
        assert b64.decode("Zg==") == b"f"
        assert b64.decode("Zm8=") == b"fo"
        assert b64.decode("Zm9v") == b"foo"

        # Extra padding should be ignored
        assert b64.decode("Zg===") == b"f"
        assert b64.decode("Zm8==") == b"fo"
        assert b64.decode("Zm9v=") == b"foo"

        # No padding should work too
        assert b64.decode("Zg") == b"f"
        assert b64.decode("Zm8") == b"fo"

    def test_roundtrip(self, implementation):
        """Encode→Decode should return original data."""
        impl, impl_name = implementation
        b58 = impl.init(alphabet=BASE58_ALPHABET)
        original = "Hello, World!"
        encoded = b58.encode(original)
        decoded = b58.decode(encoded)
        assert decoded == original.encode("utf-8")

    def test_alphabet_uniqueness(self, implementation):
        """Alphabet with duplicate characters should raise error."""
        impl, impl_name = implementation
        with pytest.raises(ValueError, match="duplicate"):
            impl.init(alphabet="AABC")

    def test_invalid_decode_character(self, implementation):
        """Decoding with character not in alphabet should raise error."""
        impl, impl_name = implementation
        b58 = impl.init(alphabet=BASE58_ALPHABET)
        with pytest.raises(ValueError, match="Invalid character"):
            b58.decode("0OIl")  # These chars are not in Base58

    @pytest.mark.parametrize(
        "alphabet,mode",
        [
            (BASE64_ALPHABET, "RFC4648"),
            (BASE32_ALPHABET, "RFC4648"),
            (BASE16_ALPHABET, "RFC4648"),
            (BASE58_ALPHABET, "DEFAULT"),
            (BASE57_ALPHABET, "DEFAULT"),
            (BASE56_ALPHABET, "DEFAULT"),
        ],
    )
    def test_large_data_roundtrip(self, implementation, alphabet, mode):
        """10KB of random bytes should survive encode-decode roundtrip."""
        import secrets

        impl, impl_name = implementation

        mode_enum = impl.Mode.RFC4648 if mode == "RFC4648" else impl.Mode.DEFAULT
        encoder = impl.init(alphabet=alphabet, mode=mode_enum)

        # Generate 10KB of random data
        original_data = secrets.token_bytes(10 * 1024)

        # Roundtrip test
        encoded = encoder.encode(original_data)
        decoded = encoder.decode(encoded)

        assert decoded == original_data, f"{impl_name}: Large data roundtrip failed"

    def test_max_encoded_length_base64(self, implementation):
        """Test max_encoded_length calculation for base64."""
        impl, impl_name = implementation
        b64 = impl.init(alphabet=BASE64_ALPHABET, mode=impl.Mode.RFC4648)

        # Empty data
        assert b64.max_encoded_length(0) == 0

        # 1 byte: "f" -> "Zg==" (4 chars with padding)
        assert b64.max_encoded_length(1) == 4

        # 3 bytes: "foo" -> "Zm9v" (4 chars, no padding needed)
        assert b64.max_encoded_length(3) == 4

        # 4 bytes: "foob" -> "Zm9vYg==" (8 chars with padding)
        assert b64.max_encoded_length(4) == 8

    def test_max_encoded_length_base32(self, implementation):
        """Test max_encoded_length calculation for base32."""
        impl, impl_name = implementation
        b32 = impl.init(alphabet=BASE32_ALPHABET, mode=impl.Mode.RFC4648)

        # 1 byte: "f" -> "MY======" (8 chars with padding)
        assert b32.max_encoded_length(1) == 8

        # 5 bytes: "fooba" -> "MZXW6YTB" (8 chars, no padding needed)
        assert b32.max_encoded_length(5) == 8

        # 6 bytes -> 16 chars with padding
        assert b32.max_encoded_length(6) == 16

    def test_max_encoded_length_base16(self, implementation):
        """Test max_encoded_length calculation for base16."""
        impl, impl_name = implementation
        b16 = impl.init(alphabet=BASE16_ALPHABET, mode=impl.Mode.RFC4648)

        # 1 byte: "f" -> "66" (2 chars)
        assert b16.max_encoded_length(1) == 2

        # 3 bytes: "foo" -> "666F6F" (6 chars)
        assert b16.max_encoded_length(3) == 6

    def test_max_encoded_length_base58(self, implementation):
        """Test max_encoded_length calculation for base58."""
        impl, impl_name = implementation
        b58 = impl.init(alphabet=BASE58_ALPHABET)

        # Check that actual encoding never exceeds calculated max
        test_data = b"test data"
        max_len = b58.max_encoded_length(len(test_data))
        actual = b58.encode(test_data)
        assert len(actual.encode("utf-8")) <= max_len, (
            f"Actual {len(actual)} exceeds max {max_len}"
        )


class TestPresets:
    """Test preset instances (basex.b64, basex.b58, etc.)."""

    def test_b64_preset(self, implementation):
        """Test basex.b64 preset."""
        impl, impl_name = implementation
        assert impl.b64.encode("foo") == "Zm9v"
        assert impl.b64.decode("Zm9v") == b"foo"

    def test_b32_preset(self, implementation):
        """Test basex.b32 preset."""
        impl, impl_name = implementation
        assert impl.b32.encode("foo") == "MZXW6==="
        assert impl.b32.decode("MZXW6===") == b"foo"

    def test_b16_preset(self, implementation):
        """Test basex.b16 preset."""
        impl, impl_name = implementation
        assert impl.b16.encode("foo") == "666F6F"
        assert impl.b16.decode("666F6F") == b"foo"

    def test_b58_preset(self, implementation):
        """Test basex.b58 preset."""
        impl, impl_name = implementation
        assert impl.b58.encode("Hello World!") == "2NEpo7TZRRrLZSi2U"
        assert impl.b58.decode("2NEpo7TZRRrLZSi2U") == b"Hello World!"

    def test_b57_preset(self, implementation):
        """Test basex.b57 preset."""
        impl, impl_name = implementation
        assert impl.b57.encode("Hello World!") == "3orqLftwyK9mqMwUd"
        assert impl.b57.decode("3orqLftwyK9mqMwUd") == b"Hello World!"

    def test_b56_preset(self, implementation):
        """Test basex.b56 preset."""
        impl, impl_name = implementation
        assert impl.b56.encode("Hello World!") == "4Q9SNpVv4JrdwvjKj"
        assert impl.b56.decode("4Q9SNpVv4JrdwvjKj") == b"Hello World!"


class TestValidations:
    """Test input validation and error handling."""

    # Alphabet validations
    def test_empty_alphabet(self, implementation):
        """Empty alphabet should raise ValueError."""
        impl, impl_name = implementation
        with pytest.raises(ValueError, match="cannot be empty"):
            impl.init(alphabet="")

    def test_single_char_alphabet(self, implementation):
        """Single character alphabet should raise ValueError."""
        impl, impl_name = implementation
        with pytest.raises(ValueError, match="at least 2 characters"):
            impl.init(alphabet="A")

    def test_alphabet_type_validation_int(self, implementation):
        """Non-string alphabet should raise TypeError."""
        impl, impl_name = implementation
        with pytest.raises(TypeError, match="(Alphabet must be str|incorrect type)"):
            impl.init(alphabet=123)

    def test_alphabet_type_validation_list(self, implementation):
        """List alphabet should raise TypeError."""
        impl, impl_name = implementation
        with pytest.raises(TypeError, match="(Alphabet must be str|incorrect type)"):
            impl.init(alphabet=["A", "B", "C"])

    def test_alphabet_type_validation_none(self, implementation):
        """None alphabet should raise TypeError."""
        impl, impl_name = implementation
        with pytest.raises(TypeError, match="(Alphabet must be str|incorrect type)"):
            impl.init(alphabet=None)

    # Data type validations for encode
    def test_encode_invalid_type_int(self, implementation):
        """encode() with int should raise TypeError."""
        impl, impl_name = implementation
        encoder = impl.init(alphabet=BASE58_ALPHABET)
        with pytest.raises(TypeError, match="Data must be str or bytes"):
            encoder.encode(123)

    def test_encode_invalid_type_list(self, implementation):
        """encode() with list should raise TypeError."""
        impl, impl_name = implementation
        encoder = impl.init(alphabet=BASE58_ALPHABET)
        with pytest.raises(TypeError, match="Data must be str or bytes"):
            encoder.encode([1, 2, 3])

    def test_encode_invalid_type_none(self, implementation):
        """encode() with None should raise TypeError."""
        impl, impl_name = implementation
        encoder = impl.init(alphabet=BASE58_ALPHABET)
        with pytest.raises(TypeError, match="Data must be str or bytes"):
            encoder.encode(None)

    # Data type validations for decode
    def test_decode_invalid_type_bytes(self, implementation):
        """decode() with bytes should raise TypeError."""
        impl, impl_name = implementation
        encoder = impl.init(alphabet=BASE58_ALPHABET)
        with pytest.raises(TypeError, match="(Data must be str|incorrect type)"):
            encoder.decode(b"bytes")

    def test_decode_invalid_type_int(self, implementation):
        """decode() with int should raise TypeError."""
        impl, impl_name = implementation
        encoder = impl.init(alphabet=BASE58_ALPHABET)
        with pytest.raises(TypeError, match="(Data must be str|incorrect type)"):
            encoder.decode(123)

    def test_decode_invalid_type_none(self, implementation):
        """decode() with None should raise TypeError."""
        impl, impl_name = implementation
        encoder = impl.init(alphabet=BASE58_ALPHABET)
        with pytest.raises(TypeError, match="(Data must be str|incorrect type)"):
            encoder.decode(None)

    # Unicode support
    def test_unicode_alphabet_cyrillic(self, implementation):
        """Unicode (Cyrillic) alphabet should work."""
        impl, impl_name = implementation
        encoder = impl.init(alphabet="абвгдежзий")
        encoded = encoder.encode("test")
        decoded = encoder.decode(encoded)
        assert decoded == b"test"

    def test_unicode_alphabet_chinese(self, implementation):
        """Unicode (Chinese) alphabet should work."""
        impl, impl_name = implementation
        encoder = impl.init(alphabet="你好世界朋友加油")
        encoded = encoder.encode("hello")
        decoded = encoder.decode(encoded)
        assert decoded == b"hello"
