#include <Python.h>
#include <numpy/arrayobject.h>
#include <lz4.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <errno.h>

#define CACHE_MAGIC               0x4C5A4E43
#define CACHE_VERSION             1
#define MAX_DIMS                  8
#define MAX_SIZE                  1024ULL * 1024 * 1024
#define LZ4_ACCELERATION_DEFAULT  4
#define LZ4_ACCELERATION_MIN      1
#define LZ4_ACCELERATION_MAX      16

#pragma pack(push, 1);
typedef struct {
  uint64_t uncompressed_size;
  uint64_t compressed_size;
  uint64_t shape[MAX_DIMS];
  uint32_t magic;
  uint32_t version;
  uint32_t ndim;
  uint32_t dtype;
} CacheHeader;
#pragma pack(pop);

static PyArrayObject* ensure_contiguous(PyObject* obj) {
  if (!PyArray_Check(obj)) {
    PyErr_SetString(PyExc_TypeError, "Expected a NumPy array");
    return NULL;
  }
  PyArrayObject* arr = (PyArrayObject*)obj;
  if (PyArray_IS_C_CONTIGUOUS(arr)) {
    Py_INCREF(arr);
    return arr;
  }
  PyArrayObject* copy = (PyArrayObject*)PyArray_NewCopy(arr, NPY_CORDER);
  if (!copy) {
    PyErr_SetString(PyExc_RuntimeError, "Failed to make a contiguous copy of the array");
    return NULL;
  }
  return copy;
}

static int write_cache_file(const char* path, const CacheHeader* header, const void* compressed_data) {
  FILE* f = fopen(path, "wb");
  if (!f) {
    PyErr_Format(PyExc_IOError, "Cannot open file for writing: %s", strerror(errno));
    return -1;
  }
  
  if (setvbuf(f, NULL, _IOFBF, 1 << 20) != 0) {};

  if (fwrite(header, sizeof(CacheHeader), 1, f) != 1) {
    PyErr_SetString(PyExc_IOError, "Failed to write header");
    fclose(f);
    return -1;
  }

  if (header->compressed_size > 0) {
    size_t to_write = (size_t)header->compressed_size;
    size_t written = fwrite(compressed_data, 1, to_write, f);
    if (written != to_write) {
      PyErr_Format(PyExc_OSError,
                   "Failed to write compressed data: wrote %zu of %llu bytes, errno=%d (%s), ferror=%d",
                   written,
                   (unsigned long long)header->compressed_size,
                   errno, strerror(errno),
                   ferror(f));
      fclose(f);
      return -1;
    }
  }

  if (fflush(f) != 0) {
    PyErr_Format(PyExc_OSError, "Failed to flush file: %s", strerror(errno));
    fclose(f);
    return -1;
  }

  if (fclose(f) != 0) {
    PyErr_Format(PyExc_OSError, "Failed to close file: %s", strerror(errno));
    return -1;
  }
  return 0;
}

static int read_cache_file(const char* path, CacheHeader* header, void** compressed_data) {
  FILE* f = fopen(path, "rb");
  if (!f) {
    PyErr_Format(PyExc_IOError, "Cannot open file for reading: %s", strerror(errno));
    return -1;
  }

  if (setvbuf(f, NULL, _IOFBF, 1 << 20) != 0) {};

  if (fread(header, sizeof(CacheHeader), 1, f) != 1) {
    PyErr_SetString(PyExc_IOError, "Failed to read header");
    fclose(f);
    return -1;
  }

  if (header->magic != CACHE_MAGIC || header->version != CACHE_VERSION) {
    PyErr_SetString(PyExc_RuntimeError, "Invalid file format");
    fclose(f);
    return -1;
  }

  if (header->compressed_size > MAX_SIZE) {
    PyErr_SetString(PyExc_RuntimeError, "Compressed size too large (>1GB)");
    fclose(f);
    return -1;
  }

  *compressed_data = malloc(header->compressed_size);
  if (!*compressed_data) {
    PyErr_NoMemory();
    fclose(f);
    return -1;
  }

  if (header->compressed_size > 0) {
    size_t read = fread(*compressed_data, 1, header->compressed_size, f);
    if (read != header->compressed_size) {
      PyErr_SetString(PyExc_IOError, "Failed to read compressed data");
      free(*compressed_data);
      fclose(f);
      return -1;
    }
  }

  if (fclose(f) != 0) {
    PyErr_Format(PyExc_OSError, "Failed to close file: %s", strerror(errno));
    free(*compressed_data);
    return -1;
  }
  return 0;
}

