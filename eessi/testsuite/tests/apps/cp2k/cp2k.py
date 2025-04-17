import reframe as rfm
from reframe.core.builtins import parameter, run_after, performance_function, sanity_function
import reframe.utility.sanity as sn

from eessi.testsuite.constants import SCALES, COMPUTE_UNITS, DEVICE_TYPES
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.utils import find_modules


@rfm.simple_test
class EESSI_CP2K(rfm.RunOnlyRegressionTest, EESSI_Mixin):

    benchmark_info = parameter([
        # (bench_name, energy_ref, energy_tol)
        ('QS/H2O-32', -550.5055, 1e-4),
        ('QS/H2O-128', -2202.1791, 1e-4),
        ('QS/H2O-512', -8808.1439, 1e-4),
    ], fmt=lambda x: x[0], loggable=True)

    module_name = parameter(find_modules('CP2K'))
    scale = parameter(SCALES.keys())

    executable = 'cp2k.popt'
    time_limit = '2h'
    device_type = DEVICE_TYPES.CPU
    compute_unit = COMPUTE_UNITS.CPU
    bench_name_ci = 'QS/H2O-32'  # set CI on smallest benchmark
    readonly_files = ['QS']

    def required_mem_per_node(self):
        mems = {
            'QS/H2O-32': {'intercept': 0.5, 'slope': 0.15},
            'QS/H2O-128': {'intercept': 5, 'slope': 0.15},
            'QS/H2O-512': {'intercept': 34, 'slope': 0.20},
        }
        mem = mems[self.bench_name]
        return (self.num_tasks_per_node * mem['slope'] + mem['intercept']) * 1024

    @run_after('init')
    def set_bench_name(self):
        self.bench_name, self.energy_ref, self.energy_tol = self.benchmark_info
        self.descr = f'EESSI_CP2K {self.bench_name} benchmark'

    @run_after('setup')
    def prepare_test(self):
        self.executable_opts += ['-i', f'{self.bench_name}.inp']

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

    @run_after('setup')
    def skip_tests(self):
        """Skip tests that are not suited for the requested resources"""

        # Skip QS/H2O-512 benchmark if not enough cores requested
        min_cores = 16
        self.skip_if(self.bench_name == 'QS/H2O-512' and self.num_tasks < min_cores,
                     f'Skipping benchmark {self.bench_name}: less than {min_cores} cores requested ({self.num_tasks})')

        # Skip QS/H2O-512 benchmark if too many nodes requested
        max_nodes = 8
        self.skip_if(self.bench_name == 'QS/H2O-512' and self.num_nodes > max_nodes,
                     f'Skipping benchmark {self.bench_name}: more than {max_nodes} nodes requested ({self.num_nodes})')
