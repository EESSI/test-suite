"""
=====================
2D Mixing Layer Test
=====================
This test case simulates the Kelvin-Helmholtz instabilty where an initial
hyperbolic tangent velocity profile imposed in a fully periodic 2D square box is
slightly perturbed to initiate rolling of the shear layers.

The dimension of the side length of the bounding box and the non-dimensional run
time are specified through the --grid-size and the --run-time command line
arguments respectively. If unspecified default values of 256 and 1.0 are used.

The test conducts a validation run and computes the normalized kinetic energy as
a validation metric. Further, the performance of the employed stream-collide
algorithm is evaluated and reported in Mega lattice updates per seconds (MLUPS).

The test can be executed run in 2 modes, namely, serial/openmp parallelized.

Serial runs:
    python mixing_layer_2D.py

OpenMP parallel runs:
    OMP_NUM_THREADS=4 python mixing_layer_2D.py --openmp
"""

from lbmpy.methods.population_space import PopulationSpaceBGK

from lbmpy import LBStencil, LBMOptimisation, create_lb_update_rule
from lbmpy.equilibrium import DiscreteHydrodynamicMaxwellian
from lbmpy.macroscopic_value_kernels import macroscopic_values_setter

import numpy
import pystencils as ps

from statistics import median

import argparse
import time


