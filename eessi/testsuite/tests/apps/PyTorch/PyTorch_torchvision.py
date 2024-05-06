import reframe as rfm
import reframe.utility.sanity as sn

from eessi.testsuite import hooks
from eessi.testsuite.constants import SCALES, TAGS, DEVICE_TYPES, COMPUTE_UNIT, CPU, NUMA_NODE, GPU, INVALID_SYSTEM
from eessi.testsuite.utils import find_modules, log

class EESSI_PyTorch_torchvision(rfm.RunOnlyRegressionTest):
    nn_model = parameter(['vgg16', 'resnet50', 'resnet152', 'densenet121', 'mobilenet_v3_large'])
    ### SHOULD BE DETERMINED BY SCALE
    #n_processes = parameter([1, 2, 4, 8, 16])
    scale = parameter(SCALES.keys())
    # Not sure how we would ensure the horovod module is _also_ loaded...
    # parallel_strategy = parameter([None, 'horovod', 'ddp'])
    parallel_strategy = parameter([None, 'ddp'])
    compute_device = variable(str)
    # module_name = parameter(find_modules('PyTorch-bundle'))
    module_name = parameter(find_modules('torchvision'))

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
        if self.compute_device==DEVICE_TYPES[GPU]:
            hooks.assign_tasks_per_compute_unit(test=self, compute_unit=COMPUTE_UNIT[GPU])
        else:
            # Hybrid code, so launch 1 rank per socket.
            # Probably, launching 1 task per NUMA domain is even better, but the current hook doesn't support it
            hooks.assign_tasks_per_compute_unit(test=self, compute_unit=COMPUTE_UNIT[NUMA_NODE])

        # This is a hybrid test, binding is important for performance
        hooks.set_compact_process_binding(self)

    @run_after('setup')
    def set_ddp_env_vars(self):
        # Set environment variables for PyTorch DDP
        ### TODO: THIS WILL ONLY WORK WITH SLURM, WE SHOULD MAKE A SKIP_IF BASED ON THE SCHEDULER
        if self.parallel_strategy == 'ddp':
            # Set additional options required by DDP
            self.executable_opts += ["--master-port $(python python_get_free_socket.py)"]
            self.executable_opts += ["--master-address $(hostname --fqdn)"]
            self.executable_opts += ["--world-size %s" % self.num_tasks]

    @run_after('setup')
    def filter_invalid_parameter_combinations(self):
        # We cannot detect this situation before the setup phase, because it requires self.num_tasks.
        # Thus, the core count of the node needs to be known, which is only the case after the setup phase.
        msg=f"Skipping test: parallel strategy is 'None', but requested process count is larger than one ({self.num_tasks})"
        self.skip_if(self.num_tasks > 1 and self.parallel_strategy is None, msg)
        msg=f"Skipping test: parallel strategy is {self.parallel_strategy}, but only one process is requested"
        self.skip_if(self.num_tasks == 1 and not self.parallel_strategy is None, msg)

    @run_after('setup')
    def pass_parallel_strategy(self):
        # Set parallelization strategy when using more than one process
        if self.num_tasks != 1:
            self.executable_opts += ['--use-%s' % self.parallel_strategy]

    @run_after('setup')
    def avoid_horovod_cpu_contention(self):
        # Horovod had issues with CPU performance, see https://github.com/horovod/horovod/issues/2804
        # The root cause is Horovod having two threads with very high utilization, which interferes with
        # the compute threads. It was fixed, but seems to be broken again in Horovod 0.28.1
        # The easiest workaround is to reduce the number of compute threads by 2
        if self.compute_device == DEVICE_TYPES[CPU] and self.parallel_strategy == 'horovod':
            self.env_vars['OMP_NUM_THREADS'] = max(self.num_cpus_per_task-2, 2)  # Never go below 2 compute threads

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
class PyTorch_torchvision_CPU(PyTorch_torchvision):
    compute_device = DEVICE_TYPES[CPU]


@rfm.simple_test
class PyTorch_torchvision_GPU(PyTorch_torchvision):
    compute_device = DEVICE_TYPES[GPU]
    precision = parameter(['default', 'mixed'])

    @run_after('init')
    def prepare_gpu_test(self):
        # Set precision
        if self.precision == 'mixed':
            self.executable_opts += ['--use-amp']

    @run_after('init')
    def skip_hvd_plus_amp(self):
        '''Skip combination of horovod and AMP, it does not work see https://github.com/horovod/horovod/issues/1417'''
        if self.parallel_strategy == 'horovod' and self.precision == 'mixed':
            self.valid_systems = [INVALID_SYSTEM]

