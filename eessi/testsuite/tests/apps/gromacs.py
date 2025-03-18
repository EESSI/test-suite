"""
This module tests the binary 'gmx_mpi' in available modules containing substring 'GROMACS'.
Test input files are taken from https://www.hecbiosim.ac.uk/access-hpc/benchmarks,
as defined in the ReFrame test library,
see https://github.com/reframe-hpc/reframe/blob/develop/hpctestlib/sciapps/gromacs/benchmarks.py

ReFrame terminology:

"pipeline stages":
https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#pipeline-hooks

"test parameter": a list of values, which will generate different test variants.
https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#reframe.core.builtins.parameter

"test variant": a version of a test with a specific value for each test parameter
https://reframe-hpc.readthedocs.io/en/stable/regression_test_api.html#test-variants

"concrete test cases": all test combinations that will actually run:
- test variants
- valid system:partition+programming environment combinations
https://reframe-hpc.readthedocs.io/en/stable/tutorial_deps.html#listing-dependencies

Tests can be filtered by name, tag, programming environment, system, partition, or maintainer,
see https://reframe-hpc.readthedocs.io/en/stable/manpage.html#test-filtering

Hooks acting on all possible test combinations (before filtering) are called after the 'init' stage.
Hooks acting on concrete test cases (after filtering) are called after the 'setup' stage.

See also https://reframe-hpc.readthedocs.io/en/stable/pipeline.html
"""

import reframe as rfm
from reframe.core.builtins import parameter, run_after  # added only to make the linter happy

from hpctestlib.sciapps.gromacs.benchmarks import gromacs_check

from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES, SCALES
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.utils import find_modules, log


class EESSI_GROMACS_base(gromacs_check):
    @run_after('init')
    def set_device_type(self):
        self.device_type = self.nb_impl


@rfm.simple_test
class EESSI_GROMACS(EESSI_GROMACS_base, EESSI_Mixin):
    scale = parameter(SCALES.keys())
    time_limit = '30m'
    module_name = parameter(find_modules('GROMACS'))
    bench_name_ci = 'HECBioSim/Crambin'
    # input files are downloaded
    readonly_files = ['']
    # executable_opts in addition to those set by the hpctestlib
    executable_opts = ['-dlb', 'yes', '-npme', '-1']

    def required_mem_per_node(self):
        return self.num_tasks_per_node * 1024

    def __init__(self):
        # self.device_type must be set before the @run_after('init') hooks of the EESSI_Mixin class
        self.device_type = self.nb_impl

    @run_after('init')
    def set_compute_unit(self):
        """
        Set the compute unit to which tasks will be assigned:
        one task per CPU core for CPU runs, and one task per GPU for GPU runs.
        """
        if self.device_type == DEVICE_TYPES.CPU:
            self.compute_unit = COMPUTE_UNITS.CPU
        elif self.device_type == DEVICE_TYPES.GPU:
            self.compute_unit = COMPUTE_UNITS.GPU
        else:
            msg = f"No mapping of device type {self.device_type} to a COMPUTE_UNITS was specified in this test"
            raise NotImplementedError(msg)

    @run_after('setup')
    def set_omp_num_threads(self):
        """
        Set number of OpenMP threads.
        Set both OMP_NUM_THREADS and -ntomp explicitly to avoid conflicting values.
        Set default number of OpenMP threads equal to number of CPUs per task.
        Also support setting OpenMP threads on the cmd line via custom executable option '-ntomp'.
        """
        omp_num_threads = self.num_cpus_per_task
        self.executable_opts += ['-ntomp', str(omp_num_threads)]
        log(f'executable_opts set to {self.executable_opts}')

        self.env_vars['OMP_NUM_THREADS'] = omp_num_threads
        log(f'env_vars set to {self.env_vars}')
