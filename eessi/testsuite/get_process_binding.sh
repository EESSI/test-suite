#!/bin/bash
# get process binding with hwloc

hwlocbind=$(hwloc-bind --get)

binding=$(hwloc-calc -p -H package.numanode.core.pu "$hwlocbind" 2>&1 | grep -v unsupported)

if [[ -n $binding ]]; then
    echo "$binding"
else
    # skip numanode as a fallback: not supported until hwloc v2.9.0
    hwloc-calc -p -H package.core.pu "$hwlocbind"
fi
