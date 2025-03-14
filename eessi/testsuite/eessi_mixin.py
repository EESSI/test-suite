from reframe.core.builtins import parameter, run_after, run_before, variable
from reframe.core.exceptions import ReframeFatalError
from reframe.core.pipeline import RegressionMixin
from reframe.utility.sanity import make_performance_function
import reframe.utility.sanity as sn

from eessi.testsuite import hooks
from eessi.testsuite.constants import DEVICE_TYPES, SCALES, COMPUTE_UNITS, TAGS
from eessi.testsuite.utils import log
from eessi.testsuite import __version__ as testsuite_version


# Hooks from the Mixin class seem to be executed _before_ those of the child class
# Thus, if the Mixin class needs self.X to be defined in after setup, the child class would have to define it before
# setup. That's a disadvantage and might not always be possible - let's see how far we get. It also seems that,
# like normal inheritance, functions with the same in the child and parent class will mean the child class
# will overwrite that of the parent class. That is a plus, as we can use the EESSI_Mixin class as a basis,
# but still overwrite specific functions in case specific tests would require this
# TODO: for this reason, we probably want to put _each_ hooks.something invocation into a seperate function,
# so that each individual one can be overwritten
#
# Note that I don't think we can do anything about the things set in the class body, such as the parameter's.
# Maybe we can move those to an __init__ step of the Mixin, even though that is not typically how ReFrame
# does it anymore?
# That way, the child class could define it as class variables, and the parent can use it in its __init__ method?
class EESSI_Mixin(RegressionMixin):
    """
    All EESSI tests should derive from this mixin class unless they have a very good reason not to.
    To run correctly, tests inheriting from this class need to define variables and parameters that are used here.
    That definition needs to be done 'on time', i.e. early enough in the execution of the ReFrame pipeline.
    Here, we list which class attributes must be defined by the child class, and by (the end of) what phase:

    - Init phase: device_type, scale, module_name, bench_name (if bench_name_ci is set)
    - Setup phase: compute_unit, required_mem_per_node

    The child class may also overwrite the following attributes:

    - Init phase: time_limit, measure_memory_usage, bench_name_ci
    """

    # Set defaults for these class variables, can be overwritten by child class if desired
    measure_memory_usage = variable(bool, value=False)
    exact_memory = variable(bool, value=False)
    user_executable_opts = variable(str, value='')
    scale = parameter(SCALES.keys())
    bench_name = None
    bench_name_ci = None
    num_tasks_per_compute_unit = 1
    always_request_gpus = None

    # Create ReFrame variables for logging runtime environment information
    cvmfs_repo_name = variable(str, value='None')
    cvmfs_software_subdir = variable(str, value='None')
    full_modulepath = variable(str, value='None')
    # These are optionally set in CI on the command line
    EESSI_CONFIGS_URL = variable(str, value='None')
    EESSI_CONFIGS_BRANCH = variable(str, value='None')

    # Make sure the version of the EESSI test suite gets logged in the ReFrame report
    eessi_testsuite_version = variable(str, value=testsuite_version)

    # Note that the error for an empty parameter is a bit unclear for ReFrame 4.6.2, but that will hopefully improve
    # see https://github.com/reframe-hpc/reframe/issues/3254
    # If that improves: uncomment the following to force the user to set module_name
    # module_name = parameter()

    def __init_subclass__(cls, **kwargs):
        " set default values for built-in ReFrame attributes "
        super().__init_subclass__(**kwargs)
        cls.valid_prog_environs = ['default']
        cls.valid_systems = ['*']
        if not cls.time_limit:
            cls.time_limit = '1h'
        if not cls.readonly_files:
            msg = ' '.join([
                "Built-in attribute `readonly_files` is empty. To avoid excessive copying, it's highly recommended",
                "to add all files and/or dirs in `sourcesdir` that are needed but not modified during the test,",
                "thus can be symlinked into the stage dirs. If you are sure there are no such files,",
                "set `readonly_files = ['']`.",
            ])
            raise ReframeFatalError(msg)

    # Helper function to validate if an attribute is present it item_dict.
    # If not, print it's current name, value, and the valid_values
    def EESSI_mixin_validate_item_in_list(self, item, valid_items):
        """
        Check if the item 'item' exist in the values of 'valid_items'.
        If item is not found, an error will be raised that will mention the valid values for 'item'.
        """
        value = getattr(self, item)
        if value not in valid_items:
            if len(valid_items) == 1:
                msg = f"The variable '{item}' has value {value}, but the only valid value is {valid_items[0]}"
            else:
                msg = f"The variable '{item}' has value {value}, but the only valid values are {valid_items}"
            raise ReframeFatalError(msg)

    @run_after('init')
    def EESSI_mixin_validate_init(self):
        """Check that all variables that have to be set for subsequent hooks in the init phase have been set"""
        # List which variables we will need/use in the run_after('init') hooks
        var_list = ['device_type', 'scale', 'module_name', 'measure_memory_usage']
        for var in var_list:
            if not hasattr(self, var):
                msg = "The variable '%s' should be defined in any test class that inherits" % var
                msg += " from EESSI_Mixin before (or in) the init phase, but it wasn't"
                raise ReframeFatalError(msg)

        # Check that the value for these variables is valid,
        # i.e. exists in their respective dict from eessi.testsuite.constants
        self.EESSI_mixin_validate_item_in_list('device_type', DEVICE_TYPES[:])
        self.EESSI_mixin_validate_item_in_list('scale', SCALES.keys())
        self.EESSI_mixin_validate_item_in_list('valid_systems', [['*']])
        self.EESSI_mixin_validate_item_in_list('valid_prog_environs', [['default']])

    @run_after('init')
    def EESSI_mixin_run_after_init(self):
        """Hooks to run after init phase"""

        # Filter on which scales are supported by the partitions defined in the ReFrame configuration
        hooks.filter_supported_scales(self)

        hooks.filter_valid_systems_by_device_type(self, required_device_type=self.device_type)

        hooks.set_modules(self)

        # Set scales as tags
        hooks.set_tag_scale(self)

    @run_before('setup', always_last=True)
    def EESSI_mixin_measure_mem_usage(self):
        if self.measure_memory_usage:
            hooks.measure_memory_usage(self)
            # Since we want to do this conditionally on self.measure_mem_usage, we use make_performance_function
            # instead of the @performance_function decorator
            self.perf_variables['memory'] = make_performance_function(hooks.extract_memory_usage, 'MiB', self)

    @run_after('init', always_last=True)
    def EESSI_mixin_set_tag_ci(self):
        """
        Set CI tag if bench_name_ci and bench_name are set and are equal
        Also set tag on bench_name if set
        """
        tags_added = False
        if self.bench_name_ci:
            if not self.bench_name:
                msg = "Attribute bench_name_ci is set, but bench_name is not set"
                raise ReframeFatalError(msg)
            if self.bench_name == self.bench_name_ci:
                self.tags.add(TAGS.CI)
                tags_added = True
        if self.bench_name:
            self.tags.add(self.bench_name)
            tags_added = True
        if tags_added:
            log(f'tags set to {self.tags}')

    @run_after('setup')
    def EESSI_mixin_validate_setup(self):
        """Check that all variables that have to be set for subsequent hooks in the setup phase have been set"""
        var_list = ['compute_unit']
        for var in var_list:
            if not hasattr(self, var):
                msg = "The variable '%s' should be defined in any test class that inherits" % var
                msg += " from EESSI_Mixin before (or in) the setup phase, but it wasn't"
                raise ReframeFatalError(msg)

        # Check if mem_func was defined to compute the required memory per node as function of the number of
        # tasks per node
        if not hasattr(self, 'required_mem_per_node'):
            msg = "The function 'required_mem_per_node' should be defined in any test class that inherits"
            msg += " from EESSI_Mixin before (or in) the setup phase, but it wasn't. Note that this function"
            msg += " can use self.num_tasks_per_node, as it will be called after that attribute"
            msg += " has been set."
            raise ReframeFatalError(msg)

        # Check that the value for these variables is valid
        # i.e. exists in their respective dict from eessi.testsuite.constants
        self.EESSI_mixin_validate_item_in_list('compute_unit', COMPUTE_UNITS[:])

    @run_after('setup')
    def EESSI_mixin_assign_tasks_per_compute_unit(self):
        """Call hooks to assign tasks per compute unit, set OMP_NUM_THREADS, and set compact process binding"""
        hooks.assign_tasks_per_compute_unit(test=self, compute_unit=self.compute_unit,
                                            num_per=self.num_tasks_per_compute_unit)

        # Set OMP_NUM_THREADS environment variable
        hooks.set_omp_num_threads(self)

        # Set compact process binding
        hooks.set_compact_process_binding(self)

    @run_after('setup')
    def EESSI_mixin_request_mem(self):
        """Call hook to request the required amount of memory per node"""
        hooks.req_memory_per_node(self, app_mem_req=self.required_mem_per_node())

    @run_after('setup')
    def EESSI_mixin_log_runtime_info(self):
        """Log additional runtime information: which CVMFS repo was used (or if it was testing local software),
        path to the modulefile, EESSI software subdir, EESSI testsuite version"""
        self.postrun_cmds.append('echo "EESSI_CVMFS_REPO: $EESSI_CVMFS_REPO"')
        self.postrun_cmds.append('echo "EESSI_SOFTWARE_SUBDIR: $EESSI_SOFTWARE_SUBDIR"')
        if self.module_name:
            # Get full modulepath
            get_full_modpath = f'echo "FULL_MODULEPATH: $(module --location show {self.module_name})"'
            self.postrun_cmds.append(get_full_modpath)

    @run_before('run', always_last=True)
    def EESSI_mixin_set_user_executable_opts(self):
        "Override executable_opts with user_executable_opts if set on the cmd line"
        if self.user_executable_opts:
            log(f'Overwriting executable_opts {self.executable_opts} by executable_opts '
                'specified on cmd line {[self.user_executable_opts]}')
            self.executable_opts = [self.user_executable_opts]

    @run_after('run')
    def EESSI_mixin_extract_runtime_info_from_log(self):
        """Extracts the printed runtime info from the job log and logs it as reframe variables"""
        if self.is_dry_run():
            return

        # If EESSI_CVMFS_REPO environment variable was set, extract it and store it in self.cvmfs_repo_name
        repo_name = sn.extractall(r'EESSI_CVMFS_REPO: /cvmfs/(?P<repo>.*)$', f'{self.stagedir}/{self.stdout}',
                                  'repo', str)
        if repo_name:
            self.cvmfs_repo_name = f'{repo_name}'

        software_subdir = sn.extractall(r'EESSI_SOFTWARE_SUBDIR: (?P<subdir>.*)$',
                                        f'{self.stagedir}/{self.stdout}', 'subdir', str)
        if software_subdir:
            self.cvmfs_software_subdir = f'{software_subdir}'

        module_path = sn.extractall(r'FULL_MODULEPATH: (?P<modpath>.*)$', f'{self.stagedir}/{self.stdout}',
                                    'modpath', str)
        if module_path:
            self.full_modulepath = f'{module_path}'
