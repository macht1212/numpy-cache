import gc
import os
import tempfile

import numpy as np
import pytest

from numpy_cache import load as cache_load
from numpy_cache import save as cache_save

SIZES = [
    ((100, 100), "1e4"),
    ((500, 500), "2.5e5"),
]

ACCELERATIONS = [1, 4, 16]

# ===================== WRITE BENCHMARKS =====================

@pytest.mark.parametrize("shape,label", SIZES)
@pytest.mark.parametrize("accel", ACCELERATIONS, ids=lambda a: f"accel={a}")
def test_write_cache(benchmark, shape, label, accel):
    arr = np.random.randn(*shape).astype(np.float32)
    with tempfile.NamedTemporaryFile(suffix=".npc", delete=False) as f:
        path = f.name
    try:
        def do():
            cache_save(arr, path, acceleration=accel)
        if shape[0] * shape[1] > 250000:
            benchmark.pedantic(do, iterations=5, rounds=3, warmup_rounds=1)
        else:
            benchmark(do)
        print(f"\nnumpy_cache (accel={accel}) write: {os.path.getsize(path)/1024/1024:.2f} MB")
    finally:
        if os.path.exists(path):
            os.remove(path)
        gc.collect()

@pytest.mark.parametrize("shape,label", SIZES)
def test_write_np_save(benchmark, shape, label):
    arr = np.random.randn(*shape).astype(np.float32)
    with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
        path = f.name
    try:
        def do():
            np.save(path, arr)
        if shape[0] * shape[1] > 250000:
            benchmark.pedantic(do, iterations=5, rounds=3, warmup_rounds=1)
        else:
            benchmark(do)
        print(f"\nnp.save write: {os.path.getsize(path)/1024/1024:.2f} MB")
    finally:
        if os.path.exists(path):
            os.remove(path)
        gc.collect()

@pytest.mark.parametrize("shape,label", SIZES)
def test_write_np_savez(benchmark, shape, label):
    arr = np.random.randn(*shape).astype(np.float32)
    with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
        path = f.name
    try:
        def do():
            np.savez(path, arr=arr)
        if shape[0] * shape[1] > 250000:
            benchmark.pedantic(do, iterations=5, rounds=3, warmup_rounds=1)
        else:
            benchmark(do)
        print(f"\nnp.savez write: {os.path.getsize(path)/1024/1024:.2f} MB")
    finally:
        if os.path.exists(path):
            os.remove(path)
        gc.collect()

@pytest.mark.parametrize("shape,label", SIZES)
def test_write_np_savez_compressed(benchmark, shape, label):
    arr = np.random.randn(*shape).astype(np.float32)
    with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
        path = f.name
    try:
        def do():
            np.savez_compressed(path, arr=arr)
        if shape[0] * shape[1] > 250000:
            benchmark.pedantic(do, iterations=5, rounds=3, warmup_rounds=1)
        else:
            benchmark(do)
        print(f"\nnp.savez_compressed write: {os.path.getsize(path)/1024/1024:.2f} MB")
    finally:
        if os.path.exists(path):
            os.remove(path)
        gc.collect()

# ===================== READ BENCHMARKS =====================

@pytest.mark.parametrize("shape,label", SIZES)
@pytest.mark.parametrize("accel", ACCELERATIONS, ids=lambda a: f"accel={a}")
def test_read_cache(benchmark, shape, label, accel):
    arr = np.random.randn(*shape).astype(np.float32)
    with tempfile.NamedTemporaryFile(suffix=".npc", delete=False) as f:
        path = f.name
    try:
        cache_save(arr, path, acceleration=accel)
        def do():
            return cache_load(path)
        if shape[0] * shape[1] > 250000:
            benchmark.pedantic(do, iterations=5, rounds=3, warmup_rounds=1)
        else:
            benchmark(do)
    finally:
        if os.path.exists(path):
            os.remove(path)
        gc.collect()

@pytest.mark.parametrize("shape,label", SIZES)
def test_read_np_save(benchmark, shape, label):
    arr = np.random.randn(*shape).astype(np.float32)
    with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
        path = f.name
    try:
        np.save(path, arr)
        def do():
            return np.load(path)
        if shape[0] * shape[1] > 250000:
            benchmark.pedantic(do, iterations=5, rounds=3, warmup_rounds=1)
        else:
            benchmark(do)
    finally:
        if os.path.exists(path):
            os.remove(path)
        gc.collect()

@pytest.mark.parametrize("shape,label", SIZES)
def test_read_np_savez(benchmark, shape, label):
    arr = np.random.randn(*shape).astype(np.float32)
    with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
        path = f.name
    try:
        np.savez(path, arr=arr)
        def do():
            data = np.load(path)
            return data['arr']
        if shape[0] * shape[1] > 250000:
            benchmark.pedantic(do, iterations=5, rounds=3, warmup_rounds=1)
        else:
            benchmark(do)
    finally:
        if os.path.exists(path):
            os.remove(path)
        gc.collect()

@pytest.mark.parametrize("shape,label", SIZES)
def test_read_np_savez_compressed(benchmark, shape, label):
    arr = np.random.randn(*shape).astype(np.float32)
    with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
        path = f.name
    try:
        np.savez_compressed(path, arr=arr)
        def do():
            data = np.load(path)
            return data['arr']
        if shape[0] * shape[1] > 250000:
            benchmark.pedantic(do, iterations=5, rounds=3, warmup_rounds=1)
        else:
            benchmark(do)
    finally:
        if os.path.exists(path):
            os.remove(path)
        gc.collect()