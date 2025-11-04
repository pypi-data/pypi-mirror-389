#define _STRINGLIST_C

#include "_StringList.h"
#include "_StringList_C_API_defines.h"

#include <Python.h>
#define NPY_NO_DEPRECATED_API NPY_2_3_API_VERSION
#include <numpy/arrayobject.h>

#include <algorithm>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_set>
#include <vector>

/*
==========================================================================================
OptimizedString Implementation
==========================================================================================
*/

void OptimizedString::set(const char *str, size_t len) noexcept {
  // Clear existing data
  clear();

  if (len <= SSO_SIZE - 1) {
    // Small string - store inline
    std::memcpy(small.data, str, len);
    small.data[len] = '\0';
    small.size = static_cast<uint8_t>(len);
    is_large_flag = 0;
    is_interned_flag = 0;
  } else {
    // Large string - allocate on heap
    char *buf = static_cast<char *>(std::malloc(len + 1));
    if (buf) {
      std::memcpy(buf, str, len);
      buf[len] = '\0';

      large.ptr = buf;
      large.size = len;
      is_large_flag = 1;
      is_interned_flag = 0; // Not interned by default
    } else {
      // Allocation failed - store empty
      small.data[0] = '\0';
      small.size = 0;
      is_large_flag = 0;
      is_interned_flag = 0;
    }
  }
}

void OptimizedString::clear() noexcept {
  // Only free if it's a large string AND not interned (interned strings are
  // owned by the pool)
  if (!is_small() && !is_interned() && large.ptr) {
    std::free(const_cast<char *>(large.ptr));
    large.ptr = nullptr;
  }
  // Reset to small empty state
  small.size = 0;
  small.data[0] = '\0';
  is_large_flag = 0;
  is_interned_flag = 0;
}

void OptimizedString::set_interned(const char *interned_ptr,
                                   size_t len) noexcept {
  // Clear existing data
  clear();

  if (len <= SSO_SIZE - 1) {
    // Small enough for SSO - copy into inline storage
    std::memcpy(small.data, interned_ptr, len);
    small.data[len] = '\0';
    small.size = static_cast<uint8_t>(len);
    is_large_flag = 0;
    is_interned_flag = 0; // Not using interned pointer for small strings
  } else {
    // Large string - store interned pointer (don't allocate or copy)
    large.ptr = interned_ptr;
    large.size = len;
    is_large_flag = 1;
    is_interned_flag = 1; // Mark as interned - don't free on clear
  }
}

OptimizedString::OptimizedString(const OptimizedString &other) noexcept
    : is_large_flag(0), is_interned_flag(0), reserved(0) {
  if (other.is_small()) {
    small = other.small;
    is_large_flag = 0;
    is_interned_flag = 0;
  } else if (other.is_interned()) {
    // Copy interned pointer (don't allocate new memory)
    large.ptr = other.large.ptr;
    large.size = other.large.size;
    is_large_flag = 1;
    is_interned_flag = 1;
  } else {
    // Deep copy non-interned large string
    set(other.large.ptr, other.large.size);
  }
}

OptimizedString::OptimizedString(OptimizedString &&other) noexcept {
  // Move all data
  if (other.is_small()) {
    small = other.small;
    is_large_flag = 0;
    is_interned_flag = 0;
  } else {
    large.ptr = other.large.ptr;
    large.size = other.large.size;
    is_large_flag = other.is_large_flag;
    is_interned_flag = other.is_interned_flag;
    // Prevent other from freeing the pointer
    other.large.ptr = nullptr;
  }
  reserved = 0;
  // Mark other as empty small string
  other.small.size = 0;
  other.is_large_flag = 0;
  other.is_interned_flag = 0;
}

OptimizedString &
OptimizedString::operator=(const OptimizedString &other) noexcept {
  if (this != &other) {
    clear();
    if (other.is_small()) {
      small = other.small;
      is_large_flag = 0;
      is_interned_flag = 0;
    } else if (other.is_interned()) {
      // Copy interned pointer (don't allocate new memory)
      large.ptr = other.large.ptr;
      large.size = other.large.size;
      is_large_flag = 1;
      is_interned_flag = 1;
    } else {
      // Deep copy non-interned large string
      set(other.large.ptr, other.large.size);
    }
  }
  return *this;
}

