import os
import subprocess
import sys

import numpy as np
from setuptools import Extension, setup

np_include = np.get_include()

lz4_include_dirs = []

standard_paths = [
    "/usr/include",
    "/usr/local/include",
    "/opt/homebrew/include",
]

for path in standard_paths:
    if os.path.exists(os.path.join(path, "lz4.h")):
        lz4_include_dirs.append(path)
        break

if not lz4_include_dirs:
    try:
        result = subprocess.run(
            ["pkg-config", "--cflags-only-I", "liblz4"],
            capture_output=True,
            text=True,
            check=True,
        )

        for flag in result.stdout.split():
            if flag.startswith("-I"):
                lz4_include_dirs.append(flag[2:])

    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

if not lz4_include_dirs:
    for base in ["/usr", "/usr/local", "/opt/homebrew"]:
        for root, dirs, files in os.walk(base):
            if "lz4.h" in files:
                lz4_include_dirs.append(root)
                break

        if lz4_include_dirs:
            break

if not lz4_include_dirs:
    raise RuntimeError(
        "lz4.h not found. Please install liblz4-dev (Ubuntu) or lz4 (macOS)."
    )

library_dirs = []

for libdir in [
    "/usr/lib",
    "/usr/local/lib",
    "/opt/homebrew/lib",
]:
    if os.path.exists(libdir):
        library_dirs.append(libdir)

extra_compile_args = ["-O3"] if sys.platform != "win32" else []

cache_module = Extension(
    "numpy_cache._cache",
    sources=["csrc/cache_module.c"],
    include_dirs=[np_include] + lz4_include_dirs,
    library_dirs=library_dirs,
    libraries=["lz4"],
    extra_compile_args=extra_compile_args,
)

print("=== Build configuration ===")
print(f"NumPy include: {np_include}")
print(f"LZ4 include paths: {lz4_include_dirs}")
print(f"Library dirs: {library_dirs}")
print(f"Compile args: {extra_compile_args}")
print("===========================")

setup(
    name="numpy-cache",
    version="0.1.2",
    packages=["numpy_cache"],
    package_dir={"": "src"},
    ext_modules=[cache_module],
    zip_safe=False,
    entry_points={
    'console_scripts': [
        'numpy-cache=numpy_cache.__main__:cli',
        ],
    },
)