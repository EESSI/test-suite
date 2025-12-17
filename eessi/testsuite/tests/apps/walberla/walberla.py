"""
This module tests the binary 05_BackwardFacingStep in available modules containing substring 'waLBerla'.
The test is taken from the existing tutorials within the walberla repository:
https://github.com/lssfau/walberla/tree/master/apps/tutorials/lbm

License information can be found here:
https://github.com/lssfau/walberla/blob/master/COPYING.txt

"""

import reframe as rfm
# added only to make the linter happy
from reframe.core.builtins import deferrable, parameter, run_after, run_before, sanity_function, performance_function
import reframe.utility.sanity as sn
from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES, SCALES
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.utils import find_modules


def filter_scales():
    """
    Filtering function for filtering scales for the waLBerla test returns all scales from 8 cores to 2 nodes. This is
    because this case is testing strong scaling and the number of cells per MPI process become too less typically once
    it crosses 2 nodes. Further filtering is done within the test based on MPI tasks. The code is capable of running on
    1 to 4 cores as well but it will take about 1 hour to run on a single core.
    """
    return [
        k for (k, v) in SCALES.items()
        if ((v['num_nodes'] <= 2) and (v.get('node_part', 0) != 0)) or (v.get('num_cpus_per_node', 0) > 4)
    ]


@rfm.simple_test
class EESSI_WALBERLA_BACKWARD_FACING_STEP(rfm.RunOnlyRegressionTest, EESSI_Mixin):
    """
    This is the main walberla class for the backward facing step test. The test consists of steps that modify the input
    file from the precompiled walberla tutorials binary. These are run as pre-run commands and the main test with the
    executable `05_BackwardFacingStep` is measured for performance.
    The code will run on one core but will take about an hour to run therefore this test is implemented to execute on
    at least 8 cores and at most 384 cores.
    """
    executable = '05_BackwardFacingStep'
    executable_opts = ['05_BackwardFacingStep.prm']
    time_limit = '30m'
    readonly_files = ['']
    device_type = parameter([DEVICE_TYPES.CPU])
    module_name = parameter(find_modules('waLBerla'))
    valid_systems = ['*']
    scale = parameter(filter_scales())

    @run_after('init')
    def set_compute_unit(self):
        """
        This test is a CPU only test.
        Set the compute unit to which tasks will be assigned:
        one task per CPU core for CPU runs.
        """
        if self.device_type == DEVICE_TYPES.CPU:
            self.compute_unit = COMPUTE_UNITS.CPU
        else:
            msg = f"No mapping of device type {self.device_type} to a COMPUTE_UNITS was specified in this test"
            raise NotImplementedError(msg)

    def required_mem_per_node(self):
        return (400 + self.num_tasks_per_node * 300)

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
        """
        Function:
        1. Copying the built binary from the tutorial section of the relevant waLBerla module.
        2. Modifying the input prm file to adjust for number of MPI tasks (blocks) and cells per block keeping the
        domain size same.
        3. Adjusting timesteps since the run need not be that long as in the original input prm file.
        """
        # The sed commands below are just editing the input file 05_BackwardFacingStep.prm and only the first parameter
        # within blocks and cells per block. The whole idea is to keep the number of cells around the value of 6000 in
        # the x direction. Since this is a cartesian system, the default is assigned is one process per block. This is
        # as per walberla source code and the runs would crash if there is a mismatch between total number of blocks and
        # number of MPI ranks.
        # Note: It is also possible to edit the y component or the second parameter of the blocks and cellsPerBlock BUT
        # this would vary the viscosity of the of the fluid with the number of MPI processes because this is hardcoded
        # within the compiled tutorial source code to use this length to calculate the Reynolds number within the
        # channel. For this the source code needs to be modified to include the number of MPI processes so that the
        # problem at hand does not change which would in turn need recompilation, therefore only x parameter is varied.
        # The last sed command limits the timesteps to 300000 instead of 10000000 because the quasi steady state is
        # already reached.
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
        ''' Checking for completion string within stdout and number of output timesteps within vtk. '''
        n_time_steps = sn.count(sn.extractall(
            'DataSet timestep="(?P<timestep>[0-9]+)"', "./lbm/vtk_05_BackwardFacingStep/fluid_field.pvd",
            tag='timestep'))
        return (sn.assert_found("END LOGGING -", self.stdout,
                                msg="The run did not finish, the logger did not indicate completion. Check for errors.")
                and sn.assert_eq(n_time_steps, 15))

    @performance_function('s/timestep')
    def perf(self):
        ''' Collecting performance timings within the log and computing average performance time per step. '''
        perftimes = sn.extractall(r'[INFO\s*].*\((?P<perf>\S+)\s+sec\)\[(?P<numsteps>.*)\]', self.stdout,
                                  tag=['perf', 'numsteps'], conv=float)
        seconds_per_timestep = perftimes[-1][0] / perftimes[-1][1]
        return seconds_per_timestep

    @sanity_function
    def assert_sanity(self):
        ''' Check all sanity criteria. '''
        return sn.all([
            self.check_files(),
            self.assert_completion(),
        ])
