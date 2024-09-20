import setuptools
import pkg_resources


# write_to got replaced by version_file starting from setuptools_scm v8.
def get_setuptools_scm_version():
    try:
        scm_version = pkg_resources.get_distribution("setuptools_scm").version
        return tuple(map(int, scm_version.split(".")[:2]))  # Convert version string to tuple, e.g., (8, 0)
    except pkg_resources.DistributionNotFound:
        return (0, 0)  # If setuptools_scm is not found, assume version 0.0


scm_version = get_setuptools_scm_version()

if scm_version >= (8, 0):
    scm_arg_key = "version_file"
else:
    scm_arg_key = "write_to"

setuptools.setup(
    use_scm_version={scm_arg_key: "eessi/testsuite/_version.py"},
    setup_requires=['setuptools_scm'],
)
