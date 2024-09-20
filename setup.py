import setuptools

setuptools.setup(
    use_scm_version={"version_file": "eessi/testsuite/_version.py"},
    setup_requires=['setuptools_scm'],
)
