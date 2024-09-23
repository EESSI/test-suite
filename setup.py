import setuptools
import sys

python_version = sys.version_info
if python_version < (3, 8):
    scm_dict = {'write_to': 'eessi/testsuite/_version.py'}
    scm_require = ['packaging<=21.3', 'setuptools_scm<7']
    scm_arg_key = "write_to"
else:
    scm_dict = {'version_file': 'eessi/testsuite/_version.py', 'fallback_version': '80.0.0'}
    scm_require = ['setuptools>=61', 'setuptools_scm>=8']
    scm_arg_key = "version_file"

sys.path.append('.')
from eessi.testsuite import __version__

setuptools.setup(
    use_scm_version={scm_arg_key: 'eessi/testsuite/_version.py', 'fallback_version': __version__},
#    use_scm_version=scm_dict,
    setup_requires=scm_require,
)
