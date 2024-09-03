#!/usr/bin/env python
"""
MPI_Reduce on MPI rank. This should result in a total of (size * (size - 1) / 2),
where size is the total number of ranks.
Prints the total number of ranks, the sum of all ranks, and the time elapsed for the reduction."
"""

import argparse
import time

from mpi4py import MPI

parser = argparse.ArgumentParser(description='mpi4py reduction benchmark',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--n_warmup', type=int, default=100,
                    help='Number of warmup iterations')
parser.add_argument('--n_iter', type=int, default=1000,
                    help='Number of benchmark iterations')
args = parser.parse_args()

n_warmup = args.n_warmup
n_iter = args.n_iter

size = MPI.COMM_WORLD.Get_size()
rank = MPI.COMM_WORLD.Get_rank()
name = MPI.Get_processor_name()

# Warmup
t0 = time.time()
for i in range(n_warmup):
    total = MPI.COMM_WORLD.reduce(rank, op=MPI.SUM)

# Actual reduction, multiple iterations for accuracy of timing
t1 = time.time()
for i in range(n_iter):
    total = MPI.COMM_WORLD.reduce(rank, op=MPI.SUM)
t2 = time.time()
total_time = (t2 - t1) / n_iter

if rank == 0:
    print(f"Total ranks: {size}")
    print(f"Sum of all ranks: {total}")  # Should be (size * (size-1) / 2)
    print(f"Time elapsed: {total_time:.3e}")
