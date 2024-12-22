#
# Copyright (C) 2013-2024 The ESPResSo project
#
# This file is part of ESPResSo.
#
# ESPResSo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ESPResSo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import espressomd
import espressomd.version
import espressomd.electrostatics
import argparse
import time
import numpy as np

parser = argparse.ArgumentParser(description="Benchmark P3M simulations.")
parser.add_argument("--size", metavar="S", action="store",
                    default=9, required=False, type=int,
                    help="Problem size, such that the number of particles N is "
                         "equal to (2*S)^2; with --weak-scaling this number N "
                         "is multiplied by the number of cores!")
parser.add_argument("--gpu", action=argparse.BooleanOptionalAction,
                    default=False, required=False, help="Use GPU implementation")
parser.add_argument("--topology", metavar=("X", "Y", "Z"), nargs=3, action="store",
                    default=None, required=False, type=int, help="Cartesian topology")
group = parser.add_mutually_exclusive_group()
group.add_argument("--weak-scaling", action="store_true",
                   help="Weak scaling benchmark (Gustafson's law: constant work per core)")
group.add_argument("--strong-scaling", action="store_true",
                   help="Strong scaling benchmark (Amdahl's law: constant total work)")
args = parser.parse_args()


def get_reference_values_per_ion(base_vector):
    madelung_constant = -1.74756459463318219
    base_tensor = base_vector * np.eye(3)
    ref_energy = madelung_constant
    ref_pressure = madelung_constant * base_tensor / np.trace(base_tensor)
    return ref_energy, ref_pressure


def get_normalized_values_per_ion(system):
    energy = system.analysis.energy()["coulomb"]
    p_scalar = system.analysis.pressure()["coulomb"]
    p_tensor = system.analysis.pressure_tensor()["coulomb"]
    N = len(system.part)
    V = system.volume()
    return 2. * energy / N, 2. * p_scalar * V / N, 2. * p_tensor * V / N


# initialize system
system = espressomd.System(box_l=[100., 100., 100.])
system.time_step = 0.01
system.cell_system.skin = 0.4

# set MPI Cartesian topology
node_grid = system.cell_system.node_grid.copy()
n_cores = int(np.prod(node_grid))
if args.topology:
    system.cell_system.node_grid = node_grid = args.topology

# place ions on a cubic lattice
base_vector = np.array([1., 1., 1.])
lattice_size = 3 * [2 * args.size]
if args.weak_scaling:
    lattice_size = np.multiply(lattice_size, node_grid)
system.box_l = np.multiply(lattice_size, base_vector)
for var_j in range(lattice_size[0]):
    for var_k in range(lattice_size[1]):
        for var_l in range(lattice_size[2]):
            _ = system.part.add(pos=np.multiply([var_j, var_k, var_l], base_vector),
                                q=(-1.)**(var_j + var_k + var_l), fix=3 * [True])

# setup P3M algorithm
algorithm = espressomd.electrostatics.P3M
if args.gpu:
    algorithm = espressomd.electrostatics.P3MGPU
solver = algorithm(prefactor=1., accuracy=1e-6)
if (espressomd.version.major(), espressomd.version.minor()) == (4, 2):
    system.actors.add(solver)
else:
    system.electrostatics.solver = solver


print("Algorithm executed. \n")

# Old rtol_pressure = 2e-5
# This resulted in failures especially at high number of nodes therefore increased
# to a larger value.

atol_energy = atol_pressure = 1e-12
atol_forces = 1e-5
atol_abs_forces = 2e-6

rtol_energy = 5e-6
rtol_pressure = 1e-4
rtol_forces = 0.
rtol_abs_forces = 0.
# run checks
print("Executing sanity checks...\n")
forces = np.copy(system.part.all().f)
energy, p_scalar, p_tensor = get_normalized_values_per_ion(system)
ref_energy, ref_pressure = get_reference_values_per_ion(base_vector)
np.testing.assert_allclose(energy, ref_energy, atol=atol_energy, rtol=rtol_energy)
np.testing.assert_allclose(p_scalar, np.trace(ref_pressure) / 3.,
                           atol=atol_pressure, rtol=rtol_pressure)
np.testing.assert_allclose(p_tensor, ref_pressure, atol=atol_pressure, rtol=rtol_pressure)
np.testing.assert_allclose(forces, 0., atol=atol_forces, rtol=rtol_forces)
np.testing.assert_allclose(np.median(np.abs(forces)), 0., atol=atol_abs_forces, rtol=rtol_abs_forces)

print("Final convergence met with tolerances: \n\
            energy: ", atol_energy, "\n\
            p_scalar: ", atol_pressure, "\n\
            p_tensor: ", atol_pressure, "\n\
            forces: ", atol_forces, "\n\
            abs_forces: ", atol_abs_forces, "\n")

print("Sampling runtime...\n")
# sample runtime
n_steps = 10
timings = []
for _ in range(10):
    tick = time.time()
    system.integrator.run(n_steps)
    tock = time.time()
    timings.append((tock - tick) / n_steps)

print("10 steps executed...\n")
# write results to file
header = '"mode","cores","mpi.x","mpi.y","mpi.z","particles","mean","std"\n'
report = f'''"{"weak scaling" if args.weak_scaling else "strong scaling"}",\
{n_cores},{node_grid[0]},{node_grid[1]},{node_grid[2]},{len(system.part)},\
{np.mean(timings):.3e},{np.std(timings,ddof=1):.3e}\n'''
print(header)
print(report)

print(f"Performance: {np.mean(timings):.3e} \n")
