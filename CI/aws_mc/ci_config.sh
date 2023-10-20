# Configurable items
REFRAME_ARGS="--tag CI --tag 1_node|2_nodes"
REFRAME_VERSION=4.3.2  # ReFrame version that will be pip-installed to drive the test suite
# Latest release does not contain the `aws_mc.py` ReFrame config yet
# The custom EESSI_TESTSUITE_URL and EESSI_TESTSUITE_BRANCH can be removed in a follow-up PR
EESSI_TESTSUITE_URL='https://github.com/casparvl/test-suite.git'
EESSI_TESTSUITE_BRANCH='CI'
