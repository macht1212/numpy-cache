# Changelog

## [0.1.2] – 2026-08-xx
### Added
- New `inspect()` function to read and display the header of a cache file without loading the actual data. Returns a dictionary containing magic, version, ndim, dtype, shape, and sizes.
- Supporting C helper functions: `shape_to_tuple`, `create_array_from_header`, `validate_header_size`, and `header_to_dict` for cleaner and safer header handling.
- Comprehensive test suite for the `inspect` functionality, covering valid files, empty arrays, multiple dtypes, multidimensional arrays, non‑contiguous arrays, and edge cases.

### Changed
- Refactored `cache_load` by extracting common operations into reusable helper functions, improving code readability and maintainability.
- Exposed inspect in the public API via `numpy_cache/__init__.py`.

### Fixed
- None.

### Deprecated
- None.

### Removed
- None

## [0.1.1] – 2026-08-21

### Added
- None.

### Changed
- CI, release, setup.py

### Fixed
- Problems with PyPi publishing.

### Deprecated
- None.

### Removed
- None

## [0.1.0] – 2026-08-21

### Added
- **Configurable acceleration** – `acceleration` parameter (1–16) for LZ4 compression speed/ratio trade‑off (default 4).
- **Support for empty arrays** – zero‑size arrays are now saved and loaded correctly.
- **Packed binary header** – `#pragma pack(push, 1)` ensures portability across compilers and architectures.
- **I/O buffering** – 1 MB buffers for faster file operations (`setvbuf`).
- **Detailed error messages** – includes `errno`, `strerror`, `ferror` for easier debugging.
- **Public constants** – `MAX_DIMS`, `VERSION`, `MAGIC`, `MAX_SIZE`, `ACCELERATION_MIN`, `ACCELERATION_MAX`, `ACCELERATION_DEFAULT` exposed to Python.
- **Unit tests** – full coverage for all dtypes, shapes, empty arrays, non‑contiguous inputs, and error cases.
- **Comparative benchmarks** – against `np.save`, `np.savez`, and `np.savez_compressed`.

### Changed
- **Header format** – removed `checksum` field (LZ4’s `LZ4_decompress_safe` already validates integrity); reduced header size from 100 to 96 bytes.
- **Header field order** – rearranged for clarity; now includes `uncompressed_size` and `compressed_size` first.
- **Build system** – switched to Poetry; improved `setup.py` with automatic LZ4 include detection.
- **Error handling** – more robust; proper cleanup of resources on failures.

### Fixed
- **Memory corruption** – fixed invalid pointer issues that caused `errno=14 (Bad address)` in earlier versions.
- **Incomplete writes** – resolved problem where `fwrite` would stop prematurely; now uses chunked writing and checks `ferror`.
- **Decompression mismatch** – ensured size validation for all cases.
- **Compilation warnings** – eliminated all warnings on GCC and Clang.

### Security
- LZ4 decompression uses `LZ4_decompress_safe` to prevent buffer overflows.
- Rejects files with oversized compressed/uncompressed data (>1 GB).

### Deprecated
- None.

### Removed
- **Checksum** – removed to reduce overhead and simplify the format.

---

## [0.0.1] – 2026-08-15 *(pre‑release, internal)*

> **Note:** This version was an early prototype and is **not recommended** for production use. It is kept for historical reference only.

### Added
- Basic `save` and `load` functions.
- LZ4 compression via `LZ4_compress_default`.
- Support for C‑contiguous numeric arrays (basic dtypes).
- A `checksum` field in the header (CRC32 placeholder, never implemented).
- Simple `setup.py` for building the C extension.

### Known Issues
- **Memory corruption** – `fwrite` often failed with `errno=14 (Bad address)`.
- **No buffering** – slow I/O on large files.
- **Header not packed** – potential alignment issues on different platforms.
- **Missing acceleration control** – compression speed was fixed.
- **Empty arrays not handled** – saving/loading empty arrays crashed or produced errors.
- **Poor error messages** – often just `"Failed to write compressed data"` without details.
- **Benchmarks absent** – no performance comparisons.
