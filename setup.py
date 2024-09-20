import sys
import setuptools

# write_to got replaced by version_file starting from setuptools_scm v8.
# This version is only supported for python 3.8 and above
python_version = sys.version_info
if python_version < (3, 8):
    scm_arg_key = "write_to"
else:
    scm_arg_key = "version_file"

setuptools.setup(
    use_scm_version={scm_arg_key: "eessi/testsuite/_version.py"},
    setup_requires=['setuptools_scm'],
)
