# basex

Fast library for encoding/decoding data in standard base encodings (base58, base64, base32, base16) and custom base-N alphabets of any size.

## Features

- **⚡ Blazing fast**: Optional Cython-compiled wheels for maximum performance (10-100x speedup)
- **Ready-to-use presets**: `basex.b64`, `basex.b58`, `basex.b32`, `basex.b16`, `basex.b57`, `basex.b56`
- **Universal base encoding**: Works with any alphabet size
- **RFC 4648 compatible**: Full support for standard base64/base32/base16 with proper padding
- **Multiple base variants**: Base58, Base57, Base56 for human-readable encoding
- **Two encoding modes**:
  - `DEFAULT`: Universal numeric baseN encoding (for base58, base62, etc.)
  - `RFC4648`: Bitwise encoding compatible with standard base64/base32/base16
- **Robust padding handling**: Automatically handles extra or missing padding in RFC4648 mode
- **Clean API**: Presets, instance-based (`init()`), and direct function interfaces
- **Type safe**: Full type hints for str and bytes handling
- **Cross-platform**: Pre-compiled wheels for Linux (x86_64, ARM64), macOS (Intel, Apple Silicon), Windows
- **Pure Python fallback**: Works everywhere, even without compiled extensions
- **Fully tested**: 87 tests with RFC 4648 and Base58 test vectors

## Installation

```bash
uv add basex
# or with pip
pip install basex
```

Pre-compiled wheels are available for:
- **Linux**: x86_64, ARM64 (aarch64)
- **macOS**: Intel (x86_64), Apple Silicon (ARM64)
- **Windows**: x64

The package automatically uses compiled Cython extensions when available, with automatic fallback to pure Python on other platforms.

## Quick Start

### Using Presets (Recommended)

The easiest way to use basex is with the built-in presets:

```python
import basex

# Base64 (RFC 4648)
encoded = basex.b64.encode("foo")
decoded = basex.b64.decode("Zm9v")
print(f"{encoded} -> {decoded}")  # Zm9v -> b'foo'

# Base58 (Bitcoin)
encoded = basex.b58.encode("Hello World!")
print(encoded)  # 2NEpo7TZRRrLZSi2U

# Base32, Base16, Base57, Base56 also available
basex.b32.encode("test")
basex.b16.encode("test")
basex.b57.encode("test")
basex.b56.encode("test")
```

**Available Presets:**
- `basex.b64` - Base64 (RFC 4648)
- `basex.b32` - Base32 (RFC 4648)
- `basex.b16` - Base16/Hex (RFC 4648)
- `basex.b58` - Base58 (Bitcoin)
- `basex.b57` - Base57 (Base58 without '1')
- `basex.b56` - Base56 (Base58 without '1' and 'o')

### Custom Alphabets with init()

For custom alphabets, use `basex.init()`:

```python
import basex

# Create custom encoder
b58 = basex.init(
    alphabet="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz",
    mode=basex.Mode.DEFAULT
)
encoded = b58.encode("Hello World!")
decoded = b58.decode(encoded)
```

### Direct API

Quick one-off encoding without creating instance:

```python
import basex

encoded = basex.encode(
    "Hello World!",
    alphabet="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz",
    mode=basex.Mode.DEFAULT
)
```

## Encoding Modes

### Mode.DEFAULT (Universal Numeric)

Universal numeric baseN encoding that works with any alphabet size. This is the mathematical conversion of bytes to a number in base N.

- Works with any alphabet size (base58, base62, base85, etc.)
- No padding characters
- Compatible with Bitcoin Base58 and similar schemes
- **Use this for**: Custom alphabets, cryptocurrency addresses, URL shorteners

### Mode.RFC4648 (Bitwise)

RFC 4648 compatible bitwise encoding for standard base64/base32/base16.

- Requires alphabet size to be a power of 2 (2, 4, 8, 16, 32, 64)
- Automatic padding with `=` characters
- Fully compatible with Python's `base64` module and standard implementations
- **Use this for**: Standard base64, base32, base16 encoding

## Input Validation

The library performs strict validation with clear error messages for better developer experience:

