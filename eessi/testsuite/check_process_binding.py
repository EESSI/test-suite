#!/usr/bin/env python3
"""
Check process binding from standard input in format similar to the example below, which was obtained as follows:

$ mpirun -np 3 --map-by slot:PE=2 bash -c '$(hwloc-calc -p --hierarchical package.numanode.core.pu $(hwloc-bind --get))'
host1 Package:0.NUMANode:3.Core:51.PU:15 Package:0.NUMANode:4.Core:8.PU:16
host1 Package:0.NUMANode:1.Core:17.PU:5 Package:0.NUMANode:3.Core:48.PU:12
host2 Package:0.NUMANode:3.Core:49.PU:13 Package:0.NUMANode:3.Core:50.PU:14

Alternatively, if numanode is not supported:

$ mpirun -np 3 --map-by slot:PE=2 bash -c '$(hwloc-calc -p --hierarchical package.core.pu $(hwloc-bind --get))'
host1 Package:0.Core:51.PU:15 Package:0.Core:8.PU:16
host1 Package:0.Core:17.PU:5 Package:0.Core:48.PU:12
host2 Package:0.Core:49.PU:13 Package:0.Core:50.PU:14
"""

import argparse
from collections import Counter, defaultdict
import sys


def main():
    parser = argparse.ArgumentParser(description="Check process binding.")
    parser.add_argument("--nodes", type=int, required=True, help="Expected number of nodes")
    parser.add_argument("--procs", type=int, required=True, help="Expected number of processes")
    parser.add_argument("--cpus-per-proc", type=int, required=True, help="Expected number of CPUs per process")
    args = parser.parse_args()

    procs = [p for p in (line.split() for line in sys.stdin) if p]
    nodes = {x[0] for x in procs}
    cpus_per_task = [x[1:] for x in procs]

    num_procs = len(procs)
    if num_procs != args.procs:
        print(f"PROCESS BINDING ERROR: wrong number of processes: expected {args.procs}, found {num_procs}",
              file=sys.stderr)

    num_nodes = len(nodes)
    if num_nodes != args.nodes:
        print(f"PROCESS BINDING ERROR: wrong number of nodes: expected {args.nodes}, found {num_nodes}",
              file=sys.stderr)

    error_cpus = []
    warning_packages = []
    warning_numanodes = []
    warning_ht = []

    for cpus in cpus_per_task:
        num_cpus = len(cpus)
        if num_cpus != args.cpus_per_proc:
            error_cpus.append(num_cpus)

        packages = set()
        numanodes = set()
        cores_occupation = defaultdict(int)

        for cpu in cpus:
            cpu_parts = dict(item.split(':') for item in cpu.split('.'))
            packages.add(cpu_parts['Package'])
            if cpu_parts.get('NUMANode'):
                numanodes.add(cpu_parts['NUMANode'])
            cores_occupation[(cpu_parts['Package'], cpu_parts['Core'])] += 1

        num_packages = len(packages)
        if num_packages > 1:
            warning_packages.append(num_packages)

        num_numanodes = len(numanodes)
        if num_numanodes > 1:
            warning_numanodes.append(num_numanodes)

        for _, occupation in cores_occupation.items():
            if occupation > 1:
                warning_ht.append(occupation)

    if error_cpus:
        print(f"PROCESS BINDING ERROR: wrong number of cpus per process: expected {args.cpus_per_proc},"
              f" found {Counter(error_cpus)}", file=sys.stderr)

    if warning_packages:
        print(f"PROCESS BINDING WARNING: processes spanning multiple packages: {Counter(warning_packages)}",
              file=sys.stderr)

    if warning_numanodes:
        print(f"PROCESS BINDING WARNING: processes spanning multiple numanodes: {Counter(warning_numanodes)}",
              file=sys.stderr)

    if warning_ht:
        print("PROCESS BINDING WARNING: processes with cores shared by processing units, indicating hyperthreading:"
              f" {Counter(warning_ht)},", file=sys.stderr)


if __name__ == "__main__":
    main()
