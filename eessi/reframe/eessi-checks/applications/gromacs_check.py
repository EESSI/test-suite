# Copyright 2016-2021 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# ReFrame Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause

import reframe as rfm
import reframe.core.runtime as rt
from reframe.utility import OrderedSet

from hpctestlib.sciapps.gromacs.benchmarks import gromacs_check
import eessi_utils.hooks as hooks
import eessi_utils.utils as utils


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
    valid_prog_environs = ['builtin']
    valid_systems = []

    time_limit = '30m'

    @run_after('init')
    def filter_tests(self):
        # filter valid_systems, unless specified with --setvar valid_systems=<comma-separated-list>
        if not self.valid_systems:
            cuda_module = utils.is_cuda_required_module(self.module_name)
            valid_systems = ''

            # CUDA modules and when using a GPU for non-bonded interactions require partitions with 'gpu' feature
            # non-CUDA modules require partitions with 'cpu' feature
            if cuda_module:
                valid_systems = '+gpu'
                if self.nb_impl == 'cpu':
                    valid_systems += ' +cpu'
            else:
                valid_systems += '+cpu'
                if self.nb_impl == 'gpu':
                    valid_systems = ''  # impossible combination

            if valid_systems:
                self.valid_systems = [valid_systems]

        # filter out this test if the module is not among a list of manually specified modules
        # modules can be specified with --setvar modules=<comma-separated-list>
        if self.modules and self.module_name not in self.modules:
            self.valid_systems = []

        self.modules = [self.module_name]

    @run_after('init')
    def set_test_scale(self):
        scale_variant, self.num_nodes = self.scale
        self.tags.add(scale_variant)

    # Set correct tags for monitoring & CI
    @run_after('init')
    def set_test_purpose(self):
        # Run all tests from the testlib for monitoring
        self.tags.add('monitoring')
        # Select one test for CI
        if self.benchmark_info[0] == 'HECBioSim/hEGFRDimer':
            self.tags.add('CI')

    # Skip testing for when nb_impl=gpu and this is not a GPU node
    @run_after('setup')
    def skip_nb_impl_gpu_on_cpu_nodes(self):
        self.skip_if(
            (self.nb_impl == 'gpu' and not utils.is_gpu_present(self)),
            "Skipping test variant with non-bonded interactions on GPUs, "
            f"as this partition ({self.current_partition.name}) does not have GPU nodes"
        )

    # Sckip testing when nb_impl=gpu and this is not a GPU build of GROMACS
    @run_after('setup')
    def skip_nb_impl_gpu_on_non_cuda_builds(self):
        self.skip_if(
            (self.nb_impl == 'gpu' and not utils.is_cuda_required(self)),
            "Skipping test variant with non-bonded interactions on GPUs, "
            f"as this module ({self.module_name}) was not build with GPU support"
        )

    # Skip testing GPU-based modules on CPU-based nodes
    @run_after('setup')
    def skip_gpu_test_on_cpu_nodes(self):
        hooks.skip_gpu_test_on_cpu_nodes(self)

    # Assign num_tasks, num_tasks_per_node and num_cpus_per_task automatically
    # based on current partition's num_cpus and gpus
    # Only when running nb_impl on GPU do we want one task per GPU
    @run_after('setup')
    def set_num_tasks(self):
        if self.nb_impl == 'gpu':
            hooks.assign_one_task_per_gpu(test=self, num_nodes=self.num_nodes)
        else:
            hooks.assign_one_task_per_cpu(test=self, num_nodes=self.num_nodes)

    @run_after('setup')
    def set_omp_num_threads(self):
        omp_num_threads = self.num_cpus_per_task
        self.executable_opts += ['-dlb yes', f'-ntomp {omp_num_threads}', '-npme -1']
        self.variables['OMP_NUM_THREADS'] = f'{omp_num_threads}'