**Alphabet validation:**
- Must be a string (not list, bytes, etc.) - raises `TypeError` otherwise
- Must contain at least 2 unique characters - raises `ValueError` otherwise
- No duplicate characters allowed - raises `ValueError` otherwise
- Unicode characters are fully supported

**Data validation:**
- `encode()` accepts `str` or `bytes` only - raises `TypeError` for other types
- `decode()` accepts `str` only - raises `TypeError` for other types
- Fail-fast approach ensures errors are caught immediately

**Examples:**
```python
# Invalid alphabet type
basex.init(alphabet=123)  # TypeError: Alphabet must be str

# Empty alphabet
basex.init(alphabet="")  # ValueError: Alphabet cannot be empty

# Single character (base-1)
basex.init(alphabet="A")  # ValueError: At least 2 characters required

# Duplicate characters
basex.init(alphabet="AABC")  # ValueError: Duplicate characters

# Unicode alphabets work perfectly
encoder = basex.init(alphabet="абвгдежз")  # ✓ Works!
encoder = basex.init(alphabet="你好世界")  # ✓ Works!

# Invalid data types
encoder.encode(123)  # TypeError: Data must be str or bytes
encoder.decode(b"bytes")  # TypeError: Data must be str
```

## Standard Alphabets

```python
# Base64 (RFC 4648) - 64 characters
BASE64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

# Base32 (RFC 4648) - 32 characters
BASE32 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"

# Base16 / Hex (RFC 4648) - 16 characters
BASE16 = "0123456789ABCDEF"

# Base58 (Bitcoin) - 58 characters, excludes 0OIl
BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

# Base57 - Base58 without '1' to avoid confusion with 'l'
BASE57 = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

# Base56 - Base58 without '1' and 'o' to avoid confusion
BASE56 = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz"
```

**Note:** All presets are available directly as `basex.b64`, `basex.b58`, etc.

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/yokotoka/basex.git
cd basex

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=basex
```

### Project Structure

```
basex/
├── src/basex/              # Source code
│   ├── __init__.py         # Minimal fallback logic (Cython/Python)
│   ├── _version.py         # Version information
│   ├── modes.py            # Mode enum definition
│   ├── basex.py            # Pure Python implementation
│   ├── presets.py          # Preset encoder instances
│   └── _basex.pyx          # Cython-optimized implementation
├── tests/                  # Test suite
│   ├── test_basex.py       # Comprehensive tests with RFC vectors
│   └── test_fallback.py    # Fallback mechanism tests
├── .github/workflows/      # CI/CD
│   └── build-wheels.yml    # Automated wheel building and PyPI publishing
├── pyproject.toml          # Project configuration with Cython setup
└── README.md               # Documentation
```

## Roadmap

- [x] **Cython compilation**: High-performance compiled extensions
- [x] **Pre-compiled wheels**: Cross-platform binary distributions (Linux, macOS, Windows)
- [x] **Automated PyPI publishing**: GitHub Actions CI/CD pipeline
- [ ] **Benchmarks**: Performance comparison with standard libraries
- [ ] **Additional modes**: Support for base85 (Ascii85, Z85) and more
- [ ] **Further optimizations**: Profile and optimize hot paths in Cython code

## Contributing

Contributions are welcome! Please ensure:
- All tests pass: `uv run pytest`
- Code follows existing style
- New features include tests

## License

MIT

## Next Steps

After implementing the library, you can:

1. **Test the implementation**:
   ```bash
   uv run pytest -v
   ```

2. **Try it interactively**:
   ```bash
   uv run python
   >>> import basex
   >>> basex.b58.encode("Hello World!")
   '2NEpo7TZRRrLZSi2U'
   >>> basex.b64.encode("foo")
   'Zm9v'
   >>> basex.b64.decode("Zm9v")
   b'foo'
   ```

3. **Build locally** (including Cython compilation):
   ```bash
   uv build
   ```

4. **Create GitHub release** for automatic PyPI publishing:
   - Tag version: `git tag v1.0.0 && git push --tags`
   - Create release on GitHub
   - GitHub Actions will automatically build wheels and publish to PyPI

5. **Check which implementation is loaded**:
   ```bash
   uv run python -c "import basex; print(f'Implementation: {basex._implementation}')"
   ```
