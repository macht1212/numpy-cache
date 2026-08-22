# Release Notes – numpy-cache v0.1.2 🚀

## Overview

This release introduces a new **header inspection** capability, allowing users to peek into cache files without loading the actual array data. It also adds a **command‑line interface (CLI)** for quick file inspection from the terminal, and includes significant internal refactoring for better code maintainability.

---

## New Features

### 📋 Header Inspection (`inspect()`)

A new `inspect()` function is now available in the Python API. It reads the file header and returns a dictionary containing:

- `magic` – file format identifier
- `version` – cache format version
- `ndim` – number of dimensions
- `dtype` – NumPy data type code
- `uncompressed_size` – original array size in bytes
- `compressed_size` – compressed payload size in bytes
- `shape` – array dimensions as a tuple

This is useful for debugging, validating file integrity, and inspecting metadata without decompression overhead.

### 🖥️ Command‑Line Interface (CLI)

A new `numpy-cache` console script is now available. The first command implemented is `inspect`, which displays cache file headers directly in the terminal.

The CLI is built with **Click** and registered as both a Poetry script and a setuptools entry point, ensuring compatibility across installation methods.

---

## Internal Improvements

### Code Refactoring

Common operations have been extracted into reusable helper functions, improving code readability and maintainability:

- `shape_to_tuple` – converts header shape to a Python tuple
- `create_array_from_header` – constructs a NumPy array from header + data
- `validate_header_size` – checks uncompressed size limits
- `header_to_dict` – converts header to a Python dictionary

These changes reduce duplication across the codebase and make future enhancements easier.

## Dependency Changes

- Added `click` (≥8.4.2) as a dependency for the CLI.

---

# Release 0.1.1 – CI & PyPI Maintenance Release 🔧

**Release date:** 2026-08-21

This is a maintenance release focused on improving the project's build infrastructure and release automation. No functional changes have been made to the library code – **numpy-cache** remains as fast and reliable as in v0.1.0.

---

## What's Changed

### 🔧 Infrastructure Improvements

- **CI pipeline fully stabilized** – all workflows now pass on Python 3.12–3.14 across Linux, macOS.
- **PyPI releases automated** – binary wheels (manylinux, musllinux, macOS, Windows) are now built and uploaded automatically.

---

## Why Upgrade?

While v0.1.0 was already stable and production-ready, v0.1.1 ensures that:

- **Installing** via `pip install numpy-cache` works seamlessly on all modern platforms.
- **Contributing** is easier – CI tests run reliably for all pull requests.
- **Releasing** future versions will be fully automated and consistent.

No changes are required to your existing code.

# Release 0.1.0 – First Public Release 🚀

We are excited to announce the first release of **numpy-cache** – a lightweight, high‑performance disk cache for NumPy arrays powered by LZ4 compression.

## Why another cache?

When working with large arrays, you usually have to choose between:
- **Speed** (`np.save`) – but huge files.
- **Compression** (`np.savez_compressed`) – but painfully slow.

**numpy-cache** gives you **both**: near‑native speed and good compression, in a tiny package with no external dependencies beyond NumPy and LZ4.

## Key Features

- **Configurable acceleration** – tune speed vs. compression ratio (1–16).
- **All numeric dtypes** – `float32/64`, `int/uint` of all sizes, and `bool`.
- **Multi‑dimensional** – up to 8 dimensions.
- **Handles slices** – automatically makes non‑contiguous arrays contiguous.
- **Empty arrays** – saved and loaded correctly.
- **Fast I/O** – uses 1 MB buffering for optimal throughput.

## Performance Highlights (on Intel i5-1235U)

| Operation | Array Size | Time (ms) | vs. `np.savez_compressed` |
|-----------|------------|-----------|---------------------------|
| **Write** | 1 MB       | **0.76**  | 38× faster                |
| **Read**  | 1 MB       | **0.42**  | 11× faster                |
| **Write** | 100 MB*    | **~100**  | 27× faster                |
| **Read**  | 100 MB*    | **~93**   | 5× faster                 |

* extrapolated from benchmarks.

File sizes are typically **2× smaller** than `np.save` and close to `np.savez_compressed`.