static PyObject* cache_save(PyObject* self, PyObject* args, PyObject* kwargs) {
  PyObject* obj = NULL;
  const char* path = NULL;
  int acceleration = LZ4_ACCELERATION_DEFAULT;

  static char* kwlist[] = {"array", "path", "acceleration", NULL};
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "Os|i", kwlist, &obj, &path, &acceleration))
    return NULL;

  if (acceleration < LZ4_ACCELERATION_MIN || acceleration > LZ4_ACCELERATION_MAX) {
    PyErr_Format(PyExc_ValueError, 
                     "acceleration must be between %d and %d, got %d",
                     LZ4_ACCELERATION_MIN, LZ4_ACCELERATION_MAX, 
                     acceleration);
    return NULL;
  }

  PyArrayObject* arr = ensure_contiguous(obj);
  if (!arr) return NULL;

  npy_intp ndim = PyArray_NDIM(arr);
  if (ndim > MAX_DIMS) {
    PyErr_Format(PyExc_ValueError, "Array has %d dimensions, max supported is %d", (int)ndim, MAX_DIMS);
    Py_DECREF(arr);
    return NULL;
  }

  npy_intp* shape = PyArray_DIMS(arr);
  npy_intp total_size = PyArray_NBYTES(arr);
  int dtype_num = PyArray_TYPE(arr);
  void* data = PyArray_DATA(arr);

  if (total_size > INT_MAX) {
    PyErr_SetString(PyExc_ValueError, "Array too large for LZ4 compression (max 1GB)");
    Py_DECREF(arr);
    return NULL;
  }

  CacheHeader header;
  memset(&header, 0, sizeof(header));
  header.magic = CACHE_MAGIC;
  header.version = CACHE_VERSION;
  header.ndim = (uint32_t)ndim;
  for (int i = 0; i < ndim; ++i) header.shape[i] = (uint64_t)shape[i];
  header.dtype = (uint32_t)dtype_num;
  header.uncompressed_size = (uint64_t)total_size;

  if (total_size == 0) {
    header.compressed_size = 0;
    int res = write_cache_file(path, &header, NULL);
    Py_DECREF(arr);
    if (res != 0) return NULL;
    Py_RETURN_NONE;
  }

  int max_compressed_size = LZ4_compressBound((int)total_size);
  if (max_compressed_size <= 0) {
    PyErr_SetString(PyExc_RuntimeError, "Invalid LZ4 compression bound");
    Py_DECREF(arr);
    return NULL;
  }

  void* compressed_data = malloc(max_compressed_size);
  if (!compressed_data) {
    PyErr_NoMemory();
    Py_DECREF(arr);
    return NULL;
  }

  int compressed_size = LZ4_compress_fast((const char*)data, (char*)compressed_data,
                                          (int)total_size, max_compressed_size, acceleration);
  if (compressed_size <= 0) {
    PyErr_SetString(PyExc_RuntimeError, "LZ4 compression failed");
    free(compressed_data);
    Py_DECREF(arr);
    return NULL;
  }

  if (compressed_size > max_compressed_size) {
    PyErr_SetString(PyExc_RuntimeError, "LZ4 compressed size exceeds bound");
    free(compressed_data);
    Py_DECREF(arr);
    return NULL;
  }

  header.compressed_size = (uint64_t)compressed_size;

  int res = write_cache_file(path, &header, compressed_data);
  free(compressed_data);
  Py_DECREF(arr);

  if (res != 0) return NULL;
  Py_RETURN_NONE;
}

