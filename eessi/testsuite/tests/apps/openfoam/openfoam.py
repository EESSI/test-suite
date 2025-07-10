"""
This module tests the binary icofoam in available modules containing substring 'OPENFOAM'.
This line of tests target binaries from OpenFOAM from https://www.openfoam.com/ .
The test is taken from the ExaFOAM project:
https://develop.openfoam.com/committees/hpc/-/tree/develop/incompressible/icoFoam/cavity3D

License information can be found here:
https://develop.openfoam.com/committees/hpc/-/blob/develop/incompressible/icoFoam/cavity3D/README.md#copyright

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
# added only to make the linter happy
from reframe.core.builtins import deferrable, parameter, run_after, run_before, sanity_function, performance_function
import reframe.utility.sanity as sn
from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES, SCALES
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.utils import find_modules


def filter_scales_8M():
    """
    Filtering function for filtering scales for the OpenFOAM 8M mesh test
    returns all scales with at least half a node.
    """
    return [
        k for (k, v) in SCALES.items()
        if (v['num_nodes'] >= 1) and (0 < v.get('node_part', 0) <= 2)
    ]


@rfm.simple_test
class EESSI_OPENFOAM_LID_DRIVEN_CAVITY(rfm.RunOnlyRegressionTest, EESSI_Mixin):
    """
    This is the main OPENFOAM class for the Lid-driven cavity test. The test consists of many steps which are run as
    pre-run commands and the main test with the executable `icoFoam` is measured for performance.
    """
#    ldc_8M = fixture(EESSI_OPENFOAM_base, scope='partition')
    executable = 'icoFoam'
    executable_opts = ['-parallel', '2>&1', '|', 'tee log.icofoam']
    time_limit = '60m'
    readonly_files = ['']
    device_type = parameter([DEVICE_TYPES.CPU])
    module_name = parameter(find_modules('OpenFOAM/v', name_only=False))
    valid_systems = ['*']
    scale = parameter(filter_scales_8M())

    @run_after('init')
    def set_compute_unit(self):
        """
        Set the compute unit to which tasks will be assigned:
        one task per CPU core for CPU runs.
        """
        if self.device_type == DEVICE_TYPES.CPU:
            self.compute_unit = COMPUTE_UNITS.CPU
        else:
            msg = f"No mapping of device type {self.device_type} to a COMPUTE_UNITS was specified in this test"
            raise NotImplementedError(msg)

    def required_mem_per_node(self):
        return self.num_tasks_per_node * 1700

    @run_after('setup')
    def check_launcher_options(self):
        # We had to get the launcher command and prepend this to the prerun steps (func prepare_environment) because:
        # 1. A typical OpenFOAM job would contain multiple mpirun steps working on the same stage directory.
        # 2. We had trouble using ReFrame fixtures to separate these over multiple jobs, because we couldn't get it to
        #    work together with the mixin class.
        if (self.job.launcher.command(self.job)[0] == 'mpirun'):
            self.launcher_command = self.job.launcher.command(self.job)
            self.launcher_command[-1] = str(self.num_tasks_per_node * self.num_nodes)
        elif (self.job.launcher.command(self.job)[0] == 'srun'):
            self.launcher_command = self.job.launcher.command(self.job)
        else:
            self.skip(msg="The chosen launcher for this test is different from mpirun or srun which means that the"
                      "test will definitely fail, therefore skipping this test.")

    @run_after('setup')
    def check_minimum_cores(self):
        # The 8M test case requires minimally 8 cores to run within reasonable time.
        if self.num_tasks < 8:
            self.skip(msg="The minimum number of cores required by this test is 8. Launch on a scale with higher core"
                      "count.")

    @run_before('run')
    def prepare_environment(self):
        # fullpath = os.path.join(self.ldc_8M.stagedir, 'fixedTol')
        self.prerun_cmds = [
            'cd ./cavity3D/8M/fixedTol',
            'source $FOAM_BASH',
            f"foamDictionary -entry numberOfSubdomains -set {self.num_tasks_per_node * self.num_nodes} "
            "system/decomposeParDict",
            'blockMesh 2>&1 | tee log.blockMesh',
            f"{' '.join(self.launcher_command)} redistributePar -decompose -parallel 2>&1 | tee log.decompose",
            f"{' '.join(self.launcher_command)} renumberMesh -parallel -overwrite 2>&1 | tee log.renumberMesh"]

    @deferrable
    def check_files(self):
        ''' Check for all the log files present. '''
        return (sn.path_isfile("./cavity3D/8M/fixedTol/log.blockMesh")
                and sn.path_isfile("./cavity3D/8M/fixedTol/log.decompose")
                and sn.path_isfile("./cavity3D/8M/fixedTol/log.renumberMesh")
                and sn.path_isfile("./cavity3D/8M/fixedTol/log.icofoam"))

    @deferrable
    def assert_completion(self):
        n_ranks = sn.count(sn.extractall(
            '^Processor (?P<rank>[0-9]+)', "./cavity3D/8M/fixedTol/log.decompose", tag='rank'))
        return (sn.assert_found("^Writing polyMesh with 0 cellZones", "./cavity3D/8M/fixedTol/log.blockMesh",
                                msg="BlockMesh failure.")
                and sn.assert_found(r"\s+nCells: 8000000", "./cavity3D/8M/fixedTol/log.blockMesh",
                                    msg="BlockMesh failure.")
                and sn.assert_eq(n_ranks, self.num_tasks)
                and sn.assert_found(r"^Finalising parallel run", "./cavity3D/8M/fixedTol/log.renumberMesh",
                                    msg="Did not reach the end of the renumberMesh run. RenumberMesh failure.")
                and sn.assert_found(r"^Time = 0.0075", "./cavity3D/8M/fixedTol/log.icofoam",
                                    msg="Did not reach the last time step. IcoFoam failure.")
                and sn.assert_found(r"^Finalising parallel run", "./cavity3D/8M/fixedTol/log.icofoam",
                                    msg="Did not reach the end of the icofoam run. IcoFoam failure."))

    @deferrable
    def assert_convergence(self):
        cumulative_cont_err = sn.extractall(r'cumulative = (?P<cont>\S+)', "./cavity3D/8M/fixedTol/log.icofoam",
                                            'cont', float)
        abs_cumulative_cont_err = sn.abs(cumulative_cont_err[-1])
        return sn.assert_le(abs_cumulative_cont_err, 1e-15,
                            msg="The cumulative continuity errors are high. Try varying pressure solver.")

    @performance_function('s/timestep')
    def perf(self):
        perftimes = sn.extractall(r'ClockTime = (?P<perf>\S+)', "./cavity3D/8M/fixedTol/log.icofoam", 'perf',
                                  float)
        seconds_per_timestep = perftimes[-1] / 15.0
        return seconds_per_timestep

    @sanity_function
    def assert_sanity(self):
        '''Check all sanity criteria'''
        return sn.all([
            self.check_files(),
            self.assert_completion(),
            self.assert_convergence(),
        ])