OptimizedString &OptimizedString::operator=(OptimizedString &&other) noexcept {
  if (this != &other) {
    clear();
    if (other.is_small()) {
      small = other.small;
      is_large_flag = 0;
      is_interned_flag = 0;
    } else {
      large.ptr = other.large.ptr;
      large.size = other.large.size;
      is_large_flag = other.is_large_flag;
      is_interned_flag = other.is_interned_flag;
      // Prevent other from freeing the pointer
      other.large.ptr = nullptr;
    }
    reserved = 0;
    // Mark other as empty small string
    other.small.size = 0;
    other.is_large_flag = 0;
    other.is_interned_flag = 0;
  }
  return *this;
}

OptimizedString::~OptimizedString() { clear(); }

/*
==========================================================================================
StringListStorage Implementation (COW)
==========================================================================================

COPY-ON-WRITE (COW) SEMANTICS:
- Multiple StringList objects can share the same StringListStorage
- Atomic refcount tracks number of sharing instances
- make_writable() creates private copy when refcount > 1
- Reduces memory usage and enables efficient copies

THREADING:
- refcount uses std::atomic for thread-safe reference counting
- COW copies are safe across threads
- Individual string mutations require GIL (standard Python requirement)
*/

StringListStorage::StringListStorage(size_t sz)
    : size(sz), capacity(sz), refcount(1) {

  if (sz > 0) {
    strings = new OptimizedString[sz](); // Value-initialize
  } else {
    strings = nullptr;
  }
}

StringListStorage::~StringListStorage() { delete[] strings; }

/*
==========================================================================================
String Interning Pool (Optional - for common strings)
==========================================================================================

INTERNING BEHAVIOR:
- When use_interning=True, duplicate strings share the same storage pointer
- Reduces memory usage for lists with many repeated strings
- Thread-safe via mutex lock during intern() calls
- Pool persists for lifetime of process (intentionally leaked)

LIFETIME GUARANTEES:
- g_string_pool intentionally leaks to outlive all StringList objects
- Prevents use-after-free during Python interpreter shutdown
- Interned strings remain valid as long as they're in the pool

GIL REQUIREMENTS:
- intern() itself is thread-safe (uses internal mutex)
- Callers must hold GIL when modifying StringList (standard Python requirement)
*/
namespace {

struct StringPool {
  std::unordered_set<std::string> pool;
  std::mutex mutex;

  const char *intern(const char *str, size_t len) {
    std::lock_guard<std::mutex> lock(mutex);

    // Insert returns pair<iterator, bool>
    auto [it, inserted] = pool.insert(std::string(str, len));

    // Return stable pointer from the std::string in the set
    // The c_str() pointer remains valid as long as the string stays in the set
    return it->c_str();
  }

  // Destructor automatically cleans up - std::string handles memory
  ~StringPool() = default;
};

// POOL LIFETIME: Intentionally leak g_string_pool to prevent use-after-free
// during Python interpreter shutdown. StringList objects may be destroyed after
// static destructors run, so the pool must outlive all StringList instances.
static StringPool *g_string_pool = new StringPool();

} // anonymous namespace

/*
==========================================================================================
C++ Helper utilities for safer Python object management
==========================================================================================
*/
namespace {

// RAII wrapper for Python objects to ensure proper reference counting
class PyObjectPtr {
public:
  explicit PyObjectPtr(PyObject *obj = nullptr) noexcept : ptr_(obj) {}

  ~PyObjectPtr() noexcept { Py_XDECREF(ptr_); }

  // No copy (to avoid double-decref)
  PyObjectPtr(const PyObjectPtr &) = delete;
  PyObjectPtr &operator=(const PyObjectPtr &) = delete;

  // Move semantics
  PyObjectPtr(PyObjectPtr &&other) noexcept : ptr_(other.ptr_) {
    other.ptr_ = nullptr;
  }

