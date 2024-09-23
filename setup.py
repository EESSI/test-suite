import setuptools
import sys

python_version = sys.version_info
if python_version < (3, 8):
    scm_require = ['packaging<=21.3', 'setuptools_scm<7']
    scm_arg_key = "write_to"
else:
    scm_require = ['setuptools_scm>=8']
    scm_arg_key = "version_file"


from eessi.testsuite import __version__

setuptools.setup(
    use_scm_version={scm_arg_key: 'eessi/testsuite/_version.py', fallback_version = __version__},
    setup_requires=scm_require,
)