def run_benchmark(N: int, runtime: float, use_omp: bool):
    target = ps.Target.CPU
    stencil = LBStencil("D2Q9")
    # number of ghost layers
    ngl = max([element for velocity in stencil.stencil_entries for element in velocity])

    kernel_config = ps.CreateKernelConfig(target=target, cpu_openmp=use_omp)

    equilibrium = DiscreteHydrodynamicMaxwellian(
        stencil=stencil,
        compressible=True,
        deviation_only=False,
        c_s_sq=stencil.theta0,
        order=3,
    )

    srt_method = PopulationSpaceBGK(
        stencil=stencil,
        feq=equilibrium,
        isothermal=True,
    )

    # Domain and Arrays

    # grid points
    Ny = Nx = N
    # data handler (NxN periodic grid laid out in Structure of Arrays format)
    dh = ps.create_data_handling(
        domain_size=(Ny, Nx),
        periodicity=(True, True),
        default_ghost_layers=ngl,
        default_target=target,
        default_layout="fzyx",
    )

    # create population arrays
    f = dh.add_array(name="f", values_per_cell=stencil.Q)
    f_tmp = dh.add_array(name="f_tmp", values_per_cell=stencil.Q)

    # create field arrays
    rho = dh.add_array(name="rho", values_per_cell=1)
    u = dh.add_array(name="u", values_per_cell=stencil.D)

    # Stream-Collide Kernel

    lbm_opt = LBMOptimisation(symbolic_field=f, symbolic_temporary_field=f_tmp)

    output_fields = dict({"density": rho, "velocity": u})

    update_rule = create_lb_update_rule(
        lb_method=srt_method, lbm_optimisation=lbm_opt, output=output_fields
    )

    # create stream-collide kernel
    ker_stream_collide = ps.create_kernel(update_rule, config=kernel_config).compile()

    ac_init = macroscopic_values_setter(
        lb_method=srt_method,
        density=rho.center,  # rho_(0,0)
        velocity=u.center_vector,  # \vec{u}_(0,0)
        pdfs=f,
        set_pre_collision_pdfs=True,
    )

    ker_init = ps.create_kernel(ac_init, config=kernel_config).compile()

    # Initial state
    # \begin{align}
    #     \rho &= 1 \\
    #     u_x
    #     &=
    #     \begin{cases}
    #         u_0 \tanh \left[ \kappa \left( \frac{y}{N} - \frac{1}{4} \right)\right], \, y \leq \frac{N}{2} \\
    #         u_0 \tanh \left[ \kappa \left( \frac{3}{4} - \frac{y}{N} \right)\right], \, y > \frac{N}{2}
    #     \end{cases}\\
    #     u_y
    #     &=
    #     \delta u_0 \sin \left[2\pi\left( \frac{x}{N} + \frac{1}{4} \right)\right]
    # \end{align}

    # Parameters
    kappa = 80  # shear layer width
    u0 = 0.04  # velocity scale
    delta = 0.05  # perturbation parameter
    reynolds = 30000  # Reynolds number

    # Initialize the density and velocity fields to unity and zero
    dh.fill(rho.name, 1.0)
    dh.fill(u.name, 0.0)

    # initialize the velocity field
    _x = numpy.linspace(0, 1, Nx)
    _y = numpy.linspace(0, 1, Ny)

    for y in range(Ny):
        dh.cpu_arrays[u.name][ngl: -1 * ngl, ngl + y, 1] = delta * numpy.sin(
            2 * numpy.pi * (_x + 0.25)
        )

    tmp = numpy.zeros_like(_y)
    tmp[: Ny // 2] = numpy.tanh(kappa * (_y[: Ny // 2] - 0.25))
    tmp[Ny // 2:] = numpy.tanh(kappa * (0.75 - _y[Ny // 2:]))

    for x in range(Nx):
        dh.cpu_arrays[u.name][ngl + x, ngl: -1 * ngl, 0] = tmp

    dh.cpu_arrays[u.name] *= u0

    # run the initalization kernel
    dh.run_kernel(ker_init)

    # Integration Loop

    # global synchronization function
    gl_sync = dh.synchronization_function(
        f.name, target=target, optimization={"openmp": use_omp}
    )

    def step():
        dh.run_kernel(
            kernel_function=ker_stream_collide,
            alpha=srt_method.compute_alpha(),
            beta=srt_method.compute_beta_from_reynolds_number(Re=30000, u=u0, N=N),
        )

        dh.swap(f.name, f_tmp.name)
        gl_sync()

    def loop(n):
        for iteration in range(n):
            step()

    # Simulation Run

    # characteristic time
    t0 = int(runtime * N / u0)

    print(
        f"""
    LB Configuration:
    -----------------
        1. D2Q9 lattice with O(u^3) polynomial equilibrium
        2. BGK Collision Model
        3. Isothermal temperature: lattice reference temperature (theta = 1/3)

    Case Parameters:
    ----------------
        1. Re = {reynolds}    # Reynolds
        2. u0 = {u0}     # velocity scale
        3. Nx = Ny = {N} grid points
        4. run time = {runtime} -> ({runtime} * N / u0) = {t0} iterations

    Validation run:
    ---------------
        Running simulation for {t0} iterations ...""",
        end=" ",
    )

    start_time = time.perf_counter()
    # run
    loop(t0)
    print("done")
    print(
        """
        Computing normalized averaged kinetic energy ...""",
        end=" ",
    )
    ufinal = dh.gather_array(u.name)
    print("done")

    keNorm = numpy.mean(ufinal[:, :, 0] ** 2 + ufinal[:, :, 1] ** 2)
    keNorm /= (u0) ** 2

    end_time = time.perf_counter()
    print(
        f"""\t\tNormalized Average Kinetic Energy =  {keNorm:.4f}

        Completed in {(end_time - start_time):.2f}s

    Performance in Mega lattice updates per second (MLUPS):
    -------------------------------------------------------"""
    )

    # Performance Evaluation
    # adapted from lbmstep.py
    def get_time_loop():
        fixed_loop = ps.timeloop.TimeLoop(steps=2)
        fixed_loop.add_single_step_function(step)
        arg_dict = dh.get_kernel_kwargs(ker_stream_collide)[0]

        arg_dict["alpha"] = srt_method.compute_alpha()
        arg_dict["beta"] = srt_method.compute_beta_from_reynolds_number(
            Re=30000, u=u0, N=N
        )

        for t in range(2):
            fixed_loop.add_call(gl_sync, {})
            fixed_loop.add_call(ker_stream_collide, arg_dict)
            dh.swap(f.name, f_tmp.name)

        return fixed_loop

    def benchmark(
        time_for_benchmark=5,
        init_time_steps=2,
        number_of_time_steps_for_estimation="auto",
    ):
        time_loop = get_time_loop()
        duration_of_time_step = time_loop.benchmark(
            time_for_benchmark, init_time_steps, number_of_time_steps_for_estimation
        )
        mlups = (N * N) / duration_of_time_step * 1e-6
        return mlups

    start_time = time.perf_counter()
    mlups = [benchmark() for _ in range(5)]
    end_time = time.perf_counter()

    result_str = "{mlups:.0f}±{diff:.2f}".format(
        mlups=median(mlups), diff=max(mlups) - min(mlups)
    )
    print(
        f"""\tEvaluated for 5 instances of the stream-collide operation
            Median±(max-min) = {result_str} MLUPS

        Completed in {(end_time - start_time):.2f}s
    -------------------------------------------------------"""
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--grid-size", default=256, type=int, help="Number of grid points (default 256)"
    )
    parser.add_argument(
        "--run-time",
        default=1.0,
        type=float,
        help="Non-dimensional run time (default 1.0)",
    )
    parser.add_argument(
        "--openmp",
        action="store_true",
        help="OpenMP parallel run. Serial Execution if not provided.",
    )
    args = parser.parse_args()

    execution_mode = "OMP parallel" if args.openmp else "serial"
    case_description = "\n".join(__doc__.splitlines()[:3])

    print(
        f"""{case_description}

    Execution Mode:
    ---------------
        {execution_mode.title()} Run"""
    )

    start_time = time.perf_counter()
    run_benchmark(args.grid_size, args.run_time, args.openmp)
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    minutes = int(elapsed_time // 60)
    seconds = elapsed_time % 60
    print(
        f"""
    Test completed in {minutes}min {seconds:0.2f}s.
    ==============================================="""
    )
