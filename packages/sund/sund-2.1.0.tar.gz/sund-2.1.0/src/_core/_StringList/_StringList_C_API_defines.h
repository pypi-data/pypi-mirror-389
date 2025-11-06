#ifndef _STRINGLIST_C_API_DEFINES_H
#define _STRINGLIST_C_API_DEFINES_H

#include "Python.h"

/* C API defines */
#define StringList_isStringList_NUM 0
#define StringList_isStringList_RETURN int
#define StringList_isStringList_PROTO (PyObject * list)

#define StringList_SetItemInit_NUM 1
#define StringList_SetItemInit_RETURN int
#define StringList_SetItemInit_PROTO                                           \
  (PyObject * self, PyObject * key, PyObject * value)

#define StringList_Update_NUM 2
#define StringList_Update_RETURN int
#define StringList_Update_PROTO (PyObject * self, PyObject * value)

#define StringList_New_NUM 3
#define StringList_New_RETURN PyObject *
#define StringList_New_PROTO (int size, int readonly)

#define StringList_NewFromStrings_NUM 4
#define StringList_NewFromStrings_RETURN PyObject *
#define StringList_NewFromStrings_PROTO                                        \
  (const char **strings, int size, int readonly)

#define StringList_NewEx_NUM 5
#define StringList_NewEx_RETURN PyObject *
#define StringList_NewEx_PROTO (int size, int readonly, int use_interning)

#define StringList_IsSlotInterned_NUM 6
#define StringList_IsSlotInterned_RETURN int
#define StringList_IsSlotInterned_PROTO (PyObject * self, Py_ssize_t index)

/* Total number of C API pointers */
#define StringList_API_pointers 7

#endif
