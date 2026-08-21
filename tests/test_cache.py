import os
import tempfile

import numpy as np
import pytest
from numpy_cache._cache import (
    ACCELERATION_DEFAULT,
    ACCELERATION_MAX,
    ACCELERATION_MIN,
    MAGIC,
    MAX_DIMS,
    MAX_SIZE,
    VERSION,
    load,
    save,
)


@pytest.fixture
def temp_file():
    """Создаёт временный файл и удаляет его после теста."""
    fd, path = tempfile.mkstemp(suffix=".npc")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def sample_array():
    """Базовый массив для тестов."""
    return np.random.randn(100, 100).astype(np.float32)

def test_roundtrip(temp_file, sample_array):
    save(sample_array, temp_file)
    loaded = load(temp_file)
    np.testing.assert_array_equal(sample_array, loaded)


@pytest.mark.parametrize("dtype", [
    np.float32, np.float64,
    np.int8, np.int16, np.int32, np.int64,
    np.uint8, np.uint16, np.uint32, np.uint64,
    np.bool_,
])
def test_dtypes(temp_file, dtype):
    if dtype == np.bool_:
        arr = np.random.choice([True, False], size=(20, 20))
    else:
        arr = np.random.randint(0, 100, size=(20, 20)).astype(dtype)
    save(arr, temp_file)
    loaded = load(temp_file)
    np.testing.assert_array_equal(arr, loaded)


@pytest.mark.parametrize("shape", [(10, 10, 10), (5, 6, 7, 8)])
def test_multidimensional(temp_file, shape):
    arr = np.random.randn(*shape).astype(np.float32)
    save(arr, temp_file)
    loaded = load(temp_file)
    np.testing.assert_array_equal(arr, loaded)


def test_large_array(temp_file):
    arr = np.random.randn(1000, 1000).astype(np.float32)  # ~4 МБ
    save(arr, temp_file)
    loaded = load(temp_file)
    np.testing.assert_array_equal(arr, loaded)


def test_non_contiguous(temp_file):
    arr = np.random.randn(100, 100).astype(np.float32)
    sliced = arr[::2, ::2]
    save(sliced, temp_file)
    loaded = load(temp_file)
    np.testing.assert_array_equal(sliced, loaded)


@pytest.mark.parametrize("accel", [
    ACCELERATION_MIN,
    ACCELERATION_DEFAULT,
    ACCELERATION_MAX,
    1, 5, 10, 16,
])
def test_acceleration_valid(temp_file, sample_array, accel):
    save(sample_array, temp_file, acceleration=accel)
    loaded = load(temp_file)
    np.testing.assert_array_equal(sample_array, loaded)


@pytest.mark.parametrize("bad_accel", [0, 17, -1, 100])
def test_acceleration_invalid(temp_file, sample_array, bad_accel):
    with pytest.raises(ValueError, match="acceleration must be between"):
        save(sample_array, temp_file, acceleration=bad_accel)


def test_acceleration_effect_on_size(temp_file, sample_array):
    sizes = {}
    for accel in [1, 8, 16]:
        save(sample_array, temp_file, acceleration=accel)
        sizes[accel] = os.path.getsize(temp_file)
        os.remove(temp_file)
    assert sizes[16] >= sizes[1], "Higher acceleration should produce larger file"

@pytest.mark.parametrize("shape", [(0,), (0, 5), (3, 0, 4), (0, 0)])
def test_empty_array(temp_file, shape):
    arr = np.empty(shape, dtype=np.float32)
    save(arr, temp_file)
    loaded = load(temp_file)
    np.testing.assert_array_equal(arr, loaded)
    assert loaded.shape == arr.shape
    assert loaded.dtype == arr.dtype


def test_empty_array_with_dtype(temp_file):
    arr = np.empty((0, 5), dtype=np.int64)
    save(arr, temp_file)
    loaded = load(temp_file)
    np.testing.assert_array_equal(arr, loaded)
    assert loaded.dtype == np.int64

