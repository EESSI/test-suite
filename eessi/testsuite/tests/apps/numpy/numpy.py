"""
This test was adapted from https://github.com/vscentrum/vsc-test-suite/tree/main/tests/apps/python,
originally created by Michele Pugno (UAntwerpen)

Tested matrix operations with NumPy:
- dot product
- singular value decompostion (SVD)
- cholesky decomposition
- eigen decomposition
- inversion
"""
import reframe as rfm
import reframe.utility.sanity as sn
from reframe.core.backends import getlauncher
from reframe.core.builtins import parameter, run_after, run_before, sanity_function

from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES, SCALES
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.utils import find_modules


@rfm.simple_test
class EESSI_NumPy(rfm.RunOnlyRegressionTest, EESSI_Mixin):
    descr = 'Test matrix operations with NumPy'
    executable = 'python3'
    executable_opts = ['np_ops.py']
    time_limit = '20m'
    readonly_files = ['np_ops.py']
    module_name = parameter(find_modules('SciPy-bundle'))
    device_type = DEVICE_TYPES.CPU
    compute_unit = COMPUTE_UNITS.NODE
    scale = parameter([
        k for (k, v) in SCALES.items()
        if v['num_nodes'] == 1
    ])

    def required_mem_per_node(self):
        return self.num_cpus_per_task * 100 + 600

    @run_after('setup')
    def set_launcher(self):
        """Select local launcher"""
        self.job.launcher = getlauncher('local')()

    @sanity_function
    def assert_numpy_found(self):
        """Assert that NumPy is found"""
        return sn.assert_found(r'NumPy version:\s+\S+', self.stdout)

    @run_before('performance')
    def set_perf_vars(self):
        """Set performance variables"""
        self.perf_variables.update({
            'dot': sn.make_performance_function(sn.extractsingle(
                r'^Dotted two \S* matrices in\s+(?P<dot>\S+)\s+s',
                self.stdout, 'dot', float), 's'),
            'svd': sn.make_performance_function(sn.extractsingle(
                r'^SVD of a \S* matrix in\s+(?P<svd>\S+)\s+s',
                self.stdout, 'svd', float), 's'),
            'cholesky': sn.make_performance_function(sn.extractsingle(
                r'^Cholesky decomposition of a \S* matrix in\s+(?P<cholesky>\S+)\s+s',
                self.stdout, 'cholesky', float), 's'),
            'eigendec': sn.make_performance_function(sn.extractsingle(
                r'^Eigendecomposition of a \S* matrix in\s+(?P<eigendec>\S+)\s+s',
                self.stdout, 'eigendec', float), 's'),
            'inv': sn.make_performance_function(sn.extractsingle(
                r'^Inversion of a \S* matrix in\s+(?P<inv>\S+)\s+s',
                self.stdout, 'inv', float), 's'),
        })
