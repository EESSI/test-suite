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
        'QS/H2O-32.inp',
        'QS/H2O-128.inp',
        'QS/H2O-512.inp',
    ]
    sn_list = [sn.assert_found('.*', input_file) for input_file in input_file_list]
    sanity_patterns = sn.all([
        sn.assert_found('.*', input_file, f"input file '{input_file}' seems to be missing")
        for input_file in input_file_list
    ])