  PyObjectPtr &operator=(PyObjectPtr &&other) noexcept {
    if (this != &other) {
      Py_XDECREF(ptr_);
      ptr_ = other.ptr_;
      other.ptr_ = nullptr;
    }
    return *this;
  }

  PyObject *get() const noexcept { return ptr_; }
  PyObject *release() noexcept {
    PyObject *tmp = ptr_;
    ptr_ = nullptr;
    return tmp;
  }

  explicit operator bool() const noexcept { return ptr_ != nullptr; }

private:
  PyObject *ptr_;
};

// Helper to sync OptimizedString storage to PyList items (for compatibility)
// Only materializes PyUnicode objects that don't already exist (lazy
// materialization)
inline void sync_storage_to_pylist(StringListObject *self) noexcept {
  PyListObject *list = reinterpret_cast<PyListObject *>(self);
  if (!self->storage || !list->ob_item)
    return;

  const size_t size = self->storage->size;
  for (size_t i = 0; i < size; ++i) {
    PyObject *existing = list->ob_item[i];

    // Skip if PyUnicode already exists (lazy materialization optimization)
    if (existing && PyUnicode_Check(existing)) {
      // Verify it matches storage (could be stale after direct storage
      // modification)
      Py_ssize_t len;
      const char *existing_str = PyUnicode_AsUTF8AndSize(existing, &len);
      const char *storage_str = self->storage->strings[i].c_str();
      size_t storage_len = self->storage->strings[i].length();

      if (existing_str && static_cast<size_t>(len) == storage_len &&
          std::memcmp(existing_str, storage_str, storage_len) == 0) {
        continue; // Already in sync, skip materialization
      }
    }

    // Materialize from storage
    const char *cstr = self->storage->strings[i].c_str();
    PyObject *newObj = PyUnicode_FromString(cstr);
    if (newObj) {
      list->ob_item[i] = newObj;
      Py_XDECREF(existing);
    }
  }
}

// Helper to sync PyList items to OptimizedString storage
// REQUIRES: GIL must be held (accesses PyList ob_item and calls PyUnicode APIs)
inline bool sync_pylist_to_storage(StringListObject *self) noexcept {
  PyListObject *list = reinterpret_cast<PyListObject *>(self);
  if (!self->storage || !list->ob_item)
    return false;

  const Py_ssize_t size = Py_SIZE(self);
  if (static_cast<size_t>(size) != self->storage->size)
    return false;

  for (Py_ssize_t i = 0; i < size; ++i) {
    PyObject *item = list->ob_item[i];
    if (!PyUnicode_Check(item))
      return false;

    Py_ssize_t len;
    const char *str = PyUnicode_AsUTF8AndSize(item, &len);
    if (!str)
      return false;

    // Use interning if enabled
    if (self->use_interning) {
      const char *interned =
          g_string_pool->intern(str, static_cast<size_t>(len));
      self->storage->strings[i].set_interned(interned,
                                             static_cast<size_t>(len));
    } else {
      self->storage->strings[i].set(str, static_cast<size_t>(len));
    }
  }

  return true;
}

// Helper to validate that all items in a list are Unicode strings
inline bool validateStringList(PyObject *list) noexcept {
  if (!PyList_Check(list)) {
    return false;
  }

  const Py_ssize_t size = Py_SIZE(list);
  PyObject **items = ((PyListObject *)list)->ob_item;

  for (Py_ssize_t k = 0; k < size; ++k) {
    if (!PyUnicode_Check(items[k])) {
      return false;
    }
  }
  return true;
}

// COW: Make storage writable (copy if shared)
// REQUIRES: GIL must be held (accesses PyList ob_item)
inline void make_writable(StringListObject *self) {
  if (!self->storage)
    return;

  if (self->storage->refcount.load(std::memory_order_relaxed) <= 1) {
    return; // Already exclusive owner
  }

  // Create new storage with copied strings
  size_t sz = self->storage->size;
  StringListStorage *new_storage = new StringListStorage(sz);

  // Deep copy strings
  for (size_t i = 0; i < sz; ++i) {
    new_storage->strings[i] = self->storage->strings[i];
  }

  // Replace storage
  self->storage->decref();
  self->storage = new_storage;
}

} // anonymous namespace

