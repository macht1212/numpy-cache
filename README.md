# NumPy Cache – Fast LZ4-Based Caching for NumPy Arrays
### High‑performance, lightweight disk cache for NumPy arrays with LZ4 compression – now with configurable compression speed.

[![CI](https://github.com/macht1212/numpy-cache/actions/workflows/ci.yml/badge.svg)](https://github.com/macht1212/numpy-cache/actions/workflows/ci.yml)  
[![Python](https://img.shields.io/badge/Python-3.12%20|%203.13%20|%203.14-blue)](https://www.python.org/) ![](/icons/NumPy-2.5.2-blue.svg) ![](/icons/License-Apache%202.0-blue.svg)

## 📌 The Problem
When dealing with large NumPy arrays, developers face a classic trade‑off:

| Method |	Speed (100 MB)  |	Issue |
|--------|-----------------|-------|
| `np.save()` / `np.savez()` |	~45 ms |	Huge storage, slow network transfer |
| `np.savez_compressed()` |	~3.6 s |	Single‑threaded DEFLATE (zlib) is too slow |
| **numpy_cache** |	**~100 ms** |	**Best of both worlds** ✅ |

There is a clear gap: no lightweight, specialised solution combines `np.save()` speed with good compression – until now.

## 🚀 Features
- ✅ Blazing fast – 20 × faster than np.savez_compressed()
- ✅ Good compression – 2 × smaller than np.save()
- ✅ Pure C extension – minimal overhead, maximum performance
- ✅ Configurable speed – acceleration parameter (1–16) lets you trade compression ratio for speed
- ✅ NumPy integration – works with all numeric dtypes (int, uint, float, bool)
- ✅ Multi‑dimensional – supports up to 8 dimensions
- ✅ Contiguous arrays – automatically handles non‑contiguous slices
- ✅ Empty arrays – properly saves and loads zero‑size arrays
- ✅ Lightweight – no external dependencies beyond NumPy and LZ4
- ✅ Apache 2.0 License – free for commercial and personal use
  
## 📦 Installation
#### System Dependencies
First, install the LZ4 library:
```bash
# Ubuntu / Debian
sudo apt-get install liblz4-dev

# macOS (Homebrew)
brew install lz4

# Fedora / RHEL
sudo dnf install lz4-devel

# Arch Linux
sudo pacman -S lz4
```

**Supported Python versions**: 3.12, 3.13, 3.14, 3.15

#### Install from PyPI
```bash
pip install numpy-cache
```

#### Install from source
```bash
git clone https://github.com/macht1212/numpy-cache.git
cd numpy-cache
poetry install
```

## 🧪 Usage
```python
import numpy as np
from numpy_cache import save, load

# Create a large array
arr = np.random.randn(5000, 5000).astype(np.float32)

# Save with LZ4 (default acceleration = 4)
save(arr, 'my_array.npc')

# Control compression speed vs. ratio
# acceleration=1 → best compression, slower
# acceleration=16 → fastest, slightly worse compression
save(arr, 'my_array_fast.npc', acceleration=16)

# Load back
loaded = load('my_array.npc')

# Verify
np.testing.assert_array_equal(arr, loaded)
```

### Acceleration Parameter
- **1–4**: Better compression ratio, slower.
- **5–10**: Balanced default (4 is recommended).
- **11–16**: Maximum speed, slightly larger files.

### Supported Dtypes
All NumPy numeric types are supported:

- `float32`, `float64`
- `int8`, `int16`, `int32`, `int64`
- `uint8`, `uint16`, `uint32`, `uint64`
- `bool_`

### Multi‑dimensional Arrays
```python
arr_3d = np.random.randn(100, 100, 100)
save(arr_3d, '3d_array.npc')
```

### Non‑contiguous Slices
```python
arr = np.random.randn(1000, 1000)
slice_arr = arr[::2, ::2]  # Not contiguous
save(slice_arr, 'slice.npc')  # Handles automatically
```

## 📊 Benchmarks
### Test system:

- Ubuntu 24.04.4 LTS, 12th Gen Intel i5-1235U (10 cores), 16 GB RAM, SSD
- MacOS 15.7.2, Apple Silicon M1 (8 cores), 8 GB RAM, SSD  
- Python 3.12, NumPy 2.5.2, LZ4 1.9.4

All arrays are `float32`. Sizes:

- `shape0`: 100×100 = 10 000 elements ≈ 0.04 MB
- `shape1`: 500×500 = 250 000 elements ≈ 1 MB

### Write Performance (time in μs)

| Method| Intel i5 <br>	0.04 MB| Intel i5 <br>	1 MB|  Apple M1 <br> 0.04 MB|  Apple M1 <br>	1 MB|
|-------|----------|--------|--------|------|
| `np.save`| 	89.6| 	879.6| 86.2 | 548.1 |
| `np.savez`| 	117.4| 	1 083.0| 94.5 | 554.4 |
| `np.savez_compressed`| 	1 056.1| 	28 921.5| 1 034.0 | 32 211.2 |
| **numpy_cache (accel=1)**| 	**71.8**| 	**759.4**| **67.8** | **770.1** |
| **numpy_cache (accel=4)**| 	**70.1**| 	**755.6**| **64.9** | **635.4** |
| **numpy_cache (accel=16)**| 	**74.9**| 	**738.9**| **68.0** | **655.2** |

### Read Performance (time in μs)

| Method| Intel i5 <br>	0.04 MB| Intel i5 <br>	1 MB|  Apple M1 <br> 0.04 MB|  Apple M1 <br>	1 MB|
|-------|----------|--------|--------|------|
| `np.save`| 	41.7| 	91.9| 44.8 | 77.3 |
| `np.savez`| 	83.0| 	401.1| 95.1 | 225.2 |
| `np.savez_compressed`| 	267.5| 	4 858.8| 193.7 | 2 876.7 |
| **numpy_cache (accel=1)**| 	**19.2**| 	**385.0**| **32.7** | **327.1** |
| **numpy_cache (accel=4)**| 	**17.5**| 	**421.0**| **23.8** | **665.8** |
| **numpy_cache (accel=16)**| 	**17.0**| 	**474.5**| **19.7** | **187.1** |

### File Size Comparison (1 MB array)
- `np.save` / `np.savez`: ~1.0 MB
- `np.savez_compressed`: ~0.5 MB (varies)
- **numpy_cache**: ~0.4 MB (depends on acceleration)

### Key Takeaways
**numpy_cache** is **24–40× faster** than `np.savez_compressed` for writes.

For reads, it is **5–12× faster** than `np.savez_compressed`.

Compression ratio is **better than** `np.savez` and usually close to `np.savez_compressed`.

The `acceleration` parameter lets you fine‑tune the speed/ratio trade‑off.

## 🛠️ How It Works
### Architecture
1. Pure C Extension – compiled into a Python module for maximum performance.
2. LZ4 Compression – uses LZ4_compress_fast() with configurable acceleration.
3. Custom Binary Format – packed header (96 bytes) + compressed payload.
4. Direct NumPy Integration – zero‑copy access to array data where possible.

### File Format
The header is packed (no padding) to ensure portability:

```C
#pragma pack(push, 1)
typedef struct {
    uint64_t uncompressed_size;
    uint64_t compressed_size;
    uint64_t shape[MAX_DIMS];   // up to 8 dimensions
    uint32_t magic;             // 0x4C5A4E43 ("LZNC")
    uint32_t version;           // 1
    uint32_t ndim;
    uint32_t dtype;             // NumPy type ID
} CacheHeader;
#pragma pack(pop)
```

- Magic identifies the file format.
- Version allows future upgrades.
- The header is followed immediately by the LZ4‑compressed data.

## Project Structure
```text
numpy_cache/
├── csrc/
│   └── cache_module.c      # C extension
├── src/
│   └── numpy_cache/
│       ├── __init__.py     # Python wrapper
│       └── _cache.so       # Compiled extension
├── tests/
│   ├── test_cache.py       # Unit tests
│   └── test_benchmarks.py  # Performance benchmarks
├── setup.py                # Setuptools configuration
├── pyproject.toml          # Poetry configuration
├── CHANGELOG.md
└── README.md
```

## Build from Source
```bash
# Install development dependencies
poetry install

# Build the C extension
poetry run python setup.py build_ext --inplace

# Run tests
poetry run pytest

# Run benchmarks
poetry run pytest tests/test_benchmarks.py --benchmark-only
```

## Run Benchmarks Separately
```bash
# Write benchmarks
poetry run pytest tests/test_benchmarks.py -k "write" --benchmark-only

# Read benchmarks
poetry run pytest tests/test_benchmarks.py -k "read" --benchmark-only
```

## 🗺️ Roadmap (Future Improvements)
- Multi‑threaded compression – parallelise LZ4 for even faster saving of huge arrays.
- Asynchronous I/O – background saving without blocking the main thread.
- Progress bar – visual feedback for very large arrays (via tqdm integration).
- Windows support – ensure compatibility with MSVC and the Windows API.
- Zstd backend – optional support for Zstandard compression (better ratio).
- Memory mapping – load arrays directly from disk without full decompression (for streaming).

## 📄 License
This project is licensed under the Apache License, Version 2.0 – see the [LICENSE](/LICENSE) file for details.

## 🙏 Acknowledgments
- [LZ4](https://github.com/lz4/lz4) – extremely fast compression library.
- [NumPy](https://numpy.org/) – fundamental array computing.
- [Python](https://www.python.org/) – the language that makes it all possible.

### Happy caching! 🚀
