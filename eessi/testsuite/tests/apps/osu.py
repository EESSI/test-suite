"""
This module tests the binary 'osu' in available modules containing substring 'OSU-Micro-Benchmarks'. The basic
application class is taken from the hpctestlib to which extra features are added.

Note: OSU-Micro-Benchmarks CUDA module binaries must be linked to stubs so that it at the least finds libcuda.so.1 on
non-GPU nodes. Otherwise those tests will FAIL.
"""
import reframe as rfm
from reframe.core.builtins import parameter, run_after
from reframe.utility import reframe

from hpctestlib.microbenchmarks.mpi.osu import osu_benchmark

from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES, INVALID_SYSTEM, SCALES
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.utils import find_modules, log


def filter_scales_pt2pt_cpu():
    """
    Filtering function for filtering scales for the pt2pt OSU test on CPUs
    returns all scales with either 2 cores, 1 full node, or 2 full nodes
    """
    return [
        k for (k, v) in SCALES.items()
        if v['num_nodes'] * v.get('num_cpus_per_node', 0) == 2
        or (v['num_nodes'] == 2 and v.get('node_part', 0) == 1)
        or (v['num_nodes'] == 1 and v.get('node_part', 0) == 1)
    ]


def filter_scales_pt2pt_gpu():
    """
    Filtering function for filtering scales for the pt2pt OSU test on GPUs
    returns all scales with either a partial node, 1 full node, or 2 full nodes
    """
    return [
        k for (k, v) in SCALES.items()
        if (v['num_nodes'] == 1 and v.get('node_part', 0) > 1)
        or (v['num_nodes'] == 2 and v.get('node_part', 0) == 1)
        or (v['num_nodes'] == 1 and v.get('node_part', 0) == 1)
    ]


def filter_scales_coll():
    """
    Filtering function for filtering scales for the collective OSU test
    returns all scales with at least 2 cores
    """
    return [
        k for (k, v) in SCALES.items()
        if (v['num_nodes'] * v.get('num_cpus_per_node', 1) > 1)
        or (v.get('node_part', 0) > 0)
    ]


class EESSI_OSU_Base(osu_benchmark):
    """ base class for OSU tests """
    time_limit = '30m'
    module_name = parameter(find_modules('OSU-Micro-Benchmarks'))

    # reset num_tasks_per_node from the hpctestlib: we handle it ourselves
    num_tasks_per_node = None
    readonly_files = ['']

    # Set num_warmup_iters to 5 to reduce execution time, especially on slower interconnects
    num_warmup_iters = 5
    # Set num_iters to 10 to reduce execution time, especially on slower interconnects
    num_iters = 10

    def required_mem_per_node(self):
        return self.num_tasks_per_node * 1024

    @run_after('init')
    def filter_scales_2gpus(self):
        """Filter out scales with < 2 GPUs if running on GPUs"""
        if (
            self.device_type == DEVICE_TYPES.GPU
            and SCALES[self.scale]['num_nodes'] == 1
            and SCALES[self.scale].get('num_gpus_per_node', 2) < 2
        ):
            self.valid_systems = [INVALID_SYSTEM]
            log(f'valid_systems set to {self.valid_systems} for scale {self.scale} and device_type {self.device_type}')

    @run_after('init')
    def set_device_buffers(self):
        """
        device_buffers is inherited from the hpctestlib class and adds options to the launcher
        commands in a @run_before('setup') hook if not equal to 'cpu'.
        Therefore, we must set device_buffers *before* the @run_before('setup') hooks.
        """
        if self.device_type == DEVICE_TYPES.GPU:
            self.device_buffers = 'cuda'
        else:
            self.device_buffers = 'cpu'

    @run_after('init')
    def set_tags(self):
        """ Setting custom tags """
        self.bench_name = self.benchmark_info[0]
        self.tags.add(self.bench_name.split('.')[-1])