/*
==========================================================================================
C_API functions
==========================================================================================
*/
static int StringList_isStringList(PyObject *list) {
  return validateStringList(list) ? 1 : 0;
}

/*
==========================================================================================
PyMethods
==========================================================================================
*/
// new SetItem function for StringList
// REQUIRES: GIL must be held (Python API function, accesses ob_item)
int StringList_SetItem(PyObject *self, PyObject *key, PyObject *value) {
  StringListObject *strListObj = reinterpret_cast<StringListObject *>(self);

  if (strListObj->readonly) {
    PyErr_SetString(PyExc_TypeError, "The StringList is read only");
    return -1;
  }

  if (!value) {
    PyErr_SetString(PyExc_TypeError, "Cannot delete item in StringList");
    return -1;
  }
  if (!PyUnicode_Check(value) && !StringList_isStringList(value)) {
    PyErr_SetString(PyExc_TypeError, "Only strings allowed in StringList");
    return -1;
  }

  // COW: Make writable if shared
  if (strListObj->storage) {
    make_writable(strListObj);
  }

  // Handle single index assignment
  if (PyLong_Check(key)) {
    Py_ssize_t index = PyLong_AsSsize_t(key);
    if (index == -1 && PyErr_Occurred()) {
      return -1;
    }

    const Py_ssize_t size = Py_SIZE(self);
    if (index < 0)
      index += size;

    if (index < 0 || index >= size) {
      PyErr_SetString(PyExc_IndexError, "StringList index out of range");
      return -1;
    }

    // Fast path: single string assignment to OptimizedString
    if (PyUnicode_Check(value)) {
      Py_ssize_t len;
      const char *str = PyUnicode_AsUTF8AndSize(value, &len);
      if (!str)
        return -1;

      if (strListObj->storage &&
          static_cast<size_t>(index) < strListObj->storage->size) {
        // Update optimized storage with interning if enabled
        if (strListObj->use_interning) {
          const char *interned =
              g_string_pool->intern(str, static_cast<size_t>(len));
          strListObj->storage->strings[index].set_interned(
              interned, static_cast<size_t>(len));
        } else {
          strListObj->storage->strings[index].set(str,
                                                  static_cast<size_t>(len));
        }
      }

      // Also update PyList for compatibility
      Py_INCREF(value);
      PyObject *old = ((PyListObject *)self)->ob_item[index];
      ((PyListObject *)self)->ob_item[index] = value;
      Py_XDECREF(old);

      return 0;
    }
  }

  // Pre-validate slice assignments so size never changes (length preserving
  // only)
  if (PySlice_Check(key)) {
    Py_ssize_t start, stop, step, slicelen;
    if (PySlice_GetIndicesEx(key, Py_SIZE(self), &start, &stop, &step,
                             &slicelen) < 0)
      return -1; // error already set

    if (PyUnicode_Check(value)) {
      // Reject multi-element slice replacement with a raw string
      if (slicelen != 1) {
        PyErr_SetString(
            PyExc_TypeError,
            "Cannot assign a string to a slice of length != 1 in StringList");
        return -1;
      }
      // Perform an index assignment directly
      PyObject *indexObj = PyLong_FromSsize_t(start);
      if (!indexObj)
        return -1;
      int orig_size = Py_SIZE(self);
      int rr = StringList_SetItem(self, indexObj, value);
      Py_DECREF(indexObj);
      if (rr < 0)
        return -1;
      if (Py_SIZE(self) != orig_size) {
        PyErr_SetString(PyExc_TypeError,
                        "Internal error: StringList resized during assignment");
        return -1;
      }
      return rr;
    } else if (StringList_isStringList(value)) {
      if (Py_SIZE(value) != slicelen) {
        if (start == 0 && step == 1 && stop == Py_SIZE(self)) {
          PyErr_Format(PyExc_TypeError,
                       "Cannot replace entire StringList with different length "
                       "(expected %zd, got %zd)",
                       (Py_ssize_t)Py_SIZE(self), (Py_ssize_t)Py_SIZE(value));
        } else {
          PyErr_SetString(PyExc_TypeError, "StringList is not resizeable");
        }
        return -1;
      }
    } else {
      PyErr_SetString(PyExc_TypeError,
                      "Unsupported slice assignment type for StringList");
      return -1;
    }
  }

  int size = Py_SIZE(self); // store size for compare

  // Update StringList using the base type PyList_Type assign function
  int r =
      Py_TYPE(self)->tp_base->tp_as_mapping->mp_ass_subscript(self, key, value);

  if (size != Py_SIZE(self)) {
    PyErr_SetString(PyExc_TypeError, "StringList is not resizable (attempted "
                                     "implicit resize in assignment)");
    return -1;
  }

  // Sync PyList changes back to optimized storage
  if (r == 0 && strListObj->storage) {
    sync_pylist_to_storage(strListObj);
  }

  return r;
}

