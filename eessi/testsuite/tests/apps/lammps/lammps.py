"""
This module tests the binary 'lmp' in available modules containing substring 'LAMMPS'.
The tests come from the lammps github repository (https://github.com/lammps/lammps/)
"""

import reframe as rfm
from reframe.core.builtins import deferrable, parameter, performance_function, run_after, sanity_function
import reframe.utility.sanity as sn

from eessi.testsuite import utils
from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES, SCALES
from eessi.testsuite.eessi_mixin import EESSI_Mixin

from statistics import mean

# Todo should find a way to set the tag CI when the module of LAMMPS is not a fat-build
# The only way to easily check it without running lmp is to check the easyconfig in software dir


def split(list, size):
    """Split a sequence into equally‑sized chunks of length 'size'."""
    return [list[i:i + size] for i in range(0, len(list), size)]


def filter_scale_up_to_8_cores():
    """
    Returns all scales with (guaranteed) 8 cores or less. E.g. 1_core, 2_core, ..., 1cpn_2nodes, ...
    Does not return scales like 1_8_node, since for this scale the number of cores is system-dependent.
    """
    return [
        k for (k, v) in SCALES.items()
        if ('num_cpus_per_node' in v.keys() and v.keys() and v['num_cpus_per_node'] * v['num_nodes'] <= 8)
    ]


def filter_scale_partial_and_full_nodes():
    """
    Returns all scales that do have a (guaranteed) core count, e.g. 1_8_node, 1_4_node, ..., 2_nodes, ..., 16_nodes.
    Does not return scales that nhave `num_cpus_per_node` set.
    """
    return [
        k for (k, v) in SCALES.items()
        if 'num_cpus_per_node' not in v.keys()
    ]


