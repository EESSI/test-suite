"""
This module tests the binary 05_BackwardFacingStep in available modules containing substring 'waLBerla'.
The test is taken from the existing tutorials within the walberla repository:
https://github.com/lssfau/walberla/tree/master/apps/tutorials/lbm

License information can be found here:
https://github.com/lssfau/walberla/blob/master/COPYING.txt

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


def filter_scales_1M():
    """
    Filtering function for filtering scales for the waLBerla test
    returns all scales with at least half a node.
    """
    return [
        k for (k, v) in SCALES.items()
        if ((v['num_nodes'] <= 2) and (v.get('node_part', 0) != 0)) or (v.get('num_cpus_per_node', 0)
                                                                        * v.get('num_nodes', 0) > 1)
    ]


@rfm.simple_test
class EESSI_WALBERLA_BACKWARD_FACING_STEP(rfm.RunOnlyRegressionTest, EESSI_Mixin):
    """
    This is the main walberla class for the backward facing step test. The test consists of steps that modify the input
    file from the precompiled walberla tutorials binary. These are run as pre-run commands and the main test with the
    executable `05_BackwardFacingStep` is measured for performance.
    """
#    ldc_64M = fixture(EESSI_OPENFOAM_base, scope='partition')
    executable = '05_BackwardFacingStep'
    executable_opts = ['05_BackwardFacingStep.prm']
    time_limit = '120m'
    readonly_files = ['']
    device_type = parameter([DEVICE_TYPES.CPU])
    module_name = parameter(find_modules('waLBerla'))
    valid_systems = ['*']
    scale = parameter(filter_scales_1M())

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
    def check_core_count(self):
        # The walberla backward facing step test case can run on a max of 384 cores and a minimum of 8 cores to run
        # within reasonable time.
        if self.num_tasks > 384:
            self.skip(msg="The maximum number of cores that the strong scaling can hold for this test is 384. Launch on"
                      "a scale with a smaller core count.")
        elif self.num_tasks < 8:
            self.skip(msg="The minimum number of MPI tasks required for this test is 8 to run within reasonable time."
                      "Launch of scale with larger core count")

    @run_before('run')
    def prepare_environment(self):
        # fullpath = os.path.join(self.ldc_64M.stagedir, 'fixedTol')
        self.prerun_cmds = [
            'cp -r ${EBROOTWALBERLA}/build/apps/tutorials/lbm .',
            'chmod -R u+w lbm',
            'cd lbm',
            f"sed -i -r 's/(blocks\\s*)<\\s*1,\\s*1,\\s*1\\s*>/\\1< {self.num_tasks} , 1, 1 >/g'"
            " 05_BackwardFacingStep.prm",
            f"sed -i -r 's/(cellsPerBlock\\s*)<\\s*6000,\\s*100,\\s*1\\s*>/\\1< {int(6000 / self.num_tasks) + 1} "
            ", 100, 1 >/g' 05_BackwardFacingStep.prm",
            "sed -i -r 's/(timesteps\\s*)10000000/\\1300000/g' 05_BackwardFacingStep.prm "]

    @deferrable
    def check_files(self):
        ''' Check for all the log files present. '''
        return (sn.path_isfile("./lbm/vtk_05_BackwardFacingStep/fluid_field.pvd")
                and sn.path_isfile("./lbm/vtk_05_BackwardFacingStep/flag_field.pvd"))

    @deferrable
    def assert_completion(self):
        n_time_steps = sn.count(sn.extractall(
            'DataSet timestep="(?P<timestep>[0-9]+)"', "./lbm/vtk_05_BackwardFacingStep/fluid_field.pvd",
            tag='timestep'))
        return (sn.assert_found("END LOGGING -", self.stdout,
                                msg="The run did not finish, the logger did not indicate completion. Check for errors.")
                and sn.assert_eq(n_time_steps, 15))

    @performance_function('s/timestep')
    def perf(self):
        perftimes = sn.extractall(r'[INFO\s*].*\((?P<perf>\S+)\s+sec\)\[(?P<numsteps>.*)\]', self.stdout,
                                  tag=['perf', 'numsteps'], conv=float)
        seconds_per_timestep = perftimes[-1][0] / perftimes[-1][1]
        return seconds_per_timestep

    @sanity_function
    def assert_sanity(self):
        '''Check all sanity criteria'''
        return sn.all([
            self.check_files(),
            self.assert_completion(),
        ])
