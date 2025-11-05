"""Setup script for basex-python with Cython extensions."""
from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "basex._basex",
        ["src/basex/_basex.pyx"],
        extra_compile_args=["-O3"],
        define_macros=[
            ("CYTHON_TRACE", "0"),
        ],
    )
]

setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
        },
    ),
)
