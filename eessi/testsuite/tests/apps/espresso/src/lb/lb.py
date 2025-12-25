#
# Copyright (C) 2013-2025 The ESPResSo project
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

import os
import time
import argparse
import numpy as np
import espressomd
import espressomd.lb
import espressomd.version

parser = argparse.ArgumentParser(description="Benchmark LB simulations.")
parser.add_argument("--gpu", action=argparse.BooleanOptionalAction,
                    default=False, required=False, help="Use GPU implementation")
parser.add_argument("--topology", metavar=("X", "Y", "Z"), nargs=3, action="store",
                    default=None, required=False, type=int, help="Cartesian topology")
parser.add_argument("--unit-cell", action="store", nargs="+",
                    type=int, default=[64, 64, 64], required=False,
                    help="unit cell size")
parser.add_argument("--single-precision", action="store_true", required=False,
                    help="Using single-precision floating point accuracy")
parser.add_argument("--kT", metavar="kT", action="store",
                    type=float, default=0., required=False,
                    help="Thermostat heat bath")
group = parser.add_mutually_exclusive_group()
group.add_argument("--weak-scaling", action="store_true",
                   help="Weak scaling benchmark (Gustafson's law: constant work per core)")
group.add_argument("--strong-scaling", action="store_true",
                   help="Strong scaling benchmark (Amdahl's law: constant total work)")
group = parser.add_mutually_exclusive_group()
group.add_argument("--particles-per-rank", metavar="N", action="store",
                   type=int, default=0, required=False,
                   help="Number of particles per MPI rank")
group.add_argument("--particles-total", metavar="N", action="store",
                   type=int, default=0, required=False,
                   help="Number of particles in total")
args = parser.parse_args()


required_features = []
if args.particles_per_rank or args.particles_total:
    required_features.append("LENNARD_JONES")
if args.gpu:
    required_features.append("CUDA")
espressomd.assert_features(required_features)
espresso_version = (espressomd.version.major(), espressomd.version.minor())

# initialize system
system = espressomd.System(box_l=[100., 100., 100.])
system.time_step = 0.01
system.cell_system.skin = 0.4

# set MPI Cartesian topology
node_grid = np.array(system.cell_system.node_grid)
n_mpi_ranks = int(np.prod(node_grid))
n_omp_threads = int(os.environ.get("OMP_NUM_THREADS", 1))
if args.topology:
    system.cell_system.node_grid = node_grid = args.topology

if args.weak_scaling:
    system.box_l = np.multiply(np.array(args.unit_cell), node_grid)
else:
    system.box_l = args.unit_cell

if args.particles_total:
    n_part = args.particles_total
else:
    n_part = n_mpi_ranks * args.particles_per_rank

# set CUDA topology
devices = {}
if args.gpu:
    devices = espressomd.cuda_init.CudaInitHandle().list_devices()
    if len(devices) > 1 and espresso_version >= (5, 0):
        system.cuda_init_handle.call_method("set_device_id_per_rank")

# place particles at random
if n_part:
    # volume of N spheres with radius r: N * (4/3*pi*r^3)
    lj_sig = 1.
    lj_eps = 1.
    lj_cut = lj_sig * 2**(1. / 6.)
    volume = float(np.prod(system.box_l))
    vfrac = n_part * 4. / 3. * np.pi * (lj_sig / 2.)**3 / volume
    print(f"volume fraction: {100.*vfrac:.2f}%")
    assert vfrac < 0.74, "invalid volume fraction"
    system.non_bonded_inter[0, 0].lennard_jones.set_params(
        epsilon=lj_eps, sigma=lj_sig, cutoff=lj_cut, shift="auto")
    system.part.add(pos=np.random.random((n_part, 3)) * system.box_l)
    print("minimize")
    energy_target = n_part / 10.
    system.integrator.set_steepest_descent(
        f_max=0., gamma=0.001, max_displacement=0.01)
    system.integrator.run(200)
    energy = system.analysis.energy()["total"]
    assert energy < energy_target, f"Minimization failed to converge to {energy_target:.1f}"
    print("set Langevin")
    system.integrator.set_vv()
    system.thermostat.set_langevin(kT=1., gamma=1., seed=42)
    min_skin = 0.2
    max_skin = 1.0
    print("Tune skin: {:.3f}".format(system.cell_system.tune_skin(
        min_skin=min_skin, max_skin=max_skin, tol=0.05, int_steps=10)))
    print("MD equilibration")
    system.integrator.run(500)
    print("Tune skin: {:.3f}".format(system.cell_system.tune_skin(
        min_skin=min_skin, max_skin=max_skin, tol=0.05, int_steps=10)))
    print("MD equilibration")
    system.integrator.run(500)
    system.thermostat.turn_off()