static PyObject* cache_load(PyObject* self, PyObject* args) {
  const char* path = NULL;
  if (!PyArg_ParseTuple(args, "s", &path)) return NULL;

  CacheHeader header;
  void* compressed_data = NULL;

  if (read_cache_file(path, &header, &compressed_data) != 0) return NULL;

  if (header.uncompressed_size > MAX_SIZE) {
    PyErr_SetString(PyExc_RuntimeError, "Uncompressed size too large (>1GB)");
    free(compressed_data);
    return NULL;
  }

  if (header.uncompressed_size > INT_MAX) {
    PyErr_SetString(PyExc_RuntimeError, "Uncompressed size too large for LZ4");
    free(compressed_data);
    return NULL;
  }

  if (header.uncompressed_size == 0) {
    free(compressed_data);
    PyArray_Descr* descr = PyArray_DescrFromType((int)header.dtype);
    if (!descr) {
        PyErr_SetString(PyExc_RuntimeError, "Unsupported dtype");
        return NULL;
    }
    npy_intp dims[MAX_DIMS];
    for (int i = 0; i < (int)header.ndim; ++i)
        dims[i] = (npy_intp)header.shape[i];
    return (PyObject*)PyArray_Zeros((int)header.ndim, dims, descr, 0);
  }

  void* decompressed_data = malloc(header.uncompressed_size);
  if (!decompressed_data) {
    PyErr_NoMemory();
    free(compressed_data);
    return NULL;
  }

  int decompressed_size = LZ4_decompress_safe((const char*)compressed_data,
                                              (char*)decompressed_data,
                                              (int)header.compressed_size,
                                              (int)header.uncompressed_size);
  free(compressed_data);

  if (decompressed_size < 0) {
    PyErr_SetString(PyExc_RuntimeError, "LZ4 decompression failed");
    free(decompressed_data);
    return NULL;
  }

  if ((uint64_t)decompressed_size != header.uncompressed_size) {
    PyErr_SetString(PyExc_RuntimeError, "Decompressed size mismatch");
    free(decompressed_data);
    return NULL;
  }

  PyArray_Descr* descr = PyArray_DescrFromType((int)header.dtype);
  if (!descr) {
    PyErr_SetString(PyExc_RuntimeError, "Unsupported dtype");
    free(decompressed_data);
    return NULL;
  }

  npy_intp dims[MAX_DIMS];
  for (int i = 0; i < (int)header.ndim; ++i)
    dims[i] = (npy_intp)header.shape[i];

  PyArrayObject* arr = (PyArrayObject*)PyArray_NewFromDescr(
          &PyArray_Type,
          descr,
          (int)header.ndim,
          dims,
          NULL,
          decompressed_data,
          NPY_ARRAY_OWNDATA,
          NULL
  );

  if (!arr) {
    PyErr_SetString(PyExc_RuntimeError, "Failed to create NumPy array");
    free(decompressed_data);
    return NULL;
  }

  return (PyObject*)arr;
}

