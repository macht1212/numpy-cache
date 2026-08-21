#include <Python.h>

static PyObject* cache_save(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* cache_load(PyObject* self, PyObject* args);
static PyObject* inspect_header(PyObject* self, PyObject* args);