// Function to redefine since StringList are non-resizeable
PyObject *StringList_append(StringListObject *self, PyObject *notuse) {
  PyErr_SetString(PyExc_TypeError, "StringList are not resizeable");
  return nullptr;
}

PyObject *StringList_extend(StringListObject *self, PyObject *notuse) {
  PyErr_SetString(PyExc_TypeError, "StringList are not resizeable");
  return nullptr;
}

PyObject *StringList_insert(StringListObject *self, PyObject *notuse) {
  PyErr_SetString(PyExc_TypeError, "StringList are not resizeable");
  return nullptr;
}

PyObject *StringList_remove(StringListObject *self, PyObject *notuse) {
  PyErr_SetString(PyExc_TypeError, "StringList are not resizeable");
  return nullptr;
}

PyObject *StringList_pop(StringListObject *self, PyObject *notuse) {
  PyErr_SetString(PyExc_TypeError, "StringList are not resizeable");
  return nullptr;
}

// Explicitly disable sort to prevent reordering without paired data updates
PyObject *StringList_sort(StringListObject *self, PyObject *args,
                          PyObject *kwds) {
  PyErr_SetString(PyExc_TypeError, "Sorting StringList is not allowed");
  return nullptr;
}

// Explicitly disable reverse for the same reason
PyObject *StringList_reverse(StringListObject *self, PyObject *args,
                             PyObject *kwds) {
  PyErr_SetString(PyExc_TypeError, "Reversing StringList is not allowed");
  return nullptr;
}

PyObject *StringList_Reduce(StringListObject *self) {
  const Py_ssize_t size = Py_SIZE(self);

  PyObjectPtr state(PyList_New(size));
  if (!state) {
    return nullptr;
  }

  // Copy all items efficiently (PyList_SetItem steals reference)
  PyObject **selfItems = ((PyListObject *)self)->ob_item;
  PyObject **stateItems = ((PyListObject *)state.get())->ob_item;

  for (Py_ssize_t k = 0; k < size; ++k) {
    PyObject *item = selfItems[k];
    Py_INCREF(item);
    stateItems[k] = item;
  }

  // Create args tuple: (size, readonly)
  PyObjectPtr args(
      Py_BuildValue("(ii)", static_cast<int>(size), self->readonly));
  if (!args) {
    return nullptr;
  }

  // Return (type, args, state) tuple for pickle protocol
  // args is already a tuple, so we use 'O' not '(O)'
  return Py_BuildValue("(OOO)", Py_TYPE(self), args.get(), state.get());
}

