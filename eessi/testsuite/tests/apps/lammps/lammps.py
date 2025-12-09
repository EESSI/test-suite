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

from statistics import mean

# Todo should find a way to set the tag CI when the module of LAMMPS is not a fat-build
# The only way to easily check it without running lmp is to check the easyconfig in software dir


def split(list, size):
    return [list[i:i + size] for i in range(0, len(list), size)]


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

    @deferrable
    def assert_run_steps(self):
        '''Assert that the test calulated the right number of neighbours'''
        regex = r'^Loop time of (?P<perf>[.0-9]+) on [0-9]+ procs for (?P<steps>\S+) steps with [0-9]+ atoms'
        n_steps = sn.extractsingle(regex, self.stdout, 'steps', int)
        return sn.assert_eq(n_steps, 10000)

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
        '''Asert that the calculated energy at timestep 100 is with the margin of error'''
        regex = r'^\s+[.0-9]+\s+[.0-9]+\s+[.0-9]+\s+[.0-9]+$'
        values = sn.extractall(regex, 'nden_profile.out')
        return self.compute_ndenprof(values, 30, 10, 100)


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


@rfm.simple_test
class EESSI_LAMMPS_ALL_balance_staggered_global(EESSI_LAMMPS_base, EESSI_Mixin):
    tags = {TAGS.CI}

    sourcesdir = 'src/ALL'
    executable = 'lmp -in in.balance.staggered.global'
    readonly_files = ['in.balance.staggered.global']

    @deferrable
    def check_number_neighbors(self):
        '''Assert that the test calulated the right number of neighbours'''
        regex = r'Neighbor list builds = (?P<neigh>\S+)'
        n_neigh = sn.extractsingle(regex, self.stdout, 'neigh', int)
        n_neigh_diff = sn.abs(n_neigh - 2529)
        return sn.assert_lt(n_neigh_diff, 1100)

    @performance_function('timesteps/s')
    def perf(self):
        regex = r'^Performance: [.0-9]+ tau/day, (?P<perf>[.0-9]+) timesteps/s, [.0-9]+ Matom-step/s'
        return sn.extractsingle(regex, self.stdout, 'perf', float)

    @sanity_function
    def assert_sanity(self):
        '''Check all sanity criteria'''
        return sn.all([
            self.assert_lammps_openmp_treads(),
            self.assert_lammps_processor_grid(),
            self.assert_run_steps(),
            self.assert_inbalence(),
        ])

    @run_after('init')
    def check_if_ALL_included(self):
        """Only run this test when LAMMPS has the ALL package."""
        # Can determine if this is included based on the versionsuffix.
        # At this moment the package is not upstream available and has the versionsuffix ALL.
        # See https://github.com/multixscale/dev.eessi.io-lammps-plugin-obmd/pull/7
        if 'ALL' in self.module_name:
            #  print(self)
            return
        else:
            self.skip(msg="This test is not going to pass since this LAMMPS package does not include ALL."
                          "test will definitely fail, therefore skipping this test.")

    @deferrable
    def assert_inbalence(self):
        '''Asert that the calculated energy at timestep 100 is with the margin of error'''
        regex = (
            r'^\s+10000\s+50\s+[-+]?[.0-9]+\s+[-+]?[.0-9]+\s+0\s+[-+]?[.0-9]+\s+'
            r'[-+]?[.0-9]+\s+0\s+[-+]?[.0-9]+\s+[-+]?[.0-9]+\s+[-+]?[.0-9]+\s+'
            r'[-+]?[.0-9]+\s+[-+]?[0-9]+\s+(?P<var14>[-+]?[.0-9]+)\s'
        )
        inbalence = sn.extractsingle(regex, self.stdout, 'var14', float)
        return sn.assert_lt(inbalence, 1.1)

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


@rfm.simple_test
class EESSI_LAMMPS_ALL_OBMD_simulation_staggered_global(EESSI_LAMMPS_base, EESSI_Mixin):
    tags = {TAGS.CI}

    sourcesdir = 'src/ALL+OBMD'
    executable = 'lmp -in in.simulation.staggered.global'
    readonly_files = ['in.simulation.staggered.global']

    @performance_function('timesteps/s')
    def perf(self):
        regex = r'^Performance: [.0-9]+ tau/day, (?P<perf>[.0-9]+) timesteps/s, [.0-9]+ Matom-step/s'
        return sn.extractsingle(regex, self.stdout, 'perf', float)

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
        """Only run this test when LAMMPS has the ALL package."""
        # Can determine if this is included based on the versionsuffix.
        # At this moment the package is not upstream available and has the versionsuffix ALL.
        # See https://github.com/multixscale/dev.eessi.io-lammps-plugin-obmd/pull/7
        if 'ALL' in self.module_name and 'OBMD' in self.module_name:
            # print(self)
            return
        else:
            self.skip(msg="This test is not going to pass since this LAMMPS package does not include ALL."
                          "test will definitely fail, therefore skipping this test.")

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


@rfm.simple_test
class EESSI_LAMMPS_OBMD_simmulation(EESSI_LAMMPS_base, EESSI_Mixin):
    tags = {TAGS.CI}

    sourcesdir = 'src/OBMD'
    readonly_files = ['input.py', 'dpd_8map_obmd.data']

    prerun_cmds = ['python input.py']

    executable = 'lmp -in in.simulation'

    @performance_function('timesteps/s')
    def perf(self):
        regex = r'^Performance: [.0-9]+ tau/day, (?P<perf>[.0-9]+) timesteps/s, [.0-9]+ Matom-step/s'
        return sn.extractsingle(regex, self.stdout, 'perf', float)

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
