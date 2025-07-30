#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import numpy as np
from time import time

parser = ArgumentParser(
    description='NumPy test',
    formatter_class=ArgumentDefaultsHelpFormatter,
)

parser.add_argument('--matrix-size', type=int, default=8192, help='matrix size')
parser.add_argument('--iterations', type=int, default=4, help='number of iterations (not Eigen decomposition)')
parser.add_argument('--iterations-eigen', type=int, default=1, help='number of Eigen decomposition iterations')

args = parser.parse_args()

size = args.matrix_size
niter = args.iterations
niter_eigen = args.iterations_eigen

print('NumPy version:', np.__version__)

# Let's take the randomness out of random numbers (for reproducibility)
np.random.seed(534)

A, B = np.random.random((size, size)), np.random.random((size, size))
E = np.random.random((int(size / 2), int(size / 4)))
F = np.random.random((int(size / 2), int(size / 2)))
F = np.dot(F, F.T)
G = np.random.random((int(size / 2), int(size / 2)))
J = (F + F.T) / 2.

# Matrix multiplication
t = time()
for i in range(niter):
    np.dot(A, B)

delta = time() - t
print('Dotted two %dx%d matrices in %0.2f s.' % (size, size, delta / niter))
del A, B

# Singular value decomposition (SVD)
t = time()
for i in range(niter):
    np.linalg.svd(E, full_matrices=False)

delta = time() - t
print("SVD of a %dx%d matrix in %0.2f s." % (size / 2, size / 4, delta / niter))
del E

# Cholesky decomposition
t = time()
for i in range(niter):
    np.linalg.cholesky(F)

delta = time() - t
print("Cholesky decomposition of a %dx%d matrix in %0.2f s." % (size / 2, size / 2, delta / niter))

# Matrix inversion
t = time()
for i in range(niter):
    np.linalg.inv(J)

delta = time() - t
print("Inversion of a %dx%d matrix in %0.2f s." % (size / 2, size / 2, delta / niter))

# Eigen decomposition
t = time()
for i in range(niter_eigen):
    np.linalg.eig(G)

delta = time() - t
print("Eigendecomposition of a %dx%d matrix in %0.2f s." % (size / 2, size / 2, delta / niter_eigen))
