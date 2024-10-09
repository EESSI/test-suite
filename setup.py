import setuptools
import sys
import pkg_resources


def get_version_by_import():
    # Add the fallback version to whatever was set for scm_dict
    sys.path.append('.')
    from eessi.testsuite import __version__
    return __version__


# Get python version
python_version = sys.version_info

# Get setuptools version
# We control it when installing from pyproject.toml, but not when installing from setup.py / setup.cfg
# Check setuptools version
current_setuptools_version = pkg_resources.parse_version(pkg_resources.get_distribution("setuptools").version)

# Set the version requirement for setuptools_scm, depending on the combination of Python and setuptools version
version_file_path = 'eessi/testsuite/_version.py'
scm_dict = {'write_to': version_file_path}
if python_version >= (3, 8) and current_setuptools_version >= pkg_resources.parse_version("61.0.0"):
    setuptools_scm_requirement = 'setuptools_scm>8.0.0,<=8.1.0'
    scm_dict = {'version_file': version_file_path}
elif python_version >= (3, 7) and current_setuptools_version >= pkg_resources.parse_version("45.0.0"):
    setuptools_scm_requirement = 'setuptools_scm>7.0.0,<=7.1.0'
elif python_version >= (3, 6) and current_setuptools_version >= pkg_resources.parse_version("45.0.0"):
    setuptools_scm_requirement = 'setuptools_scm>=6.0.0,<=6.4.2'
elif python_version >= (3, 6) and current_setuptools_version >= pkg_resources.parse_version("42.0.0"):
    setuptools_scm_requirement = 'setuptools_scm>=5.0.0,<=5.0.2'
elif python_version >= (3, 6) and current_setuptools_version >= pkg_resources.parse_version("34.4.0"):
    setuptools_scm_requirement = 'setuptools_scm>=4.0.0,<=4.1.2'

# Set the fallback_version for scm based on what eessi.testsuite.__version__ returns
scm_dict['fallback_version'] = get_version_by_import()

setuptools.setup(
    use_scm_version=scm_dict,
    setup_requires=[setuptools_scm_requirement],
)