PyObject *StringList_SetState(StringListObject *self, PyObject *statetuple) {
  PyObject *state = nullptr;

  if (!PyArg_Parse(statetuple, "(O)", &state)) {
    PyErr_SetString(PyExc_TypeError,
                    "StringList_SetState: invalid state tuple");
    return nullptr;
  }

  if (!PyList_Check(state)) {
    PyErr_SetString(PyExc_TypeError,
                    "StringList_SetState: state must be a list");
    return nullptr;
  }

  const Py_ssize_t selfSize = Py_SIZE(self);
  const Py_ssize_t stateSize = Py_SIZE(state);

  if (selfSize != stateSize) {
    PyErr_Format(PyExc_ValueError,
                 "StringList_SetState: size mismatch (expected %zd, got %zd)",
                 selfSize, stateSize);
    return nullptr;
  }

  // Validate all items before modifying
  if (!validateStringList(state)) {
    PyErr_SetString(PyExc_TypeError,
                    "StringList_SetState: all items must be strings");
    return nullptr;
  }

  // Efficient bulk update without individual SetItem overhead
  const int originalReadonly = self->readonly;
  self->readonly = 0;

  // COW: Make writable if shared
  if (self->storage) {
    make_writable(self);
  }

  PyObject **selfItems = ((PyListObject *)self)->ob_item;
  PyObject **stateItems = ((PyListObject *)state)->ob_item;

  for (Py_ssize_t k = 0; k < stateSize; ++k) {
    PyObject *newItem = stateItems[k];
    PyObject *oldItem = selfItems[k];

    Py_INCREF(newItem);
    selfItems[k] = newItem;
    Py_DECREF(oldItem);
  }

  // Sync storage from updated PyList (CRITICAL: maintains storage consistency)
  if (self->storage) {
    if (!sync_pylist_to_storage(self)) {
      self->readonly = originalReadonly;
      PyErr_SetString(PyExc_RuntimeError,
                      "StringList_SetState: failed to sync storage");
      return nullptr;
    }
  }

  self->readonly = originalReadonly;

  Py_RETURN_NONE;
}

/*
==========================================================================================
StringListType definition
==========================================================================================
*/
int StringList_init(StringListObject *self, PyObject *args, PyObject *kwds) {
  static char *kwlist[] = {const_cast<char *>("size"),
                           const_cast<char *>("readonly"),
                           const_cast<char *>("use_interning"), nullptr};

  int size = 0;
  int readonly = 0;
  int use_interning = 0; // Default: no interning

  // Parse arguments - use_interning is optional ("|iip")
  if (!PyArg_ParseTupleAndKeywords(args, kwds, "i|ip", kwlist, &size, &readonly,
                                   &use_interning)) {
    return -1;
  }

  if (size < 0) {
    PyErr_SetString(PyExc_TypeError,
                    "Only non-negative StringList sizes are allowed");
    return -1;
  }

  // Initialize parent object with empty tuple and dict
  PyObjectPtr emptyTuple(PyTuple_New(0));
  PyObjectPtr emptyDict(PyDict_New());

  if (!emptyTuple || !emptyDict) {
    return -1;
  }

  if (PyList_Type.tp_init(reinterpret_cast<PyObject *>(self), emptyTuple.get(),
                          emptyDict.get()) < 0) {
    return -1;
  }

  // Create optimized storage
  try {
    self->storage = new StringListStorage(static_cast<size_t>(size));
    self->use_interning = use_interning ? 1 : 0;
  } catch (const std::bad_alloc &) {
    PyErr_NoMemory();
    return -1;
  }

  // Initialize OptimizedString array with empty strings
  for (size_t i = 0; i < self->storage->size; i++) {
    self->storage->strings[i].set("", 0);
  }

  // Allocate the PyList item array for compatibility
  PyListObject *listObj = reinterpret_cast<PyListObject *>(self);

  if (size > 0) {
    listObj->ob_item =
        static_cast<PyObject **>(PyMem_Calloc(size, sizeof(PyObject *)));
    if (listObj->ob_item == nullptr) {
      delete self->storage;
      self->storage = nullptr;
      PyErr_NoMemory();
      return -1;
    }

    // Initialize all items to None (will sync from storage when accessed)
    for (int k = 0; k < size; ++k) {
      Py_INCREF(Py_None);
      listObj->ob_item[k] = Py_None;
    }
  } else {
    listObj->ob_item = nullptr;
  }

  // Set size and capacity
  Py_SET_SIZE(self, size);
  listObj->allocated = size;

  // Set readonly flag
  self->readonly = readonly ? 1 : 0;

  return 0;
}

// Deallocate StringList and clean up optimized storage
void StringList_dealloc(StringListObject *self) {
  // Clean up optimized storage with COW refcounting
  if (self->storage) {
    self->storage->decref();
    self->storage = nullptr;
  }

  // Let the base PyList_Type dealloc handle the rest
  PyList_Type.tp_dealloc(reinterpret_cast<PyObject *>(self));
}

