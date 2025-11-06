#ifndef _STRINGLIST_H
#define _STRINGLIST_H

#include "Python.h"
#include <atomic>
#include <cstdint>

/*
==========================================================================================
Optimized String Storage with Small String Optimization (SSO)
==========================================================================================
*/

// Small String Optimization: store strings <= 23 bytes inline
struct OptimizedString {
  static constexpr size_t SSO_SIZE = 23;

  union {
    // Small string: stored inline (no allocation)
    struct {
      char data[SSO_SIZE];
      uint8_t size; // String length when small
    } small;

    // Large string: heap allocated
    struct {
      const char *ptr; // Pointer to string data
      size_t size;     // String length
    } large;
  };

  // Explicit discriminant flags (outside union to avoid undefined behavior)
  uint8_t is_large_flag : 1; // 0 = small, 1 = large
  uint8_t is_interned_flag
      : 1;              // 1 = large.ptr points to intern pool (don't free)
  uint8_t reserved : 6; // Reserved for future use

  // Check if this is a small string
  inline bool is_small() const noexcept { return is_large_flag == 0; }

  // Get the string data
  inline const char *c_str() const noexcept {
    return is_small() ? small.data : large.ptr;
  }

  // Get the string length
  inline size_t length() const noexcept {
    return is_small() ? static_cast<size_t>(small.size) : large.size;
  }

  // Check if this is an interned string (from pool)
  inline bool is_interned() const noexcept { return is_interned_flag != 0; }

  // Set a string value
  void set(const char *str, size_t len) noexcept;

  // Set an interned string value (from pool - don't free on clear)
  void set_interned(const char *interned_ptr, size_t len) noexcept;

  // Clear the string
  void clear() noexcept;

  // Constructor
  OptimizedString() noexcept
      : small{{0}, 0}, is_large_flag(0), is_interned_flag(0), reserved(0) {}

  // Copy constructor
  OptimizedString(const OptimizedString &other) noexcept;

  // Move constructor
  OptimizedString(OptimizedString &&other) noexcept;

  // Assignment
  OptimizedString &operator=(const OptimizedString &other) noexcept;
  OptimizedString &operator=(OptimizedString &&other) noexcept;

  // Destructor
  ~OptimizedString();
};

/*
==========================================================================================
Copy-on-Write Storage for StringLists
==========================================================================================
*/
struct StringListStorage {
  OptimizedString *strings;
  size_t size;
  size_t capacity;
  std::atomic<uint32_t> refcount;

  StringListStorage(size_t sz);
  ~StringListStorage();

  inline void incref() noexcept {
    refcount.fetch_add(1, std::memory_order_relaxed);
  }

  inline void decref() noexcept {
    if (refcount.fetch_sub(1, std::memory_order_acq_rel) == 1) {
      delete this;
    }
  }

  // Disable copy
  StringListStorage(const StringListStorage &) = delete;
  StringListStorage &operator=(const StringListStorage &) = delete;
};

/*
==========================================================================================
Structure definitions
==========================================================================================
*/
typedef struct {
  PyListObject list;
  StringListStorage *storage; // COW optimized storage
  uint8_t readonly : 1;
  uint8_t use_interning : 1; // Use string pool for common strings
  uint8_t reserved : 6;
} StringListObject;

int StringList_init(StringListObject *self, PyObject *args, PyObject *kwds);
void StringList_dealloc(StringListObject *self);

/*
==========================================================================================
Function declaration
==========================================================================================
*/
int StringList_SetItem(PyObject *self, PyObject *key, PyObject *value);

PyObject *StringList_append(StringListObject *self, PyObject *notuse);

PyObject *StringList_extend(StringListObject *self, PyObject *notuse);

PyObject *StringList_insert(StringListObject *self, PyObject *notuse);

PyObject *StringList_remove(StringListObject *self, PyObject *notuse);

PyObject *StringList_pop(StringListObject *self, PyObject *notuse);

PyObject *StringList_Reduce(StringListObject *self);

PyObject *StringList_SetState(StringListObject *self, PyObject *statetuple);

// Disallow reordering operations that would break external data alignment
PyObject *StringList_sort(StringListObject *self, PyObject *args,
                          PyObject *kwds);
PyObject *StringList_reverse(StringListObject *self, PyObject *args,
                             PyObject *kwds);

/*
==========================================================================================
C_API function declarations
==========================================================================================
*/
int StringList_SetItemInit(PyObject *self, PyObject *key, PyObject *value);

int StringList_Update(PyObject *self, PyObject *value);

PyObject *StringList_New(int size, int readonly);

PyObject *StringList_NewEx(int size, int readonly, int use_interning);

PyObject *StringList_NewFromStrings(const char **strings, int size,
                                    int readonly);

/*
==========================================================================================
Python module definitions
==========================================================================================
*/
static PyMethodDef StringList_methods[] = {
    {"append", (PyCFunction)StringList_append, METH_VARARGS,
     "Overwritten append function"},
    {"extend", (PyCFunction)StringList_extend, METH_VARARGS,
     "Overwritten extend function"},
    {"insert", (PyCFunction)StringList_insert, METH_VARARGS,
     "Overwritten insert function"},
    {"remove", (PyCFunction)StringList_remove, METH_VARARGS,
     "Overwritten remove function"},
    {"pop", (PyCFunction)StringList_pop, METH_VARARGS,
     "Overwritten pop function"},
    {"__reduce__", (PyCFunction)StringList_Reduce, METH_NOARGS,
     "__reduce__ function"},
    {"__setstate__", (PyCFunction)StringList_SetState, METH_VARARGS,
     "__setstate__ function"},
    {"sort", (PyCFunction)StringList_sort, METH_VARARGS | METH_KEYWORDS,
     "Disabled: sorting a StringList would desynchronize associated data"},
    {"reverse", (PyCFunction)StringList_reverse, METH_VARARGS | METH_KEYWORDS,
     "Disabled: reversing a StringList would desynchronize associated data"},
    {nullptr, nullptr, 0, nullptr} /* Sentinel */
};

static PyMappingMethods StringListMapping = {
    .mp_ass_subscript = (objobjargproc)StringList_SetItem,
};

static PyTypeObject StringListType = {
    .ob_base = PyVarObject_HEAD_INIT(NULL, 0).tp_name =
        "sund._StringList.StringList",
    .tp_basicsize = sizeof(StringListObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)StringList_dealloc,
    .tp_as_mapping = &StringListMapping,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_doc = "StringList type object",
    .tp_methods = StringList_methods,
    .tp_init = (initproc)StringList_init};

static PyModuleDef StringListModule = {.m_base = PyModuleDef_HEAD_INIT,
                                       .m_name = "sund._StringList",
                                       .m_doc = "StringList Module",
                                       .m_size = -1};

#endif