#ifndef __LIBMYPY_H__
#define __LIBMYPY_H__

#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <freerdp/client.h>
#include <freerdp/freerdp.h>
#include <freerdp/settings.h>
PyObject * check_connectivity(PyObject *,PyObject *);
int RdpClientEntry(RDP_CLIENT_ENTRY_POINTS* pEntryPoints);

#endif