/*
==========================================================================================
C_API functions
==========================================================================================
*/
int StringList_SetItemInit(PyObject *self, PyObject *key, PyObject *value) {
  if (!self || !key || !value) {
    PyErr_SetString(PyExc_ValueError, "StringList_SetItemInit: null arguments");
    return -1;
  }

  StringListObject *strList = reinterpret_cast<StringListObject *>(self);

  // Temporarily disable readonly to allow initialization
  const int originalReadonly = strList->readonly;
  strList->readonly = 0;

  const int result = StringList_SetItem(self, key, value);

  // Restore readonly flag
  strList->readonly = originalReadonly;

  return result;
}

// Update all items in StringList from another list
// REQUIRES: GIL must be held (Python API function, accesses ob_item)
int StringList_Update(PyObject *self, PyObject *value) {
  if (!self || !value) {
    PyErr_SetString(PyExc_ValueError, "No arguments given to StringList");
    return -1;
  }

  if (!PyList_Check(value)) {
    PyErr_SetString(PyExc_TypeError,
                    "Given value to StringList must be a list");
    return -1;
  }

  const Py_ssize_t selfSize = Py_SIZE(self);
  const Py_ssize_t valueSize = Py_SIZE(value);

  if (selfSize != valueSize) {
    PyErr_Format(PyExc_ValueError,
                 "Cannot replace entire StringList with different length "
                 "(expected %zd, got %zd)",
                 selfSize, valueSize);
    return -1;
  }

  // Validate all items first before modifying anything
  if (!validateStringList(value)) {
    PyErr_SetString(PyExc_TypeError,
                    "All items given to StringList must be strings");
    return -1;
  }

  StringListObject *strList = reinterpret_cast<StringListObject *>(self);
  const int originalReadonly = strList->readonly;
  strList->readonly = 0;

  // COW: Make writable if shared
  if (strList->storage) {
    make_writable(strList);
  }

  // Direct item replacement - more efficient than slice assignment
  PyObject **selfItems = ((PyListObject *)self)->ob_item;
  PyObject **valueItems = ((PyListObject *)value)->ob_item;

  for (Py_ssize_t i = 0; i < selfSize; ++i) {
    PyObject *newItem = valueItems[i];
    PyObject *oldItem = selfItems[i];

    Py_INCREF(newItem);
    selfItems[i] = newItem;
    Py_DECREF(oldItem);
  }

  // Sync storage from updated PyList (CRITICAL: maintains storage consistency)
  if (strList->storage) {
    if (!sync_pylist_to_storage(strList)) {
      // Sync failed - this shouldn't happen since we validated above
      strList->readonly = originalReadonly;
      PyErr_SetString(PyExc_RuntimeError, "StringList failed to sync storage");
      return -1;
    }
  }

  strList->readonly = originalReadonly;
  return 0;
}

PyObject *StringList_New(int size, int readonly) {
  if (size < 0) {
    PyErr_SetString(PyExc_ValueError, "StringList size must be non-negative");
    return nullptr;
  }

  PyObjectPtr argList(Py_BuildValue("(ii)", size, readonly));
  if (!argList) {
    return nullptr;
  }

  PyObject *obj = PyObject_CallObject(
      reinterpret_cast<PyObject *>(&StringListType), argList.get());

  return obj;
}

PyObject *StringList_NewEx(int size, int readonly, int use_interning) {
  if (size < 0) {
    PyErr_SetString(PyExc_ValueError, "StringList size must be non-negative");
    return nullptr;
  }

  PyObjectPtr argList(Py_BuildValue("(iii)", size, readonly, use_interning));
  if (!argList) {
    return nullptr;
  }

  PyObject *obj = PyObject_CallObject(
      reinterpret_cast<PyObject *>(&StringListType), argList.get());

  return obj;
}

