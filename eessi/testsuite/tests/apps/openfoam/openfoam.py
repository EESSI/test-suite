"""
OpenFOAM Snappyhexmesh test
"""

import reframe as rfm
from reframe.core.builtins import parameter, run_after

from eessi.testsuite import hooks
from eessi.testsuite.constants import *
from eessi.testsuite.utils import find_modules, log


@rfm.simple_test
class EESSI_OPENFOAM_SNAPPYHEXMESH():
    scale 