class EESSI_LAMMPS_base(rfm.RunOnlyRegressionTest):
    """
    Base class for the LAMMPS based tests. This sets time limit, device type, module name, the compute unit and
    a number of sanity functions that may be shared amongst concrete implementations of this base class.
    """
    time_limit = '30m'
    device_type = parameter([DEVICE_TYPES.CPU, DEVICE_TYPES.GPU])

    # Parameterize over all modules that start with LAMMPS
    module_name = parameter(utils.find_modules('LAMMPS'))

    all_readonly_files = True
    is_ci_test = True

    def required_mem_per_node(self):
        mem = {'slope': 0.07, 'intercept': 0.5}
        return (self.num_tasks_per_node * mem['slope'] + mem['intercept']) * 1024

    # Set sanity step
    @deferrable
    def assert_lammps_openmp_treads(self):
        '''Assert that OpenMP thread(s) per MPI task is set'''
        n_threads = sn.extractsingle(
            r'^  using (?P<threads>[0-9]+) OpenMP thread\(s\) per MPI task', self.stdout, 'threads', int)
        utils.log(f'OpenMP thread(s) is {n_threads}')

        return sn.assert_eq(n_threads, self.num_cpus_per_task)

    @deferrable
    def assert_lammps_processor_grid(self):
        '''Assert that the processor grid is set correctly'''
        grid = list(sn.extractall(
            '^  (?P<x>[0-9]+) by (?P<y>[0-9]+) by (?P<z>[0-9]+) MPI processor grid', self.stdout, tag=['x', 'y', 'z']))
        n_cpus = int(grid[0][0]) * int(grid[0][1]) * int(grid[0][2])

        return sn.assert_eq(n_cpus, self.num_tasks)

    @deferrable
    def assert_run(self):
        '''Assert that the test calulated the right number of neighbours'''
        regex = r'^Loop time of (?P<perf>[.0-9]+) on [0-9]+ procs for 100 steps with (?P<atoms>\S+) atoms'
        n_atoms = sn.extractsingle(regex, self.stdout, 'atoms', int)

        return sn.assert_eq(n_atoms, 32000)

    @deferrable
    def assert_run_steps(self, ref_nsteps=10000):
        '''Assert that the test calulated the right number of steps'''
        regex = r'^Loop time of (?P<perf>[.0-9]+) on [0-9]+ procs for (?P<steps>\S+) steps with [0-9]+ atoms'
        n_steps = sn.extractsingle(regex, self.stdout, 'steps', int)
        return sn.assert_eq(n_steps, ref_nsteps)

    @run_after('init')
    def set_compute_unit(self):
        """Set the compute unit to which tasks will be assigned """
        if self.device_type == DEVICE_TYPES.CPU:
            self.compute_unit = COMPUTE_UNITS.CPU
        elif self.device_type == DEVICE_TYPES.GPU:
            self.compute_unit = COMPUTE_UNITS.GPU
        else:
            msg = f"No mapping of device type {self.device_type} to a COMPUTE_UNITS was specified in this test"
            raise NotImplementedError(msg)

    @run_after('setup')
    def set_executable_opts(self):
        """Set executable opts based on device_type parameter"""
        # should also check if the lammps is installed with kokkos.
        # Because this executable opt is only for that case.
        if self.device_type == DEVICE_TYPES.GPU:
            if 'kokkos' in self.module_name:
                self.executable_opts += [
                    f'-kokkos on t {self.num_cpus_per_task} g {self.num_gpus_per_node}',
                    '-suffix kk',
                    '-package kokkos newton on neigh half',
                ]
                utils.log(f'executable_opts set to {self.executable_opts}')
            else:
                self.executable_opts += [f'-suffix gpu -package gpu {self.num_gpus_per_node}']
                utils.log(f'executable_opts set to {self.executable_opts}')

    # Function to check NDS
    def compute_ndenprof(self, values, bins, start, stop):
        """Checking the values in nden_profile.out"""
        # check nden_profile.out
        LbufferEnd = 5.039193729003359
        RbufferStart = 28.555431131019034

        nds_all, dist_all, nds_avg_all = [], [], []
        for value in values:
            value = value.split()
            dist = float(value[1])
            nds = float(value[3])
            dist_all.append(dist)
            nds_all.append(nds)
            if (dist > LbufferEnd and dist < RbufferStart):
                nds_avg_all.append(nds)

        # mean NDS should be around 3.0 (+-0.05) in between buffer regions
        mean_nds = mean(nds_avg_all)
        if (abs(mean_nds - 3.0) > 0.05):
            utils.log('NDS is WRONG!')
            return False
        else:
            return True

    @deferrable
    def assert_NDS(self):
        '''Assert that the calculated energy at timestep 100 is with the margin of error'''
        regex = r'^\s+[.0-9]+\s+[.0-9]+\s+[.0-9]+\s+[.0-9]+$'
        values = sn.extractall(regex, 'nden_profile.out')
        return self.compute_ndenprof(values, 30, 10, 100)

    @performance_function('timesteps/s')
    def perf(self):
        # Note: final number may have different units, e.g. katom-step or Matom-step. This matches all.
        regex = r'^Performance: [.0-9]+ tau/day, (?P<perf>[.0-9]+) timesteps/s, [.0-9]+ [a-zA-Z]*atom-step/s'
        return sn.extractsingle(regex, self.stdout, 'perf', float)


@rfm.simple_test
class EESSI_LAMMPS_lj(EESSI_LAMMPS_base, EESSI_Mixin):
    sourcesdir = 'src/lj'
    executable = 'lmp -in in.lj'

    @deferrable
    def check_number_neighbors(self):
        '''Assert that the test calulated the right number of neighbours'''
        regex = r'Neighbor list builds = (?P<neigh>\S+)'
        n_neigh = sn.extractsingle(regex, self.stdout, 'neigh', int)
        return sn.assert_eq(n_neigh, 5)

    @deferrable
    def assert_energy(self):
        '''Assert that the calculated energy at timestep 100 is with the margin of error'''
        regex = r'^\s+100\s+[-+]?[.0-9]+\s+[-+]?[.0-9]+\s+0\s+(?P<energy>[-+]?[.0-9]+)'
        energy = sn.extractsingle(regex, self.stdout, 'energy', float)
        energy_diff = sn.abs(energy - (-4.6223613))
        return sn.assert_lt(energy_diff, 1e-4)

    @sanity_function
    def assert_sanity(self):
        '''Check all sanity criteria'''
        return sn.all([
            self.assert_lammps_openmp_treads(),
            self.assert_lammps_processor_grid(),
            self.assert_run(),
            self.check_number_neighbors(),
            self.assert_energy(),
        ])


