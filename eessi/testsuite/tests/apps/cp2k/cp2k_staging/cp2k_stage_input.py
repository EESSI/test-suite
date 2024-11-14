import reframe as rfm
from reframe.utility import sanity as sn


@rfm.simple_test
class EESSI_CP2K_stage_input(rfm.RunOnlyRegressionTest):
    '''Stage input files for CP2K'''

    valid_systems = ['*']
    valid_prog_environs = ['*']
    executable = "true"
    local = True

    # Check that all files have been staged correctly
    input_file_list = [
        'input/QS/H2O-32.inp',
        'input/QS/H2O-128.inp',
        'input/QS/H2O-512.inp'
    ]
    sn_list = [sn.assert_found('.*', input_file) for input_file in input_file_list]
    msg = "input file '%s' seems to be missing"
    sanity_patterns = sn.all([
        sn.assert_found('.*', input_file, msg % input_file) for input_file in input_file_list
    ])
