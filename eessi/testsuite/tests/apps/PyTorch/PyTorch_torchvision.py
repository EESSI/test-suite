from itertools import chain

import reframe as rfm
import reframe.utility.sanity as sn
# Added only to make the linter happy
from reframe.core.builtins import parameter, variable, run_after, sanity_function, performance_function

from eessi.testsuite import hooks
from eessi.testsuite.constants import SCALES, TAGS, DEVICE_TYPES, COMPUTE_UNIT, CPU, NUMA_NODE, GPU
from eessi.testsuite.utils import find_modules


class EESSI_PyTorch_torchvision(rfm.RunOnlyRegressionTest):
    nn_model = parameter(['vgg16', 'resnet50', 'resnet152', 'densenet121', 'mobilenet_v3_large'])
    scale = parameter(SCALES.keys())
    parallel_strategy = parameter([None, 'ddp'])
    compute_device = variable(str)
    # Both torchvision and PyTorch-bundle modules have everything needed to run this test
    module_name = parameter(chain(find_modules('torchvision'), find_modules('PyTorch-bundle')))

    descr = 'Benchmark that runs a selected torchvision model on synthetic data'

    executable = 'python'

    valid_prog_environs = ['default']
    valid_systems = ['*']

    time_limit = '30m'

    @run_after('init')
    def prepare_test(self):

        # Set nn_model as executable option
        self.executable_opts = ['pytorch_synthetic_benchmark.py --model %s' % self.nn_model]

        # If not a GPU run, disable CUDA
        if self.compute_device != DEVICE_TYPES[GPU]:
            self.executable_opts += ['--no-cuda']

    @run_after('init')
    def apply_init_hooks(self):
        # Filter on which scales are supported by the partitions defined in the ReFrame configuration
        hooks.filter_supported_scales(self)

        # Make sure that GPU tests run in partitions that support running on a GPU,
        # and that CPU-only tests run in partitions that support running CPU-only.
        # Also support setting valid_systems on the cmd line.
        hooks.filter_valid_systems_by_device_type(self, required_device_type=self.compute_device)

        # Support selecting modules on the cmd line.
        hooks.set_modules(self)

        # Support selecting scales on the cmd line via tags.
        hooks.set_tag_scale(self)

    @run_after('init')
    def set_tag_ci(self):
        if self.nn_model == 'resnet50':
            self.tags.add(TAGS['CI'])

    @run_after('setup')
    def apply_setup_hooks(self):
        if self.compute_device == DEVICE_TYPES[GPU]:
            hooks.assign_tasks_per_compute_unit(test=self, compute_unit=COMPUTE_UNIT[GPU])
        else:
            # Hybrid code, for which launching one task per NUMA_NODE is typically the most efficient
            hooks.assign_tasks_per_compute_unit(test=self, compute_unit=COMPUTE_UNIT[NUMA_NODE])

        # This is a hybrid test, binding is important for performance
        hooks.set_compact_process_binding(self)

        # Set OMP_NUM_THREADS based on the number of cores per task
        self.env_vars["OMP_NUM_THREADS"] = self.num_cpus_per_task

    @run_after('setup')
    def set_ddp_options(self):
        # Set environment variables for PyTorch DDP
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
        # Set parallelization strategy when using more than one process
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
        '''Training througput per CPU'''
        if self.compute_device == DEVICE_TYPES[CPU]:
            return sn.extractsingle(r'Img/sec per CPU:\s+(?P<perf_per_cpu>\S+)', self.stdout, 'perf_per_cpu', float)
        else:
            return sn.extractsingle(r'Img/sec per GPU:\s+(?P<perf_per_gpu>\S+)', self.stdout, 'perf_per_gpu', float)


@rfm.simple_test
class EESSI_PyTorch_torchvision_CPU(EESSI_PyTorch_torchvision):
    compute_device = DEVICE_TYPES[CPU]


@rfm.simple_test
class EESSI_PyTorch_torchvision_GPU(EESSI_PyTorch_torchvision):
    compute_device = DEVICE_TYPES[GPU]
    precision = parameter(['default', 'mixed'])

    @run_after('init')
    def prepare_gpu_test(self):
        # Set precision
        if self.precision == 'mixed':
            self.executable_opts += ['--use-amp']
