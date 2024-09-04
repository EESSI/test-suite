from reframe.core.pipeline import RegressionMixin
from reframe.core.exceptions import ReframeSyntaxError

from eessi.testsuite import hooks

class EESSI_Mixin(RegressionMixin):
    """
    All EESSI tests should derive from this mixin class unless they have a very good reason not to.
    """
    
    # We have to make sure that these gets set in any test that inherits
    # device_type = variable(str)
    # scale = variable(str)
    # module_name = variable(str)

    @run_after('init')
    def validate(self):
        """Check that all variables that have to be set for subsequent hooks in the init phase have been set"""
        if not hasattr(self, 'device_type'):
            raise ReframeSyntaxError("device_type should be defined in any class that inherits from EESSI_Mixin, but wasn't")
            

    @run_after('init')
    def run_after_init(self):
        """Hooks to run after init phase"""

        # Filter on which scales are supported by the partitions defined in the ReFrame configuration
        hooks.filter_supported_scales(self)

        hooks.filter_valid_systems_by_device_type(self, required_device_type=self.device_type)

        hooks.set_modules(self)

        # Set scales as tags
        hooks.set_tag_scale(self)
