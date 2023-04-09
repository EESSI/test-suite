"""
This module tests the binary 'gmx_mpi' in available modules containing substring 'GROMACS'.
Test input files are taken from https://www.hecbiosim.ac.uk/access-hpc/benchmarks,
    as defined in the hpctestlib.
"""

import reframe as rfm

from hpctestlib.sciapps.gromacs.benchmarks import gromacs_check
from eessi_utils import hooks, utils
from eessi_utils.utils import SCALES


@rfm.simple_test
class GROMACS_EESSI(gromacs_check):
    scale = parameter(SCALES.keys())
    valid_prog_environs = ['default']
    valid_systems = []
    time_limit = '30m'
    module_name = parameter(utils.my_find_modules('GROMACS'))

    @run_after('init')
    def run_after_init(self):
        """hooks to run after the init phase"""
        hooks.filter_tests_by_device_type(self, device_type=self.nb_impl)
        hooks.set_modules(self)
        hooks.set_scale(self)

    @run_after('init')
    def set_tag_ci(self):
        """Set tag CI on first benchmark"""
        if self.benchmark_info[0] == 'HECBioSim/hEGFRDimer':
            self.tags.add('CI')

    @run_after('setup')
    def run_after_setup(self):
        """hooks to run after the setup phase"""
        hooks.assign_one_task_per_compute_unit(test=self, compute_unit=self.nb_impl)

    @run_after('setup')
    def set_omp_num_threads(self):
        """Set number of OpenMP threads"""
        omp_num_threads = self.num_cpus_per_task
        # set both OMP_NUM_THREADS and -ntomp explicitly to avoid conflicting values
        self.executable_opts += ['-dlb yes', f'-ntomp {omp_num_threads}', '-npme -1']
        self.env_vars['OMP_NUM_THREADS'] = f'{omp_num_threads}'
