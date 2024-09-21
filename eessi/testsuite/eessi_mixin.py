from reframe.core.builtins import variable, parameter, run_after
from reframe.core.exceptions import ReframeSyntaxError
from reframe.core.pipeline import RegressionMixin
from reframe.utility.sanity import make_performance_function

from eessi.testsuite import hooks
from eessi.testsuite.constants import DEVICE_TYPES, SCALES, COMPUTE_UNIT

from eessi.testsuite import __version__ as EESSI_TESTSUITE_VERSION


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
    Here, we list which class attributes need to be defined, and by (the end of) what phase:

    - Init phase: device_type, scale, module_name
    - Setup phase: compute_unit, required_mem_per_node
    """

    # Current version of the EESSI test suite
    eessi_testsuite_version = variable(str, value=EESSI_TESTSUITE_VERSION)

    measure_memory_usage = False
#    valid_prog_environs = ['default']
#    valid_systems = ['*']
#    time_limit = '30m'
    scale = parameter(SCALES.keys())

    # Note that the error for an empty parameter is a bit unclear for ReFrame 4.6.2, but that will hopefully improve
    # see https://github.com/reframe-hpc/reframe/issues/3254
    # If that improves: uncomment the following to force the user to set module_name
    # module_name = parameter()

    # Helper function to validate if an attribute is present it item_dict.
    # If not, print it's current name, value, and the valid_values
    def validate_item_in_dict(self, item, item_dict, check_keys=False):
        """
        Check if the item 'item' exist in the values of 'item_dict'.
        If check_keys=True, then it will check instead of 'item' exists in the keys of 'item_dict'.
        If item is not found, an error will be raised that will mention the valid values for 'item'.
        """
        if check_keys:
            valid_items = list(item_dict.keys())
        else:
            valid_items = list(item_dict.values())

        value = getattr(self, item)
        if value not in valid_items:
            valid_items_str = (', '.join("'" + item + "'" for item in valid_items))
            msg = "The variable '%s' had value '%s', but the only valid values are %s" % (item, value, valid_items_str)
            raise ReframeSyntaxError(msg)

    # We have to make sure that these gets set in any test that inherits
    # device_type = variable(str)
    # scale = variable(str)
    # module_name = variable(str)

    @run_after('init')
    def validate_init(self):
        """Check that all variables that have to be set for subsequent hooks in the init phase have been set"""
        # List which variables we will need/use in the run_after('init') hooks
        var_list = ['device_type', 'scale', 'module_name', 'measure_memory_usage']
        for var in var_list:
            if not hasattr(self, var):
                msg = "The variable '%s' should be defined in any test class that inherits" % var
                msg += " from EESSI_Mixin in the init phase (or earlier), but it wasn't"
                raise ReframeSyntaxError(msg)

        # Check that the value for these variables is valid,
        # i.e. exists in their respective dict from eessi.testsuite.constants
        self.validate_item_in_dict('device_type', DEVICE_TYPES)
        self.validate_item_in_dict('scale', SCALES, check_keys=True)

    @run_after('init')
    def run_after_init(self):
        """Hooks to run after init phase"""

        # Filter on which scales are supported by the partitions defined in the ReFrame configuration
        hooks.filter_supported_scales(self)

        hooks.filter_valid_systems_by_device_type(self, required_device_type=self.device_type)

        hooks.set_modules(self)

        # Set scales as tags
        hooks.set_tag_scale(self)

    @run_after('init')
    def measure_mem_usage(self):
        if self.measure_memory_usage:
            hooks.measure_memory_usage(self)
            # Since we want to do this conditionally on self.measure_mem_usage, we use make_performance_function
            # instead of the @performance_function decorator
            self.perf_variables['memory'] = make_performance_function(hooks.extract_memory_usage, 'MiB', self)

    @run_after('setup')
    def validate_setup(self):
        """Check that all variables that have to be set for subsequent hooks in the setup phase have been set"""
        var_list = ['compute_unit']
        for var in var_list:
            if not hasattr(self, var):
                msg = "The variable '%s' should be defined in any test class that inherits" % var
                msg += " from EESSI_Mixin in the setup phase (or earlier), but it wasn't"
                raise ReframeSyntaxError(msg)

        # Check if mem_func was defined to compute the required memory per node as function of the number of
        # tasks per node
        if not hasattr(self, 'required_mem_per_node'):
            msg = "The function 'required_mem_per_node' should be defined in any test class that inherits"
            msg += " from EESSI_Mixin in the setup phase (or earlier), but it wasn't. Note that this function"
            msg += " can use self.num_tasks_per_node, as it will be called after that attribute"
            msg += " has been set."
            raise ReframeSyntaxError(msg)

        # Check that the value for these variables is valid
        # i.e. exists in their respective dict from eessi.testsuite.constants
        self.validate_item_in_dict('compute_unit', COMPUTE_UNIT)

    @run_after('setup')
    def assign_tasks_per_compute_unit(self):
        """hooks to run after the setup phase"""
        hooks.assign_tasks_per_compute_unit(test=self, compute_unit=self.compute_unit)

        # Set OMP_NUM_THREADS environment variable
        hooks.set_omp_num_threads(self)

        # Set compact process binding
        hooks.set_compact_process_binding(self)

    @run_after('setup')
    def request_mem(self):
        hooks.req_memory_per_node(self, app_mem_req=self.required_mem_per_node())
