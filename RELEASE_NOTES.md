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