# setup LB solver
lb_kwargs = {"agrid": 1., "tau": system.time_step, "kT": args.kT}
if espresso_version == (4, 2):
    assert n_omp_threads == 1, "ESPResSo 4.2 doesn't support OpenMP"
    if args.gpu:
        lb_class = espressomd.lb.LBFluidGPU
        assert args.single_precision, "ESPResSo 4.2 LB GPU only available in single-precision"
        assert len(devices) == 1, "ESPResSo 4.2 LB GPU only supports 1 GPU accelerator"
    else:
        lb_class = espressomd.lb.LBFluid
        assert not args.single_precision, "ESPResSo 4.2 LB CPU only available in double-precision"
    lbf = lb_class(dens=1., visc=1., seed=42, **lb_kwargs)
    system.actors.add(lbf)
else:
    if args.gpu:
        lb_class = espressomd.lb.LBFluidWalberlaGPU
    else:
        lb_class = espressomd.lb.LBFluidWalberla
    lbf = lb_class(density=1., kinematic_viscosity=1.,
                   single_precision=args.single_precision, **lb_kwargs)
    system.lb = lbf

if n_part:
    system.thermostat.set_lb(LB_fluid=lbf, seed=42, gamma=1.)

print("LB equilibration")
system.integrator.run(100)


def get_lb_kT(lbf):
    nodes_mass = lbf[:, :, :].density * lbf.agrid**3
    nodes_vel_sq = np.sum(np.square(lbf[:, :, :].velocity), axis=3)
    return np.mean(nodes_mass * nodes_vel_sq) / 3.


def get_md_kT(part):
    return np.mean(np.linalg.norm(part.all().v, axis=1)**2 * part.all().mass) / 3.


print("Sanity checks")
rtol_energy = 0.05
fluid_kTs = []
parts_kTs = []
for _ in range(30):
    fluid_kTs.append(get_lb_kT(lbf))
    if n_part:
        parts_kTs.append(get_md_kT(system.part))
    system.integrator.run(10)
if args.kT == 0.:
    np.testing.assert_almost_equal(np.mean(fluid_kTs), args.kT, decimal=3)
else:
    np.testing.assert_allclose(np.mean(fluid_kTs), args.kT, rtol=rtol_energy)
    if n_part:
        np.testing.assert_allclose(np.mean(parts_kTs), args.kT, rtol=rtol_energy)

print("Final convergence met with tolerances: \n\
            energy: ", rtol_energy, "\n")

print("Benchmark")
n_steps = 40
n_loops = 15
timings = []
for _ in range(n_loops):
    tick = time.time()
    system.integrator.run(n_steps)
    tock = time.time()
    timings.append((tock - tick) / n_steps)

print(f"{n_loops * n_steps} steps executed...")
print("Algorithm executed.")
# write results to file
header = '"mode","cores","mpi.x","mpi.y","mpi.z","omp.threads","gpus",\
"particles","mean","std","box.x","box.y","box.z","precision","hardware"'
report = f'''"{"weak scaling" if args.weak_scaling else "strong scaling"}",\
{n_mpi_ranks * n_omp_threads},{node_grid[0]},{node_grid[1]},{node_grid[2]},\
{n_omp_threads},{len(devices)},{len(system.part)},\
{np.mean(timings):.3e},{np.std(timings,ddof=1):.3e},\
{system.box_l[0]:.2f},{system.box_l[1]:.2f},{system.box_l[2]:.2f},\
"{'sp' if args.single_precision else 'dp'}",\
"{'gpu' if args.gpu else 'cpu'}"'''
print(header)
print(report)

print(f"Performance: {np.mean(timings):.3e} s/step")
