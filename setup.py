import setuptools
import pkg_resources

setuptools.setup(
    use_scm_version={'write_to': 'eessi/testsuite/_version.py'},
    setup_requires=['setuptools_scm'],
)
