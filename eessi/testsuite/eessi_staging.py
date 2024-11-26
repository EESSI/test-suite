from pathlib import Path

import reframe as rfm
from reframe.utility import sanity as sn
from reframe.core.builtins import run_after, sanity_function


@rfm.simple_test
class EESSI_Staging(rfm.RunOnlyRegressionTest):
    '''Stage input files'''

    valid_systems = ['*']
    valid_prog_environs = ['*']
    executable = "true"
    local = True

    @run_after('init')
    def remove_modules(self):
        "Remove any modules that have been set on the cmd line: they are not needed for staging"
        self.modules = []

    @sanity_function
    def check_stagedir(self):
        "Check that all input files have been correctly copied to the stagedir"
        ignore = {'rfm_job.sh', 'rfm_job.out', 'rfm_job.err'}
        sourcepath = Path(self.sourcesdir)
        sourcefiles = {x.relative_to(sourcepath).as_posix() for x in sourcepath.rglob('*')}
        stagepath = Path(self.stagedir)
        stagefiles = {x.relative_to(stagepath).as_posix() for x in stagepath.rglob('*')} - ignore

        return sn.assert_eq(
            sourcefiles, stagefiles,
            f'sourcesdir {self.sourcesdir} and stagedir {self.stagedir} do not have the same contents'
        )
