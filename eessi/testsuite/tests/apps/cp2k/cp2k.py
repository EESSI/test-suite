import os

import reframe as rfm
from reframe.core.builtins import parameter, run_after, performance_function, sanity_function
import reframe.utility.sanity as sn

from eessi.testsuite import hooks
from eessi.testsuite.constants import SCALES, TAGS, COMPUTE_UNIT, DEVICE_TYPES, CPU
from eessi.testsuite.utils import find_modules, log


@rfm.simple_test
class EESSI_CP2K(rfm.RunOnlyRegressionTest):

    benchmark_info = parameter([
        # (bench_name, energy_ref, energy_tol)
        ('QS/H2O-32', -550.5055, 1e-4),
        ('QS/H2O-128', -2202.1791, 1e-4),
        ('QS/H2O-512', -8808.1439, 1e-4),
    ], fmt=lambda x: x[0], loggable=True)
    module_name = parameter(find_modules('CP2K'))
    scale = parameter(SCALES.keys())

    executable = 'cp2k.popt'
    time_limit = '1h'
    valid_systems = ['*']
    valid_prog_environs = ['default']

    @run_after('init')
    def prepare_test(self):
        self.bench_name, self.energy_ref, self.energy_tol = self.benchmark_info
        self.descr = f'EESSI_CP2K {self.bench_name} benchmark'
        self.prerun_cmds = [
            f'cp {os.path.join(os.path.dirname(__file__), "input", self.bench_name)}.inp ./'
        ]
        self.executable_opts += ['-i', f'{os.path.basename(self.bench_name)}.inp']

    @sanity_function
    def assert_energy(self):
        energy = sn.extractsingle(
            r"^\s*ENERGY\| Total FORCE_EVAL.+?:\s*(?P<energy>.+)\n",
            self.stdout, 'energy', float, item=-1)
        energy_diff = sn.abs(energy - self.energy_ref)
        return sn.all([
            sn.assert_found(r'PROGRAM STOPPED IN', self.stdout),
            sn.assert_lt(energy_diff, self.energy_tol)
        ])

    @performance_function('s', perf_key='time')
    def time(self):
        return sn.extractsingle(r'^ CP2K(\s+[\d\.]+){4}\s+(?P<time>\S+)', self.stdout, 'time', float)

    @run_after('init')
    def run_after_init(self):
        """Hooks to run after the init phase"""

        # Filter on which scales are supported by the partitions defined in the ReFrame configuration
        hooks.filter_supported_scales(self)

        # Make sure that GPU tests run in partitions that support running on a GPU,
        # and that CPU-only tests run in partitions that support running CPU-only.
        # Also support setting valid_systems on the cmd line.
        hooks.filter_valid_systems_by_device_type(self, required_device_type=DEVICE_TYPES[CPU])

        # Support selecting modules on the cmd line.
        hooks.set_modules(self)

        # Support selecting scales on the cmd line via tags.
        hooks.set_tag_scale(self)

    @run_after('init')
    def set_tag_ci(self):
        """Set tag CI on smallest benchmark, so it can be selected on the cmd line via --tag CI"""
        if self.benchmark_info[0] == 'QS/H2O-32':
            self.tags.add(TAGS['CI'])
            log(f'tags set to {self.tags}')

    @run_after('setup')
    def run_after_setup(self):
        """Hooks to run after the setup phase"""

        # Calculate default requested resources based on the scale:
        # 1 task per CPU for CPU-only tests, 1 task per GPU for GPU tests.
        # Also support setting the resources on the cmd line.
        hooks.assign_tasks_per_compute_unit(test=self, compute_unit=COMPUTE_UNIT[CPU])

    @run_after('setup')
    def set_omp_num_threads(self):
        """
        Set default number of OpenMP threads equal to number of CPUs per task,
        unless OMP_NUM_THREADS is already set
        """
        self.env_vars['OMP_NUM_THREADS'] = os.getenv('OMP_NUM_THREADS', self.num_cpus_per_task)
        log(f'env_vars set to {self.env_vars}')
