"""
This module tests the binary 'lmp' in available modules containing substring 'LAMMPS'.
The tests come from the lammps github repository (https://github.com/lammps/lammps/)
"""

import reframe as rfm
import reframe.utility.sanity as sn

from eessi.testsuite import hooks, utils
from eessi.testsuite.constants import *  # noqa


class EESSI_LAMMPS_base(rfm.RunOnlyRegressionTest):
    scale = parameter(SCALES.keys())
    valid_prog_environs = ['default']
    valid_systems = ['*']
    time_limit = '30m'
    device_type = parameter([DEVICE_TYPES[CPU], DEVICE_TYPES[GPU]])

    # Parameterize over all modules that start with LAMMPS
    module_name = parameter(utils.find_modules('LAMMPS'))

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

    @run_after('init')
    def run_after_init(self):
        """hooks to run after init phase"""

        # Filter on which scales are supported by the partitions defined in the ReFrame configuration
        hooks.filter_supported_scales(self)

        hooks.filter_valid_systems_by_device_type(self, required_device_type=self.device_type)

        hooks.set_modules(self)

        # Set scales as tags
        hooks.set_tag_scale(self)

    @run_after('setup')
    def run_after_setup(self):
        """hooks to run after the setup phase"""
        if self.device_type == 'cpu':
            hooks.assign_tasks_per_compute_unit(test=self, compute_unit=COMPUTE_UNIT['CPU'])
        elif self.device_type == 'gpu':
            hooks.assign_tasks_per_compute_unit(test=self, compute_unit=COMPUTE_UNIT['GPU'])
        else:
            raise NotImplementedError(f'Failed to set number of tasks and cpus per task for device {self.device_type}')

        # Set OMP_NUM_THREADS environment variable
        hooks.set_omp_num_threads(self)


@rfm.simple_test
class EESSI_LAMMPS_lj(EESSI_LAMMPS_base):
    tags = {TAGS['CI']}

    sourcesdir = 'src/lj'
    executable = 'lmp -in in.lj'

    @deferrable
    def check_number_neighbors(self):
        '''Assert that the test calulated the right number of neighbours'''
        regex = r'^Total # of neighbors = (?P<neigh>\S+)'
        n_neigh = sn.extractsingle(regex, self.stdout, 'neigh', int)

        return sn.assert_eq(n_neigh, 1202833)

    @performance_function('tau/day')
    def perf(self):
        regex = r'^Performance: (?P<perf>[.0-9]+) tau/day,'
        return sn.extractsingle(regex, self.stdout, 'perf', float)

    @sanity_function
    def assert_sanity(self):
        '''Check all sanity criteria'''
        return sn.all([
            self.assert_lammps_openmp_treads(),
            self.assert_lammps_processor_grid(),
            self.assert_run(),
            self.check_number_neighbors(),
        ])

    @run_after('setup')
    def set_executable_opts(self):
        """Set executable opts based on device_type parameter"""
        num_default = 0  # If this test already has executable opts, they must have come from the command line
        hooks.check_custom_executable_opts(self, num_default=num_default)
        if not self.has_custom_executable_opts:
            # should also check if the lammps is installed with kokkos.
            # Because this exutable opt is only for that case.
            if self.device_type == "gpu":
                self.executable_opts += [
                    f'-kokkos on t {self.num_cpus_per_task} g {self.num_gpus_per_node}',
                    '-suffix kk',
                    '-package kokkos newton on neigh half',
                ]
                utils.log(f'executable_opts set to {self.executable_opts}')


@rfm.simple_test
class EESSI_LAMMPS_rhodo(EESSI_LAMMPS_base):
    sourcesdir = 'src/rhodo'
    readonly_files = ["data.rhodo"]
    executable = 'lmp -in in.rhodo'

    @deferrable
    def check_number_neighbors(self):
        '''Assert that the test calulated the right number of neighbours'''
        regex = r'^Total # of neighbors = (?P<neigh>\S+)'
        n_neigh = sn.extractsingle(regex, self.stdout, 'neigh', int)

        return sn.assert_eq(n_neigh, 12028093)

    @performance_function('ns/day')
    def perf(self):
        regex = r'^Performance: (?P<perf>[.0-9]+) ns/day,'
        return sn.extractsingle(regex, self.stdout, 'perf', float)

    @sanity_function
    def assert_sanity(self):
        '''Check all sanity criteria'''
        return sn.all([
            self.assert_lammps_openmp_treads(),
            self.assert_lammps_processor_grid(),
            self.assert_run(),
            self.check_number_neighbors(),
        ])

    @run_after('setup')
    def set_executable_opts(self):
        """Set executable opts based on device_type parameter"""
        num_default = 0  # If this test already has executable opts, they must have come from the command line
        hooks.check_custom_executable_opts(self, num_default=num_default)
        if not self.has_custom_executable_opts:
            # should also check if the lammps is installed with kokkos.
            # Because this exutable opt is only for that case.
            if self.device_type == "gpu":
                self.executable_opts += [
                    f'-kokkos on t {self.num_cpus_per_task} g {self.num_gpus_per_node}',
                    '-suffix kk',
                    '-package kokkos newton on neigh half',
                ]
                utils.log(f'executable_opts set to {self.executable_opts}')