@rfm.simple_test
class EESSI_LAMMPS_rhodo(EESSI_LAMMPS_base, EESSI_Mixin):
    sourcesdir = 'src/rhodo'
    executable = 'lmp -in in.rhodo'
    is_ci_test = False

    @deferrable
    def check_number_neighbors(self):
        '''Assert that the test calulated the right number of neighbours'''
        regex = r'Neighbor list builds = (?P<neigh>\S+)'
        n_neigh = sn.extractsingle(regex, self.stdout, 'neigh', int)
        return sn.assert_eq(n_neigh, 11)

    @deferrable
    def assert_energy(self):
        '''Assert that the calculated energy at timestep 100 is with the margin of error'''
        regex = r'^-+\s+Step\s+100\s+-+\s+CPU\s=\s+[.0-9]+\s+\(sec\)\s+-+\nTotEng\s+=\s+(?P<energy>[-+]?[.0-9]+)'
        energy = sn.extractsingle(regex, self.stdout, 'energy', float)
        energy_diff = sn.abs(energy - (-25290.7300))
        return sn.assert_lt(energy_diff, 1e-1)

    @sanity_function
    def assert_sanity(self):
        '''Check all sanity criteria'''
        return sn.all([
            self.assert_lammps_openmp_treads(),
            self.assert_lammps_processor_grid(),
            self.assert_run(),
            self.check_number_neighbors(),
            self.assert_energy(),
        ])

    @performance_function('timesteps/s')
    def perf(self):
        regex = r'^Performance: [.0-9]+ ns/day, [.0-9]+ hours/ns, (?P<perf>[.0-9]+) timesteps/s'
        return sn.extractsingle(regex, self.stdout, 'perf', float)


class EESSI_LAMMPS_ALL_balance_staggered_global_base(EESSI_LAMMPS_base):
    """Base class for test cases that test ALL (A Load Balancing Library) integration with LAMMPS.
    The key feature of this class is a sanity check that determines if either load balancing has improved
    over the course of the run, or if load balancing was already good from the start."""
    sourcesdir = 'src/ALL+OBMD'

    # This requires a LAMMPS with ALL functionality, i.e. only select modules with ALL in the versionsuffix
    module_name = parameter(utils.find_modules(r'LAMMPS\/.*-.*ALL', name_only=False))

    @deferrable
    def check_number_neighbors(self):
        '''Assert that the test calulated the right number of neighbours'''
        regex = r'Neighbor list builds = (?P<neigh>\S+)'
        n_neigh = sn.extractsingle(regex, self.stdout, 'neigh', int)
        n_neigh_diff = sn.abs(n_neigh - 2529)
        return sn.assert_lt(n_neigh_diff, 1100)

    @sanity_function
    def assert_sanity(self):
        '''Check all sanity criteria'''
        return sn.all([
            self.assert_lammps_openmp_treads(),
            self.assert_lammps_processor_grid(),
            self.assert_run_steps(),
            self.assert_imbalence(),
        ])

    @run_after('init')
    def check_if_ALL_included(self):
        """Only run this test when LAMMPS has the ALL package."""
        # Can determine if this is included based on the versionsuffix.
        # At this moment the package is not upstream available and has the versionsuffix ALL.
        # See https://github.com/multixscale/dev.eessi.io-lammps-plugin-obmd/pull/7
        if 'ALL' in self.module_name:
            return
        else:
            self.skip(msg="This test is not going to pass since this LAMMPS package does not include ALL."
                          "test will definitely fail, therefore skipping this test.")

    @deferrable
    def assert_imbalence(self):
        '''Assert that the imbalance has gone down by at least 50%, OR that it was already very low (<1.1)'''
        # If imb is 1, that indicates perfect balance. So the imbalance is essentially imb-1.
        initial_imbalance = sn.extractsingle(self.init_imb_regex, self.stdout, 'imb', float) - 1
        final_imbalance = sn.extractsingle(self.final_imb_regex, self.stdout, 'imb', float) - 1
        utils.log(f"Improved load balancing from {initial_imbalance} to {final_imbalance} (0 = perfect balance).")

        # Check if imbalance was small both at the start and end
        no_imbalance = sn.all(
            [initial_imbalance < 0.1, final_imbalance < 0.1]
        )

        if no_imbalance:
            utils.log("No imbalance at either start or end of the simulation. Sanity check will pass.")
            # If there was no imbalance at start or end, just assert that this was the case
            return sn.assert_true(no_imbalance)
        elif final_imbalance == 0:
            # Protect from division by zero. A final imbalance of 0 is an 'infinite' improvement
            # and should thus make this sanity check pass
            utils.log("Final imbalance was 0. Sanity check will pass.")
            return sn.assert_eq(final_imbalance, 0)
        else:
            # Compute improvement in imbalance, and check that imbalance improved by at least 50%
            improvement = initial_imbalance / final_imbalance
            utils.log(f"Improved load balancing by a factor of: {improvement}.")
            return sn.assert_gt(initial_imbalance / final_imbalance, 1.5)


