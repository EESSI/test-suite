#!/usr/bin/env python3
"""
Check process binding from standard input in format similar to the example below, which was obtained as follows:

$ mpirun -np 3 --map-by slot:PE=2 bash -c '$(hwloc-calc -p --hierarchical package.numanode.core.pu $(hwloc-bind --get))'
Package:0.NUMANode:3.Core:51.PU:15 Package:0.NUMANode:4.Core:8.PU:16
Package:0.NUMANode:1.Core:17.PU:5 Package:0.NUMANode:3.Core:48.PU:12
Package:0.NUMANode:3.Core:49.PU:13 Package:0.NUMANode:3.Core:50.PU:14
"""

import argparse
from collections import defaultdict
import sys


def main():
    parser = argparse.ArgumentParser(description="Check process binding.")
    parser.add_argument("--procs", type=int, required=True, help="Expected number of processes")
    parser.add_argument("--cpus-per-proc", type=int, required=True, help="Expected number of CPUs per process")
    args = parser.parse_args()

    procs = sys.stdin.read().splitlines()
    num_procs = len(procs)
    if num_procs != args.procs:
        print(f"PROCESS BINDING ERROR: wrong number of processes: expected {args.procs}, found {num_procs}",
              file=sys.stderr)

    cpus_per_task = [x.split() for x in procs]

    for cpus in cpus_per_task:
        num_cpus = len(cpus)
        if num_cpus != args.cpus_per_proc:
            print(f"PROCESS BINDING ERROR: wrong number of cpus per process: expected {args.cpus_per_proc},"
                  f" found {num_cpus}", file=sys.stderr)

        packages = set()
        numanodes = set()
        cores_occupation = defaultdict(int)

        for cpu in cpus:
            cpu_parts = dict(item.split(':') for item in cpu.split('.'))
            packages.add(cpu_parts['Package'])
            numanodes.add(cpu_parts['NUMANode'])
            cores_occupation[(cpu_parts['Package'], cpu_parts['Core'])] += 1

        if len(packages) > 1:
            print(f"PROCESS BINDING WARNING: process spanning multiple packages: {packages}", file=sys.stderr)

        if len(numanodes) > 1:
            print(f"PROCESS BINDING WARNING: process spanning multiple numanodes: {numanodes}", file=sys.stderr)

        for key, value in cores_occupation.items():
            if value > 1:
                print(f"PROCESS BINDING WARNING: package-core {key} is shared by {value} processing units,"
                      " indicating hyperthreading", file=sys.stderr)


if __name__ == "__main__":
    main()
