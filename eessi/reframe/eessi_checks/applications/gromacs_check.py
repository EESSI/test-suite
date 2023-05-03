"""
This module tests the binary 'gmx_mpi' in available modules containing substring 'GROMACS'.
Test input files are taken from https://www.hecbiosim.ac.uk/access-hpc/benchmarks,
    as defined in the hpctestlib.
"""

import reframe as rfm

from hpctestlib.sciapps.gromacs.benchmarks import gromacs_check
from eessi_utils import hooks, utils


@rfm.simple_test
class GROMACS_EESSI(gromacs_check):
    scale = parameter(utils.SCALES)
    valid_prog_environs = ['default']
    valid_systems = []
    time_limit = '30m'
    module_name = parameter(utils.find_modules('GROMACS'))

    @run_after('init')
    def run_after_init(self):
        """hooks to run after the init phase"""
        hooks.filter_tests_by_device_type(self, required_device_type=self.nb_impl)
        hooks.set_modules(self)
        hooks.set_tag_scale(self)

    @run_after('init')
    def set_tag_ci(self):
        if self.benchmark_info[0] == 'HECBioSim/hEGFRDimer':
            self.tags.add('CI')

    @run_after('init')
    def set_executable_opts(self):
        """
        Add extra executable_opts, unless specified via --setvar executable_opts=<x>
        """
        num_default = 4  # normalized number of executable opts added by parent class (gromacs_check)
        hooks.check_custom_executable_opts(self, num_default=num_default)
        if not self.has_custom_executable_opts:
            self.executable_opts += ['-dlb', 'yes', '-npme', '-1']

    @run_after('setup')
    def run_after_setup(self):
        """hooks to run after the setup phase"""
        hooks.assign_one_task_per_compute_unit(test=self, compute_unit=self.nb_impl)

    @run_after('setup')
    def set_omp_num_threads(self):
        """
        Set number of OpenMP threads
        Set both OMP_NUM_THREADS and -ntomp explicitly to avoid conflicting values
        """
        if '-ntomp' in self.executable_opts:
            omp_num_threads = self.executable_opts[self.executable_opts.index('-ntomp') + 1]
        else:
            omp_num_threads = self.num_cpus_per_task
            self.executable_opts += ['-ntomp', str(omp_num_threads)]

        self.env_vars['OMP_NUM_THREADS'] = omp_num_threads