static PyObject* inspect_header(PyObject* self, PyObject* args) {
  const char* path = NULL;
  if (!PyArg_ParseTuple(args, "s", &path))
      return NULL;

  FILE* f = fopen(path, "rb");
  if (!f) {
      PyErr_Format(PyExc_IOError, "Cannot open file for reading: %s", strerror(errno));
      return NULL;
  }

  CacheHeader header;
  size_t n_bytes = sizeof(header);

  if (fread(&header, n_bytes, 1, f) != 1) {
      PyErr_SetString(PyExc_IOError, "Failed to read header (file too short or corrupt)");
      fclose(f);
      return NULL;
  }

  if (fclose(f) != 0) {
      PyErr_Format(PyExc_OSError, "Failed to close file: %s", strerror(errno));
      return NULL;
  }

  PyObject* dict = PyDict_New();
  if (!dict)
      return NULL;

  PyDict_SetItemString(dict, "magic", PyLong_FromUnsignedLong(header.magic));
  PyDict_SetItemString(dict, "version", PyLong_FromUnsignedLong(header.version));
  PyDict_SetItemString(dict, "ndim", PyLong_FromUnsignedLong(header.ndim));
  PyDict_SetItemString(dict, "dtype", PyLong_FromUnsignedLong(header.dtype));
  PyDict_SetItemString(dict, "uncompressed_size", PyLong_FromUnsignedLongLong(header.uncompressed_size));
  PyDict_SetItemString(dict, "compressed_size", PyLong_FromUnsignedLongLong(header.compressed_size));

  PyObject* shape_tuple = PyTuple_New(header.ndim);
  if (!shape_tuple) {
      Py_DECREF(dict);
      return NULL;
  }
  for (uint32_t i = 0; i < header.ndim; ++i) {
      PyObject* item = PyLong_FromUnsignedLongLong(header.shape[i]);
      if (!item) {
          Py_DECREF(shape_tuple);
          Py_DECREF(dict);
          return NULL;
      }
      PyTuple_SetItem(shape_tuple, i, item);
  }
  PyDict_SetItemString(dict, "shape", shape_tuple);
  Py_DECREF(shape_tuple);

  return dict;
}

static PyMethodDef CacheMethods[] = {
  {"save", (PyCFunction)cache_save, METH_VARARGS | METH_KEYWORDS, 
    "Save a NumPy array with LZ4 compression.\n"
    "Parameters:\n"
    "  array : numpy.ndarray\n"
    "  path  : str\n"
    "  acceleration : int, optional (default: 4)\n"
    "    LZ4 compression acceleration (1-16).\n"
    "    Lower = better compression, higher = faster.\n"
    "    Recommended: 1-8 for balance.\n"
    "Returns:\n"
    "  None\n"
    "Note: Array must be < 1GB for LZ4 compression."
  },
  {"load", cache_load, METH_VARARGS, 
    "Load a NumPy array from a cache file.\n"
    "Parameters:\n"
    "  path : str\n"
    "Returns:\n"
    "  numpy.ndarray\n"
    "Raises:\n"
    "  RuntimeError on invalid or corrupted file."
  },
  {"inspect", inspect_header, METH_VARARGS,
     "Read and display the header of a cache file without loading the data.\n"
     "Returns:\n A dictionary with magic, version, ndim, dtype, shape, sizes.\n"
  },
  {NULL, NULL, 0, NULL}
};

static struct PyModuleDef cachemodule = {
  PyModuleDef_HEAD_INIT,
  "_cache",
  "High-performance cache for NumPy arrays using LZ4 compression.\n"
  "Only little-endian systems are supported.",
  -1,
  CacheMethods
};

PyMODINIT_FUNC PyInit__cache(void) {
  import_array();
  PyObject* module = PyModule_Create(&cachemodule);
  if (!module) return NULL;

  PyModule_AddIntConstant(module, "MAX_DIMS", MAX_DIMS);
  PyModule_AddIntConstant(module, "VERSION", CACHE_VERSION);
  PyModule_AddStringConstant(module, "MAGIC", "LZNC");
  PyModule_AddIntConstant(module, "MAX_SIZE", MAX_SIZE);

  PyModule_AddIntConstant(module, "ACCELERATION_MIN", LZ4_ACCELERATION_MIN);
  PyModule_AddIntConstant(module, "ACCELERATION_MAX", LZ4_ACCELERATION_MAX);
  PyModule_AddIntConstant(module, "ACCELERATION_DEFAULT", LZ4_ACCELERATION_DEFAULT);

  return module;
}