def test_max_dims(temp_file):
    shape = (2,) * MAX_DIMS
    arr = np.random.randn(*shape).astype(np.float32)
    save(arr, temp_file)
    loaded = load(temp_file)
    np.testing.assert_array_equal(arr, loaded)


def test_exceed_max_dims(temp_file):
    shape = (2,) * (MAX_DIMS + 1)
    arr = np.random.randn(*shape).astype(np.float32)
    with pytest.raises(ValueError, match="max supported is"):
        save(arr, temp_file)

def test_load_nonexistent_file():
    with pytest.raises(IOError, match="Cannot open file for reading"):
        load("/non/existent/path.npc")


def test_load_corrupted_file(temp_file):
    with open(temp_file, "wb") as f:
        f.write(b"GARBAGE")
    with pytest.raises(OSError, match="Failed to read header"):
        load(temp_file)


def test_load_invalid_magic(temp_file):
    arr = np.zeros((10,), dtype=np.float32)
    save(arr, temp_file)
    with open(temp_file, "r+b") as f:
        f.seek(80)
        f.write(b'\xEF\xBE\xAD\xDE')
    with pytest.raises(RuntimeError, match="Invalid file format"):
        load(temp_file)

def test_load_wrong_version(temp_file):
    arr = np.zeros((10,), dtype=np.float32)
    save(arr, temp_file)
    with open(temp_file, "r+b") as f:
        f.seek(84)
        f.write(b'\xFF\xFF\xFF\xFF')
    with pytest.raises(RuntimeError, match="Invalid file format"):
        load(temp_file)

def test_save_non_array(temp_file):
    with pytest.raises(TypeError, match="Expected a NumPy array"):
        save("not an array", temp_file)


def test_save_to_readonly_path():
    arr = np.zeros((10,), dtype=np.float32)
    with pytest.raises(IOError, match="Cannot open file for writing"):
        save(arr, "/dev/null/file_that_cannot_be_created")  # путь недоступен

def test_module_constants():
    assert MAX_DIMS == 8
    assert VERSION == 1
    assert MAGIC == "LZNC"
    assert MAX_SIZE == 1024 * 1024 * 1024
    assert ACCELERATION_MIN == 1
    assert ACCELERATION_MAX == 16
    assert ACCELERATION_DEFAULT == 4

@pytest.mark.parametrize("dtype", [np.complex64, np.complex128])
def test_complex_dtypes(temp_file, dtype):
    arr = np.random.randn(20, 20).astype(dtype)
    save(arr, temp_file)
    loaded = load(temp_file)
    np.testing.assert_array_equal(arr, loaded)

def test_overwrite(temp_file, sample_array):
    save(sample_array, temp_file)
    new_arr = np.ones_like(sample_array)
    save(new_arr, temp_file)
    loaded = load(temp_file)
    np.testing.assert_array_equal(new_arr, loaded)

def test_compression_reduces_size(temp_file):
    arr = np.zeros((500, 500), dtype=np.float32)
    save(arr, temp_file)
    compressed_size = os.path.getsize(temp_file)
    uncompressed_size = arr.nbytes
    header_size = 96
    assert compressed_size < uncompressed_size + header_size, \
        f"Compressed {compressed_size} >= {uncompressed_size + header_size}"

def test_many_dims(temp_file):
    shape = (2, 3, 4, 5, 6, 7, 8)
    arr = np.random.randn(*shape).astype(np.float32)
    save(arr, temp_file)
    loaded = load(temp_file)
    np.testing.assert_array_equal(arr, loaded)

def test_metadata_preserved(temp_file):
    arr = np.arange(24).reshape(2, 3, 4).astype(np.int16)
    save(arr, temp_file)
    loaded = load(temp_file)
    assert loaded.shape == (2, 3, 4)
    assert loaded.dtype == np.int16
    np.testing.assert_array_equal(arr, loaded)