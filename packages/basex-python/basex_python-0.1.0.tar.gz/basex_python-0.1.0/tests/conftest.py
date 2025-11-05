"""Pytest configuration for dual-implementation testing."""

import pytest


@pytest.fixture(params=["cython", "python"], ids=["cython", "python"])
def implementation(request):
    """Fixture that provides both Cython and Python implementations.

    This fixture runs each test twice:
    - Once with the Cython-compiled implementation
    - Once with the pure Python implementation

    This ensures both implementations produce identical results and
    prevents implementation-specific bugs.

    If Cython is not available, tests will fail (not skip) to ensure
    the compiled version is tested in CI/CD.

    Returns:
        tuple: (module, impl_name) where module has the same interface
               for both implementations
    """
    if request.param == "cython":
        try:
            from basex import _basex, presets

            # Create module-like object with same interface including presets
            class CythonImpl:
                Mode = _basex.Mode
                BaseXEncoder = _basex.BaseXEncoder
                init = staticmethod(_basex.init)
                encode = staticmethod(_basex.encode)
                decode = staticmethod(_basex.decode)
                b64 = presets.b64
                b32 = presets.b32
                b16 = presets.b16
                b58 = presets.b58
                b57 = presets.b57
                b56 = presets.b56

            return CythonImpl(), "cython"
        except ImportError as e:
            pytest.fail(
                f"Cython implementation not available: {e}\n"
                "Run 'uv pip install -e .' to compile Cython extensions"
            )
    else:
        # Import pure Python modules and create unified interface
        from basex import basex as py_impl, modes, presets

        # Create module-like object with same interface as _basex
        class PythonImpl:
            Mode = modes.Mode
            BaseXEncoder = py_impl.BaseXEncoder
            init = staticmethod(py_impl.init)
            encode = staticmethod(py_impl.encode)
            decode = staticmethod(py_impl.decode)
            b64 = presets.b64
            b32 = presets.b32
            b16 = presets.b16
            b58 = presets.b58
            b57 = presets.b57
            b56 = presets.b56

        return PythonImpl(), "python"
