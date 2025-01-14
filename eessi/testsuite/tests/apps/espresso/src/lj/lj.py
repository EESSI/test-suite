#
# Copyright (C) 2018-2024 The ESPResSo project
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

import argparse
import time
import espressomd
import numpy as np

required_features = ["LENNARD_JONES"]
espressomd.assert_features(required_features)

parser = argparse.ArgumentParser(description="Benchmark LJ simulations.")
parser.add_argument("--particles-per-core", metavar="N", action="store",
                    type=int, default=2000, required=False,
                    help="Number of particles in the simulation box")
parser.add_argument("--sample-size", metavar="S", action="store",
                    type=int, default=30, required=False,
                    help="Sample size")
parser.add_argument("--volume-fraction", metavar="FRAC", action="store",
                    type=float, default=0.50, required=False,
                    help="Fraction of the simulation box volume occupied by "
                    "particles (range: [0.01-0.74], default: 0.50)")
args = parser.parse_args()

# process and check arguments
measurement_steps = 100
if args.particles_per_core < 16000:
    measurement_steps = 200
if args.particles_per_core < 10000:
    measurement_steps = 500
if args.particles_per_core < 5000:
    measurement_steps = 1000
if args.particles_per_core < 1000:
    measurement_steps = 2000
if args.particles_per_core < 600:
    measurement_steps = 4000
if args.particles_per_core < 260:
    measurement_steps = 6000
assert args.volume_fraction > 0., "volume_fraction must be a positive number"
assert args.volume_fraction < np.pi / (3. * np.sqrt(2.)), \
    "volume_fraction exceeds the physical limit of sphere packing (~0.74)"

# make simulation deterministic
np.random.seed(42)


def get_reference_values_per_atom(x):
    # result of a polynomial fit in the range from 0.01 to 0.55
    energy = 54.2 * x**3 - 23.8 * x**2 + 4.6 * x - 0.09
    pressure = 377. * x**3 - 149. * x**2 + 32.2 * x - 0.58
    return energy, pressure


def get_normalized_values_per_atom(system):
    energy = system.analysis.energy()["non_bonded"]
    pressure = system.analysis.pressure()["non_bonded"]
    N = len(system.part)
    V = system.volume()
    return 2. * energy / N, 2. * pressure * V / N


system = espressomd.System(box_l=[10., 10., 10.])
system.time_step = 0.01
system.cell_system.skin = 0.5

lj_eps = 1.0  # LJ epsilon
lj_sig = 1.0  # particle diameter
lj_cut = lj_sig * 2**(1. / 6.)  # cutoff distance

n_proc = system.cell_system.get_state()["n_nodes"]
n_part = n_proc * args.particles_per_core
node_grid = np.array(system.cell_system.node_grid)
# volume of N spheres with radius r: N * (4/3*pi*r^3)
box_v = args.particles_per_core * 4. / 3. * \
    np.pi * (lj_sig / 2.)**3 / args.volume_fraction
# box_v = (x * n) * x * x for a column
system.box_l = float((box_v)**(1. / 3.)) * node_grid
assert np.abs(n_part * 4. / 3. * np.pi * (lj_sig / 2.)**3 / np.prod(system.box_l) - args.volume_fraction) < 0.1

system.non_bonded_inter[0, 0].lennard_jones.set_params(
    epsilon=lj_eps, sigma=lj_sig, cutoff=lj_cut, shift="auto")

system.part.add(pos=np.random.random((n_part, 3)) * system.box_l)

# energy minimization
max_steps = 1000
# particle forces for volume fractions between 0.1 and 0.5 follow a polynomial
target_f_max = 20. * args.volume_fraction**2
system.integrator.set_steepest_descent(
    f_max=target_f_max, gamma=0.001, max_displacement=0.01 * lj_sig)
n_steps = system.integrator.run(max_steps)
assert n_steps < max_steps, f'''energy minimization failed: \
E = {system.analysis.energy()["total"] / len(system.part):.3g} per particle, \
f_max = {np.max(np.linalg.norm(system.part.all().f, axis=1)):.2g}, \
target f_max = {target_f_max:.2g}'''

# warmup
system.integrator.set_vv()
system.thermostat.set_langevin(kT=1.0, gamma=1.0, seed=42)

# tuning and equilibration
min_skin = 0.2
max_skin = 1.0
print("Tune skin: {:.3f}".format(system.cell_system.tune_skin(
    min_skin=min_skin, max_skin=max_skin, tol=0.05, int_steps=100)))
print("Equilibration")
system.integrator.run(min(5 * measurement_steps, 60000))
print("Tune skin: {:.3f}".format(system.cell_system.tune_skin(
    min_skin=min_skin, max_skin=max_skin, tol=0.05, int_steps=100)))
print("Equilibration")
system.integrator.run(min(10 * measurement_steps, 60000))

print("Sampling runtime...")
timings = []
energies = []
pressures = []
for i in range(args.sample_size):
    tick = time.time()
    system.integrator.run(measurement_steps)
    tock = time.time()
    t = (tock - tick) / measurement_steps
    timings.append(t)
    energy, pressure = get_normalized_values_per_atom(system)
    energies.append(energy)
    pressures.append(pressure)

sim_energy = np.mean(energies)
sim_pressure = np.mean(pressures)
ref_energy, ref_pressure = get_reference_values_per_atom(args.volume_fraction)

print("Algorithm executed. \n")
np.testing.assert_allclose(sim_energy, ref_energy, atol=0., rtol=0.1)
np.testing.assert_allclose(sim_pressure, ref_pressure, atol=0., rtol=0.1)

print("Final convergence met with relative tolerances: \n\
            sim_energy: ", 0.1, "\n\
            sim_pressure: ", 0.1, "\n")

header = '"mode","cores","mpi.x","mpi.y","mpi.z","particles","volume_fraction","mean","std"'
report = f'''"weak scaling",{n_proc},{node_grid[0]},{node_grid[1]},\
{node_grid[2]},{len(system.part)},{args.volume_fraction:.4f},\
{np.mean(timings):.3e},{np.std(timings,ddof=1):.3e}'''
print(header)
print(report)
print(f"Performance: {np.mean(timings):.3e}")