// Check if a specific slot in StringList contains an interned string
// Returns: 1 if interned, 0 if not interned, -1 on error
int StringList_IsSlotInterned(PyObject *self, Py_ssize_t index) {
  if (!StringList_isStringList(self)) {
    PyErr_SetString(PyExc_TypeError,
                    "StringList_IsSlotInterned: not a StringList");
    return -1;
  }

  StringListObject *strListObj = reinterpret_cast<StringListObject *>(self);

  if (index < 0 || index >= Py_SIZE(self)) {
    PyErr_Format(PyExc_IndexError,
                 "StringList_IsSlotInterned: index %zd out of range", index);
    return -1;
  }

  if (!strListObj->storage) {
    return 0; // No storage means no interning
  }

  if (static_cast<size_t>(index) >= strListObj->storage->size) {
    return 0; // Index out of storage bounds
  }

  return strListObj->storage->strings[index].is_interned() ? 1 : 0;
}

PyObject *StringList_NewFromStrings(const char **strings, int size,
                                    int readonly) {
  if (size < 0) {
    PyErr_SetString(PyExc_ValueError, "StringList size must be non-negative");
    return nullptr;
  }

  if (!strings && size > 0) {
    PyErr_SetString(PyExc_ValueError,
                    "StringList_NewFromStrings: strings array is null");
    return nullptr;
  }

  PyObject *obj = StringList_New(size, readonly);
  if (!obj) {
    return nullptr;
  }

  StringListObject *strList = reinterpret_cast<StringListObject *>(obj);
  PyObject **items = ((PyListObject *)obj)->ob_item;

  // Populate with provided strings (more efficient than individual SetItem
  // calls)
  for (int i = 0; i < size; ++i) {
    PyObject *pyStr = PyUnicode_FromString(strings[i]);
    if (!pyStr) {
      Py_DECREF(obj);
      return nullptr;
    }

    Py_DECREF(items[i]); // Release the None that was placed during init
    items[i] = pyStr;    // No need to INCREF, we already own the reference
  }

  return obj;
}

/*
==========================================================================================
StringList module definition
==========================================================================================
*/
PyMODINIT_FUNC PyInit__StringList(void) {
  // Initialize the C API pointer array
  static void *StringList_API[StringList_API_pointers];

  StringList_API[StringList_isStringList_NUM] =
      reinterpret_cast<void *>(StringList_isStringList);
  StringList_API[StringList_SetItemInit_NUM] =
      reinterpret_cast<void *>(StringList_SetItemInit);
  StringList_API[StringList_Update_NUM] =
      reinterpret_cast<void *>(StringList_Update);
  StringList_API[StringList_New_NUM] = reinterpret_cast<void *>(StringList_New);
  StringList_API[StringList_NewFromStrings_NUM] =
      reinterpret_cast<void *>(StringList_NewFromStrings);
  StringList_API[StringList_NewEx_NUM] =
      reinterpret_cast<void *>(StringList_NewEx);
  StringList_API[StringList_IsSlotInterned_NUM] =
      reinterpret_cast<void *>(StringList_IsSlotInterned);

  // Create a Capsule containing the API pointer array's address
  PyObject *c_api_object = PyCapsule_New(static_cast<void *>(StringList_API),
                                         "sund._StringList._C_API", nullptr);

  if (!c_api_object) {
    return nullptr;
  }

  // Set up the StringList type (inherits from PyList)
  StringListType.tp_base = &PyList_Type;
  if (PyType_Ready(&StringListType) < 0) {
    Py_DECREF(c_api_object);
    return nullptr;
  }

  // Create the module
  PyObject *module = PyModule_Create(&StringListModule);
  if (!module) {
    Py_DECREF(c_api_object);
    return nullptr;
  }

  // Add StringList type to module
  Py_INCREF(&StringListType);
  if (PyModule_AddObject(module, "StringList",
                         reinterpret_cast<PyObject *>(&StringListType)) < 0) {
    Py_DECREF(&StringListType);
    Py_DECREF(c_api_object);
    Py_DECREF(module);
    return nullptr;
  }

  // Add C API capsule to module
  if (PyModule_AddObject(module, "_C_API", c_api_object) < 0) {
    Py_DECREF(c_api_object);
    Py_DECREF(module);
    return nullptr;
  }

  // Initialize NumPy (required for extension modules using NumPy)
  import_array();

  return module;
}