@rfm.simple_test
class EESSI_LAMMPS_ALL_balance_staggered_global_small(EESSI_LAMMPS_ALL_balance_staggered_global_base, EESSI_Mixin):
    """Implementation of a small-scale test case (running up to 8 cores) that tests load balancing
    in LAMMPS through the ALL library."""
    executable = 'lmp -in in.balance.staggered.global.small'
    scale = parameter(filter_scale_up_to_8_cores())

    # Extract the number in the 14th column (which is the imbalance) from the row that has with '50'
    # in the first column (i.e. step 50)
    init_imb_regex = (
        r'^\s+50\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(?P<imb>[-+]?[.0-9]+)\s'
    )

    # Extract the number in the 14th column (which is the imbalance) from the row that has with '10000'
    # in the first column (i.e. step 10000)
    final_imb_regex = (
        r'^\s+10000\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(?P<imb>[-+]?[.0-9]+)\s'
    )


@rfm.simple_test
class EESSI_LAMMPS_ALL_balance_staggered_global_large(EESSI_LAMMPS_ALL_balance_staggered_global_base, EESSI_Mixin):
    """Implementation of a large-scale test case (running up to 1/8th of a node and larger) that tests load
        balancing in LAMMPS through the ALL library."""
    executable = 'lmp -var x 10 -var y 10 -var z 10 -var t 1000 -in in.balance.staggered.global.large'
    scale = parameter(filter_scale_partial_and_full_nodes())

    # Extract the number in the 6th column (which is the imbalance) from the row that has with '50'
    # in the first column (i.e. step 50)
    init_imb_regex = (
        r'^\s+50\s+\S+\s+\S+\s+\S+\s+\S+\s+(?P<imb>[-+]?[.0-9]+)\s+\S+\s+\S+\s+\S+\s+\S+\s*$'
    )
    # Extract the number in the 6th column (which is the imbalance) from the row that has with '1000'
    # in the first column (i.e. step 1000)
    final_imb_regex = (
        r'^\s+1000\s+\S+\s+\S+\s+\S+\s+\S+\s+(?P<imb>[-+]?[.0-9]+)\s+\S+\s+\S+\s+\S+\s+\S+\s*$'
    )

    @sanity_function
    def assert_sanity(self):
        '''Check all sanity criteria'''
        return sn.all([
            self.assert_lammps_openmp_treads(),
            self.assert_lammps_processor_grid(),
            self.assert_run_steps(ref_nsteps=1000),
            self.assert_imbalence(),
        ])


