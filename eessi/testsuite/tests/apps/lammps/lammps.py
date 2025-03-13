"""
This module tests the binary 'lmp' in available modules containing substring 'LAMMPS'.
The tests come from the lammps github repository (https://github.com/lammps/lammps/)
"""

import reframe as rfm
from reframe.core.builtins import deferrable, parameter, performance_function, run_after, sanity_function
import reframe.utility.sanity as sn

from eessi.testsuite import utils
from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES, TAGS
from eessi.testsuite.eessi_mixin import EESSI_Mixin


class EESSI_LAMMPS_base(rfm.RunOnlyRegressionTest):
    time_limit = '30m'
    device_type = parameter([DEVICE_TYPES.CPU, DEVICE_TYPES.GPU])

    # Parameterize over all modules that start with LAMMPS
    module_name = parameter(utils.find_modules('LAMMPS'))

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


@rfm.simple_test
class EESSI_LAMMPS_lj(EESSI_LAMMPS_base, EESSI_Mixin):
    tags = {TAGS.CI}

    sourcesdir = 'src/lj'
    readonly_files = ['in.lj']
    executable = 'lmp -in in.lj'

    @deferrable
    def check_number_neighbors(self):
        '''Assert that the test calulated the right number of neighbours'''
        regex = r'Neighbor list builds = (?P<neigh>\S+)'
        n_neigh = sn.extractsingle(regex, self.stdout, 'neigh', int)
        return sn.assert_eq(n_neigh, 5)

    @deferrable
    def assert_energy(self):
        '''Asert that the calculated energy at timestep 100 is with the margin of error'''
        regex = r'^\s+100\s+[-+]?[.0-9]+\s+[-+]?[.0-9]+\s+0\s+(?P<energy>[-+]?[.0-9]+)'
        energy = sn.extractsingle(regex, self.stdout, 'energy', float)
        energy_diff = sn.abs(energy - (-4.6223613))
        return sn.assert_lt(energy_diff, 1e-4)

    @performance_function('timesteps/s')
    def perf(self):
        regex = r'^Performance: [.0-9]+ tau/day, (?P<perf>[.0-9]+) timesteps/s'
        return sn.extractsingle(regex, self.stdout, 'perf', float)

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

    @run_after('setup')
    def set_executable_opts(self):
        """Set executable opts based on device_type parameter"""
        # should also check if LAMMPS is installed with kokkos.
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


@rfm.simple_test
class EESSI_LAMMPS_rhodo(EESSI_LAMMPS_base, EESSI_Mixin):
    sourcesdir = 'src/rhodo'
    executable = 'lmp -in in.rhodo'
    readonly_files = ['data.rhodo', 'in.rhodo']

    @deferrable
    def check_number_neighbors(self):
        '''Assert that the test calulated the right number of neighbours'''
        regex = r'Neighbor list builds = (?P<neigh>\S+)'
        n_neigh = sn.extractsingle(regex, self.stdout, 'neigh', int)
        return sn.assert_eq(n_neigh, 11)

    @deferrable
    def assert_energy(self):
        '''Asert that the calculated energy at timestep 100 is with the margin of error'''
        regex = r'^-+\s+Step\s+100\s+-+\s+CPU\s=\s+[.0-9]+\s+\(sec\)\s+-+\nTotEng\s+=\s+(?P<energy>[-+]?[.0-9]+)'
        energy = sn.extractsingle(regex, self.stdout, 'energy', float)
        energy_diff = sn.abs(energy - (-25290.7300))
        return sn.assert_lt(energy_diff, 1e-1)

    @performance_function('timesteps/s')
    def perf(self):
        regex = r'^Performance: [.0-9]+ ns/day, [.0-9]+ hours/ns, (?P<perf>[.0-9]+) timesteps/s'
        return sn.extractsingle(regex, self.stdout, 'perf', float)

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
