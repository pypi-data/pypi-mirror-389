#!/usr/bin/env python3

from setuptools import setup, Extension
import sys
import platform

# Check if we're building from source distribution
IS_SDIST = "sdist" in sys.argv

# Only import these when actually building
if not IS_SDIST:
    from Cython.Build import cythonize
    import numpy


def get_compile_args():
    """Get platform-specific compile arguments."""
    if sys.platform == "win32":
        return ["/O2", "/openmp"]
    else:
        args = ["-O3", "-ffast-math"]
        if not (sys.platform == "darwin" and platform.machine() == "arm64"):
            args.append("-march=native")
        return args


def get_link_args():
    """Get platform-specific link arguments."""
    if sys.platform == "win32":
        return []
    else:
        args = ["-ffast-math"]
        if sys.platform != "darwin":
            args.append("-lm")
        return args


def get_openmp_args():
    """Get OpenMP flags for the platform."""
    if sys.platform == "win32":
        return (["/openmp"], [])
    elif sys.platform == "darwin":
        try:
            import subprocess

            result = subprocess.run(["brew", "--prefix", "libomp"], capture_output=True, text=True, check=True)
            libomp_prefix = result.stdout.strip()
            return (["-Xpreprocessor", "-fopenmp", f"-I{libomp_prefix}/include"], [f"-L{libomp_prefix}/lib", "-lomp"])
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: OpenMP not found on macOS. Install with: brew install libomp")
            return ([], [])
    else:
        return (["-fopenmp"], ["-fopenmp"])


# Base compile and link args
base_compile_args = get_compile_args()
base_link_args = get_link_args()
openmp_compile_args, openmp_link_args = get_openmp_args()

ext_modules = [
    # PSF*PSF processing
    Extension(
        "iocbio.fcs.models.psf.engines.psfmult",
        sources=["iocbio/fcs/models/psf/engines/psfmult.pyx"],
        language="c++",
        extra_compile_args=base_compile_args,
        extra_link_args=base_link_args,
    ),
    # Helper utility functions for multiplication and dot products
    Extension(
        "iocbio.fcs.models.psf.engines.prodtools",
        sources=["iocbio/fcs/models/psf/engines/prodtools.pyx"],
        language="c++",
        extra_compile_args=base_compile_args + openmp_compile_args,
        extra_link_args=base_link_args + openmp_link_args,
    ),
]

# Only cythonize when building, not when creating sdist
if IS_SDIST:
    setup_kwargs = {
        "ext_modules": ext_modules,
    }
else:
    setup_kwargs = {
        "ext_modules": cythonize(ext_modules, annotate=True, language_level="3"),
        "include_dirs": [numpy.get_include()],
    }

setup(
    **setup_kwargs,
)
