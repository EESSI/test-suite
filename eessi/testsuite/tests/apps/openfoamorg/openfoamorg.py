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


def filter_scales_64M():
    """
    Filtering function for filtering scales for the OpenFOAM 64M mesh test
    returns all scales with at least half a node.
    """
    return [
        k for (k, v) in SCALES.items()
        if (v['num_nodes'] >= 4) and (0 < v.get('node_part', 0) <= 2)
    ]


def filter_scales_8M():
    """
    Filtering function for filtering scales for the OpenFOAM 8M mesh test
    returns all scales with at least half a node.
    """
    return [
        k for (k, v) in SCALES.items()
        if (v['num_nodes'] >= 1) and (0 < v.get('node_part', 0) <= 2)
    ]


def filter_scales_1M():
    """
    Filtering function for filtering scales for the OpenFOAM 1M mesh test
    returns all scales with at least half a node.
    """
    return [
        k for (k, v) in SCALES.items()
        if ((v['num_nodes'] <= 2) and (v.get('node_part', 0) != 0)) or (v.get('num_cpus_per_node', 0)
                                                                        * v.get('num_nodes', 0) > 1)
    ]

class EESSI_OPENFOAMORG_LID_DRIVEN_CAVITY_BASE(rfm.RunOnlyRegressionTest):
    """
    This is the Base OPENFOAM(ORG version) class for the Lid-driven cavity test. The test consists of many steps which
    are run as pre-run commands and the main test with the executable `icoFoam` is measured for performance.
    """
    executable = 'icoFoam'
    executable_opts = ['-parallel', '2>&1', '|', 'tee log.icofoam']
    readonly_files = ['']
    device_type = parameter([DEVICE_TYPES.CPU])
    module_info = parameter(find_modules(r'OpenFOAM/\d', name_only=False))
    valid_systems = ['*']

    # Some test specific variables.
    path_to_wd = ""
    nCells = 0
    endTime = 0

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

    @run_before('run')
    def prepare_environment(self):
        self.prerun_cmds = [
            f"cd {self.path_to_wd}",
            'source $FOAM_BASH',
            f"foamDictionary -entry numberOfSubdomains -set {self.num_tasks_per_node * self.num_nodes} "
            "system/decomposeParDict",
            'blockMesh 2>&1 | tee log.blockMesh',
            "decomposePar 2>&1 | tee log.decompose",
            f"{' '.join(self.launcher_command)} renumberMesh -parallel -overwrite 2>&1 | tee log.renumberMesh"]

    @deferrable
    def check_files(self):
        ''' Check for all the log files present. '''
        return (sn.path_isfile(self.path_to_wd + "/log.blockMesh")
                and sn.path_isfile(self.path_to_wd + "/log.decompose")
                and sn.path_isfile(self.path_to_wd + "/log.renumberMesh")
                and sn.path_isfile(self.path_to_wd + "/log.icofoam"))

    @deferrable
    def assert_completion(self):
        n_ranks = sn.count(sn.extractall(
            '^Processor (?P<rank>[0-9]+)', self.path_to_wd + "/log.decompose", tag='rank'))
        return (sn.assert_found("^Writing polyMesh", self.path_to_wd + "/log.blockMesh",
                                msg="BlockMesh failure.")
                and sn.assert_found(rf"\s+nCells: {self.nCells}", self.path_to_wd + "/log.blockMesh",
                                    msg="BlockMesh failure.")
                and sn.assert_eq(n_ranks, self.num_tasks)
                and sn.assert_found(r"^Finalising parallel run", self.path_to_wd + "/log.renumberMesh",
                                    msg="Did not reach the end of the renumberMesh run. RenumberMesh failure.")
                and sn.assert_found(rf"^Time = {self.endTime}s", self.path_to_wd + "/log.icofoam",
                                    msg="Did not reach the last time step. IcoFoam failure.")
                and sn.assert_found(r"^Finalising parallel run", self.path_to_wd + "/log.icofoam",
                                    msg="Did not reach the end of the icofoam run. IcoFoam failure."))

    @deferrable
    def assert_convergence(self):
        cumulative_cont_err = sn.extractall(r'cumulative = (?P<cont>\S+)', self.path_to_wd + "/log.icofoam",
                                            'cont', float)
        abs_cumulative_cont_err = sn.abs(cumulative_cont_err[-1])
        return sn.assert_le(abs_cumulative_cont_err, 1e-15,
                            msg="The cumulative continuity errors are high. Try varying pressure solver.")

    @performance_function('s/timestep')
    def perf(self):
        perftimes = sn.extractall(r'ClockTime = (?P<perf>\S+)', self.path_to_wd + "/log.icofoam", 'perf',
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

@rfm.simple_test
class EESSI_OPENFOAMORG_LID_DRIVEN_CAVITY_1M(EESSI_OPENFOAMORG_LID_DRIVEN_CAVITY_BASE, EESSI_Mixin):
    """
    This is the main OPENFOAM class for the Lid-driven cavity test. The test consists of many steps which are run as
    pre-run commands and the main test with the executable `icoFoam` is measured for performance.
    """
    scale = parameter(filter_scales_1M())
    time_limit = '60m'
    is_ci_test = True

    def required_mem_per_node(self):
        return self.num_tasks_per_node * 1700

    @run_after('init')
    def update_test_specific_variables(self):
        """ This function is defined to update all test specific variables such as path to working directory, number of
        cells or the mesh size, end time, etc."""
        self.path_to_wd ="./cavity3D/1M/fixedTol"
        self.nCells = 1000000
        self.endTime = 0.015

    @run_after('setup')
    def check_maximum_cores(self):
        """
        The 1M test case should maximally run on 128 cores to run properly. Otherwise communication overhead
        becomes too high. The number of cells per core is 1e6/128 = 7812.5, which is already a pretty low number.
        This is a limitation of the test case, not of OpenFOAM.
        """
        if self.num_tasks > 128:
            self.skip(msg="The maximum number of cores this test can run on is 128. Launch on a scale with lower core"
                      "count.")

@rfm.simple_test
class EESSI_OPENFOAMORG_LID_DRIVEN_CAVITY_8M(EESSI_OPENFOAMORG_LID_DRIVEN_CAVITY_BASE, EESSI_Mixin):
    """
    This is the main OPENFOAM class for the Lid-driven cavity test. The test consists of many steps which are run as
    pre-run commands and the main test with the executable `icoFoam` is measured for performance.
    """
    scale = parameter(filter_scales_8M())
    time_limit = '60m'

    def required_mem_per_node(self):
        return self.num_tasks_per_node * 1700

    @run_after('init')
    def update_test_specific_variables(self):
        """ This function is defined to update all test specific variables such as path to working directory, number of
        cells or the mesh size, end time, etc."""
        self.path_to_wd ="./cavity3D/8M/fixedTol"
        self.nCells = 8000000
        self.endTime = 0.0075

    @run_after('setup')
    def check_minimum_cores(self):
        """The 8M test case requires minimally 8 cores to run within reasonable time."""
        if self.num_tasks < 8:
            self.skip(msg="The minimum number of cores required by this test is 8. Launch on a scale with higher core"
                      "count.")

@rfm.simple_test
class EESSI_OPENFOAMORG_LID_DRIVEN_CAVITY_64M(EESSI_OPENFOAMORG_LID_DRIVEN_CAVITY_BASE, EESSI_Mixin):
    """
    This is the main OPENFOAM class for the Lid-driven cavity test. The test consists of many steps which are run as
    pre-run commands and the main test with the executable `icoFoam` is measured for performance.
    """
    scale = parameter(filter_scales_64M())
    time_limit = '120m'

    def required_mem_per_node(self):
        return self.num_tasks_per_node * 1700

    @run_after('init')
    def update_test_specific_variables(self):
        """ This function is defined to update all test specific variables such as path to working directory, number of
        cells or the mesh size, end time, etc."""
        self.path_to_wd ="./cavity3D/64M/fixedTol"
        self.nCells = 64000000
        self.endTime = 0.00375

    @run_after('setup')
    def check_minimum_cores(self):
        """The 64M test case requires minimally 512 cores to run within reasonable time."""
        if self.num_tasks < 512:
            self.skip(msg="The minimum number of cores required by this test is 512. Launch on a scale with higher core"
                      "count.")
