#ifndef _STRINGLIST_CPP_API_H
#define _STRINGLIST_CPP_API_H

#include "_StringList_C_API.h"
#include <Python.h>
#include <string>
#include <vector>

/*
==========================================================================================
Modern C++ API for StringList
==========================================================================================

This header provides a cleaner, type-safe C++ interface for StringList
operations. It wraps the existing C API with RAII and modern C++ idioms.

Usage example:
    #include "_StringList_CPP_API.h"

    // Create a StringList
    auto strList = StringList::create(3, false);
    if (!strList) {
        // Handle error
    }

    // Set items
    strList.set(0, "first");
    strList.set(1, "second");
    strList.set(2, "third");

    // Read items
    std::string first = strList.get(0);

    // Get the underlying PyObject* (doesn't transfer ownership)
    PyObject* pyObj = strList.get();

    // Release ownership if you need to return it to Python
    PyObject* released = strList.release();

==========================================================================================
*/

namespace StringList {

/*
 * RAII wrapper for StringList PyObject
 * Automatically manages reference counting
 */
class StringListPtr {
public:
  // Constructors
  StringListPtr() : ptr_(nullptr) {}

  explicit StringListPtr(PyObject *obj, bool steal_ref = false) : ptr_(obj) {
    if (ptr_ && !steal_ref) {
      Py_INCREF(ptr_);
    }
  }

  // Destructor
  ~StringListPtr() { Py_XDECREF(ptr_); }

  // No copy (to avoid reference counting issues)
  StringListPtr(const StringListPtr &) = delete;
  StringListPtr &operator=(const StringListPtr &) = delete;

  // Move semantics
  StringListPtr(StringListPtr &&other) noexcept : ptr_(other.ptr_) {
    other.ptr_ = nullptr;
  }

  StringListPtr &operator=(StringListPtr &&other) noexcept {
    if (this != &other) {
      Py_XDECREF(ptr_);
      ptr_ = other.ptr_;
      other.ptr_ = nullptr;
    }
    return *this;
  }

  // Access the underlying PyObject (borrowed reference)
  PyObject *get() const { return ptr_; }

  // Release ownership and return the PyObject
  PyObject *release() {
    PyObject *tmp = ptr_;
    ptr_ = nullptr;
    return tmp;
  }

  // Check if valid
  explicit operator bool() const noexcept { return ptr_ != nullptr; }

  // Get size
  Py_ssize_t size() const noexcept { return ptr_ ? Py_SIZE(ptr_) : 0; }

  // Set item by index (for initialization)
  bool set(Py_ssize_t index, const char *value) noexcept {
    if (!ptr_ || index < 0 || index >= size())
      return false;

    PyObject *pyValue = PyUnicode_FromString(value);
    if (!pyValue)
      return false;

    PyObject **items = ((PyListObject *)ptr_)->ob_item;
    PyObject *oldItem = items[index];
    items[index] = pyValue;
    Py_DECREF(oldItem);

    return true;
  }

  bool set(Py_ssize_t index, const std::string &value) noexcept {
    return set(index, value.c_str());
  }

  // Get item by index as std::string
  std::string get_string(Py_ssize_t index) const noexcept {
    if (!ptr_ || index < 0 || index >= size()) {
      return "";
    }

    PyObject *item = PyList_GetItem(ptr_, index);
    if (!item || !PyUnicode_Check(item)) {
      return "";
    }

    Py_ssize_t len;
    const char *data = PyUnicode_AsUTF8AndSize(item, &len);
    if (!data) {
      return "";
    }

    return std::string(data, len);
  }

  // Update entire StringList from a list of strings
  bool update(const std::vector<std::string> &strings) noexcept {
    if (!ptr_ || static_cast<size_t>(size()) != strings.size()) {
      return false;
    }

    for (size_t i = 0; i < strings.size(); ++i) {
      if (!set(i, strings[i])) {
        return false;
      }
    }
    return true;
  }

  // Update entire StringList from a PyObject list (wrapper for
  // StringList_Update)
  bool update_from_pyobject(PyObject *value) noexcept {
    if (!ptr_ || !value) {
      return false;
    }
    return StringList_Update(ptr_, value) == 0;
  }

  // Convert to vector of strings
  std::vector<std::string> to_vector() const noexcept {
    std::vector<std::string> result;
    if (!ptr_)
      return result;

    const Py_ssize_t n = size();
    result.reserve(n);

    for (Py_ssize_t i = 0; i < n; ++i) {
      result.push_back(get_string(i));
    }

    return result;
  }

private:
  PyObject *ptr_;
};

/*
 * Create a new StringList
 * Returns a StringListPtr that manages the reference count
 *
 * @param size: Initial size of the StringList
 * @param readonly: If true, StringList is immutable
 * @param use_interning: If true, enables string interning for memory savings
 * (recommended for lists with repeated values)
 */
inline StringListPtr create(int size, bool readonly = false,
                            bool use_interning = false) noexcept {
  // Use the fast C API path
  PyObject *obj =
      StringList_NewEx(size, readonly ? 1 : 0, use_interning ? 1 : 0);
  return StringListPtr(obj, true); // steal the reference
}

/*
 * Create a StringList from a vector of strings
 */
inline StringListPtr from_vector(const std::vector<std::string> &strings,
                                 bool readonly = false) noexcept {
  auto strList = create(static_cast<int>(strings.size()), readonly);
  if (!strList) {
    return StringListPtr();
  }

  if (!strList.update(strings)) {
    return StringListPtr();
  }

  return strList;
}

/*
 * Create a StringList from a C-style array of strings (more efficient)
 */
inline StringListPtr from_c_strings(const char **strings, int size,
                                    bool readonly = false) noexcept {
  PyObject *obj = StringList_NewFromStrings(strings, size, readonly);
  return StringListPtr(obj, true);
}

/*
 * Check if a PyObject is a StringList
 */
inline bool is_stringlist(PyObject *obj) noexcept {
  return StringList_isStringList(obj) != 0;
}

/*
 * Wrap an existing PyObject as a StringListPtr (borrows reference)
 * Use this when you receive a StringList from Python code
 */
inline StringListPtr wrap(PyObject *obj) noexcept {
  if (!is_stringlist(obj)) {
    return StringListPtr();
  }
  return StringListPtr(obj, false); // borrow reference
}

/*
 * Update a StringList PyObject from another PyObject list
 * Convenience wrapper that combines wrap + update_from_pyobject
 * Returns true on success, false on failure
 */
inline bool update(PyObject *stringlist, PyObject *value) noexcept {
  auto wrapped = wrap(stringlist);
  if (!wrapped) {
    return false;
  }
  return wrapped.update_from_pyobject(value);
}

} // namespace StringList

#endif // _STRINGLIST_CPP_API_H
