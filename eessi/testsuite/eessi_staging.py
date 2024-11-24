import reframe as rfm
from reframe.utility import sanity as sn


@rfm.simple_test
class EESSI_Staging(rfm.RunOnlyRegressionTest):
    '''Stage input files'''

    valid_systems = ['*']
    valid_prog_environs = ['*']
    executable = "true"
    local = True
    sanity_patterns = sn.assert_true(True)
