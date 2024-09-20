import setuptools
import sys

scm_version = get_setuptools_scm_version()

python_version = sys.version_info
if python_version < (3, 8):
    scm_require='setuptools_scm<7'
    scm_arg_key = "write_to"
else:
    scm_require='setuptools_scm>=8'
    scm_arg_key = "version_file"


setuptools.setup(
    use_scm_version={scm_arg_key: 'eessi/testsuite/_version.py'},
    setup_requires=[scm_require],
)
