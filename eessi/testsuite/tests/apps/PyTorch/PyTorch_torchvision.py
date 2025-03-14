from itertools import chain

import reframe as rfm
import reframe.utility.sanity as sn
from reframe.core.builtins import parameter, run_after, sanity_function, performance_function

from eessi.testsuite.constants import DEVICE_TYPES, COMPUTE_UNITS
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.utils import find_modules


class EESSI_PyTorch_torchvision(rfm.RunOnlyRegressionTest, EESSI_Mixin):
    descr = 'Benchmark that runs a selected torchvision model on synthetic data'

    nn_model = parameter(['vgg16', 'resnet50', 'resnet152', 'densenet121', 'mobilenet_v3_large'])
    bench_name_ci = 'resnet50'
    parallel_strategy = parameter([None, 'ddp'])
    # Both torchvision and PyTorch-bundle modules have everything needed to run this test
    module_name = parameter(chain(find_modules('torchvision'), find_modules('PyTorch-bundle')))
    executable = 'python'
    time_limit = '30m'
    readonly_files = ['get_free_socket.py', 'pytorch_synthetic_benchmark.py']

    def required_mem_per_node(self):
        return self.num_tasks_per_node * 1024

    @run_after('init')
    def prepare_test(self):
        # Set nn_model as executable option
        self.executable_opts = ['pytorch_synthetic_benchmark.py --model %s' % self.nn_model]
        self.bench_name = self.nn_model

        # If not a GPU run, disable CUDA
        if self.device_type != DEVICE_TYPES.GPU:
            self.executable_opts += ['--no-cuda']

    @run_after('setup')
    def set_ddp_options(self):
        "Set environment variables for PyTorch DDP"
        if self.parallel_strategy == 'ddp':
            # Set additional options required by DDP
            self.executable_opts += ["--master-port $(python get_free_socket.py)"]
            self.executable_opts += ["--master-address $(hostname --fqdn)"]
            self.executable_opts += ["--world-size %s" % self.num_tasks]

    @run_after('setup')
    def filter_invalid_parameter_combinations(self):
        # We cannot detect this situation before the setup phase, because it requires self.num_tasks.
        # Thus, the core count of the node needs to be known, which is only the case after the setup phase.
        msg = "Skipping test: parallel strategy is 'None',"
        msg += f" but requested process count is larger than one ({self.num_tasks})."
        self.skip_if(self.num_tasks > 1 and self.parallel_strategy is None, msg)
        msg = f"Skipping test: parallel strategy is {self.parallel_strategy},"
        msg += " but only one process is requested."
        self.skip_if(self.num_tasks == 1 and self.parallel_strategy is not None, msg)

    @run_after('setup')
    def pass_parallel_strategy(self):
        "Set parallelization strategy when using more than one process"
        if self.num_tasks != 1:
            self.executable_opts += ['--use-%s' % self.parallel_strategy]

    @sanity_function
    def assert_num_ranks(self):
        '''Assert that the number of reported CPUs/GPUs used is correct'''
        return sn.assert_found(r'Total img/sec on %s .PU\(s\):.*' % self.num_tasks, self.stdout)

    @performance_function('img/sec')
    def total_throughput(self):
        '''Total training throughput, aggregated over all CPUs/GPUs'''
        return sn.extractsingle(r'Total img/sec on [0-9]+ .PU\(s\):\s+(?P<perf>\S+)', self.stdout, 'perf', float)

    @performance_function('img/sec')
    def througput_per_CPU(self):
        '''Training througput per device type'''
        if self.device_type == DEVICE_TYPES.CPU:
            return sn.extractsingle(r'Img/sec per CPU:\s+(?P<perf_per_cpu>\S+)', self.stdout, 'perf_per_cpu', float)
        else:
            return sn.extractsingle(r'Img/sec per GPU:\s+(?P<perf_per_gpu>\S+)', self.stdout, 'perf_per_gpu', float)


@rfm.simple_test
class EESSI_PyTorch_torchvision_CPU(EESSI_PyTorch_torchvision):
    device_type = DEVICE_TYPES.CPU
    compute_unit = COMPUTE_UNITS.NUMA_NODE


@rfm.simple_test
class EESSI_PyTorch_torchvision_GPU(EESSI_PyTorch_torchvision):
    device_type = DEVICE_TYPES.GPU
    compute_unit = COMPUTE_UNITS.GPU
    precision = parameter(['default', 'mixed'])

    @run_after('init')
    def prepare_gpu_test(self):
        # Set precision
        if self.precision == 'mixed':
            self.executable_opts += ['--use-amp']
