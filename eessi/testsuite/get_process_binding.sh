#!/bin/bash
# get process binding with hwloc

hwlocbind=$(hwloc-bind --get)
binding=$(hwloc-calc -p -H package.numanode.core.pu "$hwlocbind" 2>/dev/null)

if [[ -z $binding ]]; then
    # skip numanode as a fallback: not supported until hwloc v2.9.0
    binding=$(hwloc-calc -p -H package.core.pu "$hwlocbind")
fi

echo "$HOSTNAME $binding"