class EESSI_OSU_pt2pt_Base(EESSI_OSU_Base):
    ''' point-to-point OSU test base class '''
    compute_unit = COMPUTE_UNITS.NODE

    @run_after('init')
    def filter_benchmark_pt2pt(self):
        """ Filter out all non-mpi.pt2pt benchmarks """
        if not self.benchmark_info[0].startswith('mpi.pt2pt'):
            self.valid_systems = [INVALID_SYSTEM]

    @run_after('init')
    def select_ci(self):
        " Select the CI variants "
        if (self.bench_name in ['mpi.pt2pt.osu_latency', 'mpi.pt2pt.osu_bw']):
            self.bench_name_ci = self.bench_name

    @run_after('init')
    def set_num_tasks_per_compute_unit(self):
        """ Setting number of tasks per compute unit and cpus per task. This sets num_cpus_per_task
        for 1 node and 2 node options where the request is for full nodes."""
        if SCALES.get(self.scale).get('num_nodes') == 1:
            self.num_tasks_per_compute_unit = 2

    @run_after('setup')
    def adjust_executable_opts(self):
        """The option "D D" is only meant for Devices if and not for CPU tests.
        This option is added by hpctestlib in a @run_before('setup') to all pt2pt tests which is not required.
        Therefore we must override it *after* the 'setup' phase
        """
        if self.device_type == DEVICE_TYPES.CPU:
            self.executable_opts = [x for x in self.executable_opts if x != 'D']


@rfm.simple_test
class EESSI_OSU_pt2pt_CPU(EESSI_OSU_pt2pt_Base, EESSI_Mixin):
    ''' point-to-point OSU test on CPUs'''
    scale = parameter(filter_scales_pt2pt_cpu())
    device_type = DEVICE_TYPES.CPU


@rfm.simple_test
class EESSI_OSU_pt2pt_GPU(EESSI_OSU_pt2pt_Base, EESSI_Mixin):
    ''' point-to-point OSU test on GPUs'''
    scale = parameter(filter_scales_pt2pt_gpu())
    device_type = DEVICE_TYPES.GPU
    always_request_gpus = True

    @run_after('setup')
    def skip_test_gpus(self):
        num_gpus = self.num_gpus_per_node * self.num_nodes
        if self.scale not in ['1_node', '2_nodes']:
            # On a partial node allocation, run this test only if exactly 2 GPUs are allocated
            self.skip_if(
                num_gpus != 2,
                f"Skipping test : {num_gpus} GPU(s) available for this test case, need exactly 2"
            )
        elif self.scale == '1_node':
            # Make sure there are at least 2 GPUs
            self.skip_if(num_gpus < 2, "Skipping GPU test : only 1 GPU available for this test case")


@rfm.simple_test
class EESSI_OSU_coll(EESSI_OSU_Base, EESSI_Mixin):
    ''' collective OSU test '''
    scale = parameter(filter_scales_coll())
    device_type = parameter([DEVICE_TYPES.CPU, DEVICE_TYPES.GPU])

    @run_after('init')
    def filter_benchmark_coll(self):
        """ Filter out all non-mpi.collective benchmarks """
        if not self.benchmark_info[0].startswith('mpi.collective'):
            self.valid_systems = [INVALID_SYSTEM]

    @run_after('init')
    def select_ci(self):
        " Select the CI variants "
        if (self.bench_name in ['mpi.collective.osu_allreduce', 'mpi.collective.osu_alltoall']):
            self.bench_name_ci = self.bench_name

    @run_after('init')
    def set_compute_unit(self):
        """
        Set the compute unit to which tasks will be assigned:
        one task per core for CPU runs, and one task per GPU for GPU runs.
        """
        device_to_compute_unit = {
            DEVICE_TYPES.CPU: COMPUTE_UNITS.CPU,
            DEVICE_TYPES.GPU: COMPUTE_UNITS.GPU,
        }
        self.compute_unit = device_to_compute_unit.get(self.device_type)

    @run_after('setup')
    def skip_test_1gpu(self):
        if self.device_type == DEVICE_TYPES.GPU:
            num_gpus = self.num_gpus_per_node * self.num_nodes
            self.skip_if(num_gpus < 2, "Skipping GPU test : only 1 GPU available for this test case")
