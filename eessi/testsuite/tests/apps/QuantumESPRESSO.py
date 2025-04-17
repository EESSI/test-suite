"""
This module tests the binary 'pw.x' in available modules containing substring 'QuantumESPRESSO'.
Test input files are defined in the ReFrame test library,
see https://github.com/reframe-hpc/reframe/blob/develop/hpctestlib/sciapps/qespresso/benchmarks.py

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
from hpctestlib.sciapps.qespresso.benchmarks import QEspressoPWCheck
from reframe.core.builtins import parameter, run_after

from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.utils import find_modules


@rfm.simple_test
class EESSI_QuantumESPRESSO_PW(QEspressoPWCheck, EESSI_Mixin):
    time_limit = '30m'
    module_name = parameter(find_modules('QuantumESPRESSO'))
    # For now, QE is built for CPU targets only
    device_type = parameter([DEVICE_TYPES.CPU])
    readonly_files = ['']

    def required_mem_per_node(self):
        return (self.num_tasks_per_node * 0.9 + 4) * 1024

    @run_after('init')
    def set_ci(self):
        """Set tag CI on smallest benchmark, so it can be selected on the cmd line via --tag CI"""
        min_ecut = min(QEspressoPWCheck.ecut.values)
        min_nbnd = min(QEspressoPWCheck.nbnd.values)
        if self.ecut == min_ecut and self.nbnd == min_nbnd:
            self.bench_name = self.bench_name_ci = 'bench_ci'

    @run_after('init')
    def set_increased_walltime(self):
        """Increase the amount of time for the largest benchmark, so it can complete successfully."""
        max_ecut = max(QEspressoPWCheck.ecut.values)
        max_nbnd = max(QEspressoPWCheck.nbnd.values)
        if self.ecut == max_ecut and self.nbnd == max_nbnd:
            self.time_limit = '60m'

    @run_after('init')
    def set_compute_unit(self):
        """
        Set the compute unit to which tasks will be assigned:
        one task per CPU core for CPU runs, and one task per GPU for GPU runs.
        """
        device_to_compute_unit = {
            DEVICE_TYPES.CPU: COMPUTE_UNITS.CPU,
            DEVICE_TYPES.GPU: COMPUTE_UNITS.GPU,
        }
        self.compute_unit = device_to_compute_unit.get(self.device_type)
