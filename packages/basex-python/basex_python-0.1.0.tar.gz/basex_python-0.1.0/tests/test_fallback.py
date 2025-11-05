"""Tests for fallback mechanism between Cython and Python implementations."""


def test_implementation_detection():
    """Verify that basex detects which implementation is loaded."""
    import basex

    assert hasattr(basex, "_implementation")
    assert basex._implementation in ("cython", "python")


def test_forced_python_fallback():
    """Test that pure Python implementation works when forced."""
    # Import Python modules directly
    from basex.modes import Mode
    from basex.basex import BaseXEncoder
    from basex.presets import b64, b58

    # Test basic functionality
    test_data = "Hello World!"

    # Test base64
    encoded = b64.encode(test_data)
    decoded = b64.decode(encoded)
    assert decoded == test_data.encode("utf-8")

    # Test base58
    encoded = b58.encode(test_data)
    decoded = b58.decode(encoded)
    assert decoded == test_data.encode("utf-8")

    # Test custom encoder
    encoder = BaseXEncoder("0123456789ABCDEF", Mode.RFC4648)
    encoded = encoder.encode("test")
    decoded = encoder.decode(encoded)
    assert decoded == b"test"


def test_api_consistency():
    """Verify that both implementations expose the same API."""
    import basex

    required_attrs = [
        "Mode",
        "BaseXEncoder",
        "init",
        "encode",
        "decode",
        "b64",
        "b32",
        "b16",
        "b58",
        "b57",
        "b56",
        "__version__",
    ]

    for attr in required_attrs:
        assert hasattr(basex, attr), f"Missing attribute: {attr}"


def test_implementation_results_match():
    """Verify that Cython and Python implementations produce identical results."""
    import basex
    from basex.basex import BaseXEncoder as PyEncoder
    from basex.modes import Mode

    test_cases = [
        ("", ""),
        ("a", "a"),
        ("foo", "foo"),
        ("Hello World!", "Hello World!"),
        (b"\x00\x00test", b"\x00\x00test"),
    ]

    alphabets = [
        (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
            Mode.RFC4648,
        ),
        ("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz", Mode.DEFAULT),
    ]

    for data, expected in test_cases:
        for alphabet, mode in alphabets:
            # Pure Python result
            py_encoder = PyEncoder(alphabet, mode)
            py_encoded = py_encoder.encode(data)
            py_decoded = py_encoder.decode(py_encoded)

            # basex module result (might be Cython or Python)
            basex_encoder = basex.BaseXEncoder(alphabet, mode)
            basex_encoded = basex_encoder.encode(data)
            basex_decoded = basex_encoder.decode(basex_encoded)

            # Results must match
            assert py_encoded == basex_encoded
            assert py_decoded == basex_decoded


def test_preset_consistency():
    """Verify that preset encoders work identically across implementations."""
    import basex
    from basex import presets

    test_data = "test data 123"

    preset_pairs = [
        (basex.b64, presets.b64),
        (basex.b32, presets.b32),
        (basex.b16, presets.b16),
        (basex.b58, presets.b58),
        (basex.b57, presets.b57),
        (basex.b56, presets.b56),
    ]

    for basex_preset, py_preset in preset_pairs:
        # Encode with both
        basex_encoded = basex_preset.encode(test_data)
        py_encoded = py_preset.encode(test_data)

        # Results must match
        assert basex_encoded == py_encoded

        # Decode with both
        basex_decoded = basex_preset.decode(basex_encoded)
        py_decoded = py_preset.decode(py_encoded)

        # Results must match
        assert basex_decoded == py_decoded
        assert basex_decoded == test_data.encode("utf-8")


def test_presets_use_cython_when_available():
    """Verify presets use Cython implementation when available."""
    import basex

    if basex._implementation == "cython":
        # When Cython is available, presets should use Cython BaseXEncoder
        assert basex.b64.__class__.__module__ == "basex._basex"
        assert basex.b32.__class__.__module__ == "basex._basex"
        assert basex.b16.__class__.__module__ == "basex._basex"
        assert basex.b58.__class__.__module__ == "basex._basex"
        assert basex.b57.__class__.__module__ == "basex._basex"
        assert basex.b56.__class__.__module__ == "basex._basex"
    else:
        # When Cython is not available, presets should use Python BaseXEncoder
        assert basex.b64.__class__.__module__ == "basex.basex"
        assert basex.b32.__class__.__module__ == "basex.basex"
        assert basex.b16.__class__.__module__ == "basex.basex"
        assert basex.b58.__class__.__module__ == "basex.basex"
        assert basex.b57.__class__.__module__ == "basex.basex"
        assert basex.b56.__class__.__module__ == "basex.basex"