@rfm.simple_test
class EESSI_LAMMPS_ALL_OBMD_simulation_staggered_global(EESSI_LAMMPS_base, EESSI_Mixin):
    """Test case testing a combination of Open-Boundary Molecular Dynamics (OBMD) and A Load balancing
    Library (ALL) functionality in LAMMPS. OBMD simulations are characterized by dynamically changing particle
    populations and strongly non-uniform spatial workloads due to particle insertion, removal, and fluxes across
    open boundaries. In this context, efficient load balancing is particularly critical to sustain scalability and
    numerical efficiency, as imbalances can rapidly arise during the simulation.

    The test simulates liquid water under equilibrium conditions, which is described using the mesoscopic DPD
    water model. The density of DPD water in the region of interest is checked as part of the sanity check.
    If the density equals the desired value (within predetermined error), the test is successful."""
    sourcesdir = 'src/ALL+OBMD'

    executable = 'lmp -in in.simulation.staggered.global'

    # This requires a LAMMPS with ALL+OMBD functionality, i.e. only select modules with -ALL_OBMD versionsuffix
    module_name = parameter(utils.find_modules(r'LAMMPS\/.*-.*ALL.*OBMD', name_only=False))

    @sanity_function
    def assert_sanity(self):
        '''Check all sanity criteria'''
        return sn.all([
            self.assert_lammps_openmp_treads(),
            self.assert_lammps_processor_grid(),
            self.assert_run_steps(),
            self.assert_NDS(),
        ])

    @run_after('init')
    def check_if_ALL_OBMD_included(self):
        """Only run this test when LAMMPS has the OBMD package."""
        # Can determine if this is included based on the versionsuffix.
        # At this moment the package is not upstream available and has the versionsuffix ALL.
        # See https://github.com/multixscale/dev.eessi.io-lammps-plugin-obmd/pull/7
        if 'ALL' in self.module_name and 'OBMD' in self.module_name:
            return
        else:
            self.skip(msg="This test is not going to pass since this LAMMPS package does not include ALL."
                          "test will definitely fail, therefore skipping this test.")


@rfm.simple_test
class EESSI_LAMMPS_OBMD_simulation(EESSI_LAMMPS_base, EESSI_Mixin):
    """Test case testing Open-Boundary Molecular Dynamics (OBMD) functionality in LAMMPS. The test
    simulates liquid water under equilibrium conditions, which is described using the mesoscopic DPD
    water model. The density of DPD water in the region of interest is checked as part of the sanity check.
    If the density equals the desired value (within predetermined error), the test is successful."""
    sourcesdir = 'src/ALL+OBMD'

    prerun_cmds = ['python generate_obmd_input.py']

    executable = 'lmp -in in.simulation'

    # This requires a LAMMPS with OBMD functionality, i.e. only select modules with -OBMD versionsuffix
    # We _could_ remove the '-' and '$' to also match e.g. ALL_OBMD
    module_name = parameter(utils.find_modules(r'LAMMPS\/.*-.*OBMD', name_only=False))

    @sanity_function
    def assert_sanity(self):
        '''Check all sanity criteria'''
        return sn.all([
            self.assert_lammps_openmp_treads(),
            self.assert_lammps_processor_grid(),
            self.assert_run_steps(),
            self.assert_NDS(),
        ])

    @run_after('init')
    def check_if_OBMD_included(self):
        """Only run this test when LAMMPS has the ALL package."""
        # Can determine if this is included based on the versionsuffix.
        # At this moment the package is not upstream available and has the versionsuffix ALL.
        # See https://github.com/multixscale/dev.eessi.io-lammps-plugin-obmd/pull/7
        if 'OBMD' in self.module_name:
            return
        else:
            self.skip(msg="This test is not going to pass since this LAMMPS package does not include ALL."
                          "test will definitely fail, therefore skipping this test.")
