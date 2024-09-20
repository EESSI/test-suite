import setuptools

setuptools.setup(
    use_scm_version={'write_to': 'eessi/testsuite/_version.py'},
    setup_requires=['setuptools_scm<7','packaging<=21.3'],
)
