"""
This module tests the binary 'gmx_mpi' in available modules containing substring 'GROMACS'.
Test input files are taken from https://www.hecbiosim.ac.uk/access-hpc/benchmarks,
    as defined in the hpctestlib.
"""

import shlex

import reframe as rfm
import reframe.core.runtime as rt
from reframe.utility import OrderedSet

from hpctestlib.sciapps.gromacs.benchmarks import gromacs_check
from eessi_utils import hooks
from eessi_utils import utils


def my_find_modules(substr):
    """Return all modules in the current system that contain ``substr`` in their name."""
    if not isinstance(substr, str):
        raise TypeError("'substr' argument must be a string")

    ms = rt.runtime().modules_system
    modules = OrderedSet(ms.available_modules(substr))
    for m in modules:
        yield m


@rfm.simple_test
class GROMACS_EESSI(gromacs_check):

    scale = parameter([
        ('singlenode', 1),
        ('n_small', 2),
        ('n_medium', 8),
        ('n_large', 16)])

    module_name = parameter(my_find_modules('GROMACS'))
    valid_prog_environs = ['default']
    valid_systems = []

    time_limit = '30m'

    @run_after('init')
    def filter_tests(self):
        """filter valid_systems, unless specified with --setvar valid_systems=<comma-separated-list>"""
        if not self.valid_systems:
            is_cuda_module = utils.is_cuda_required_module(self.module_name)
            valid_systems = ''

            if is_cuda_module and self.nb_impl == 'gpu':
                # CUDA modules and when using a GPU for non-bonded interactions require partitions with 'gpu' feature
                valid_systems = '+gpu'

            elif self.nb_impl == 'cpu':
                # Non-bonded interactions on the CPU require partitions with 'cpu' feature
                # Note: making 'cpu' an explicit feature allows e.g. skipping CPU-based tests on GPU partitions
                valid_systems = '+cpu'

            elif not is_cuda_module and self.nb_impl == 'gpu':
                # Invalid combination: a module without GPU support cannot compute non-bonded interactions on GPU
                valid_systems = ''

            if valid_systems:
                self.valid_systems = [valid_systems]

        # skip this test if the module is not among a list of manually specified modules
        # modules can be specified with --setvar modules=<comma-separated-list>
        if self.modules and self.module_name not in self.modules:
            self.valid_systems = []

        self.modules = [self.module_name]

    @run_after('init')
    def set_test_scale(self):
        """Add tag based on scale used"""
        scale_variant, self.num_nodes = self.scale
        self.tags.add(scale_variant)

    @run_after('init')
    def set_test_purpose(self):
        """Set correct tags for monitoring & CI"""
        # Run all tests from the testlib for monitoring
        self.tags.add('monitoring')
        # Select one test for CI
        if self.benchmark_info[0] == 'HECBioSim/hEGFRDimer':
            self.tags.add('CI')

    @run_after('init')
    def check_custom_executable_opts(self):
        """"
        hpctestlib adds the following:
            self.executable_opts += ['-nb', self.nb_impl, '-s benchmark.tpr']
        if executable_opts are set via the cmd line with --setvar executable_opts=<x>,
            we will not add any extra executable_opts
        """
        # normalize options
        self.executable_opts = shlex.split(' '.join(self.executable_opts))
        self.has_custom_executable_opts = False
        if len(self.executable_opts) > 4:
            self.has_custom_executable_opts = True

    @run_after('setup')
    def set_num_tasks(self):
        """
        Assign default values for num_tasks, num_tasks_per_node, num_cpus_per_task, and num_gpus_per_node,
            based on current partition's num_cpus and gpus
        when running nb_impl on CPU, we request one task per CPU
        when running nb_impl on GPU, we request one task per GPU
        """
        hooks.assign_one_task_per_compute_unit(test=self, compute_unit=self.nb_impl)

    @run_after('setup')
    def set_omp_num_threads(self):
        """
        Set number of OpenMP threads
        Set both OMP_NUM_THREADS and -ntomp explicitly to avoid conflicting values
        """
        if self.has_custom_executable_opts:
            if '-ntomp' in self.executable_opts:
                omp_num_threads = self.executable_opts[self.executable_opts.index('-ntomp') + 1]
        else:
            omp_num_threads = self.num_cpus_per_task
            self.executable_opts += ['-dlb yes', f'-ntomp {omp_num_threads}', '-npme -1']

        self.env_vars['OMP_NUM_THREADS'] = omp_num_threads
