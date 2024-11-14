import reframe as rfm
from reframe.utility import sanity as sn

@rfm.simple_test
class EESSI_LAMMPS_stage_input(rfm.RunOnlyRegressionTest):
    '''Stage input files for LAMMPS'''

    valid_systems = ['*']
    valid_prog_environs = ['*']
    executable = "true"
    local = True

    # Check that all files have been staged correctly
    sanity_patterns = sn.assert_found('.*', 'rhodo/data.rhodo', "input file 'data.rhodo' seems to be missing")
