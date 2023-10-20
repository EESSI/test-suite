#!/bin/bash
# Author: Caspar van Leeuwen
# Description: This script can be used to do regular runs of the ReFrame test suite, e.g. from a cronjob.
# Setup instructions: make sure you have your github access key configured in your .ssh/config
# i.e. configure an entry with HostName github.com and IdentityFile pointing to the ssh key registered with Github

# Get directory of the current script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Check if EESSI_CI_SYSTEM_NAME is defined
if [ -z "${EESSI_CI_SYSTEM_NAME}" ]; then 
    echo "You have to define the EESSI_CI_SYSTEM_NAME environment variable in order to run the EESSI test suite CI" > /dev/stderr
    exit 1
fi

# Check if CI_CONFIG file file exists
CI_CONFIG="${SCRIPT_DIR}/${EESSI_CI_SYSTEM_NAME}/ci_config.sh"
if [ ! -f ${CI_CONFIG} ]; then
    echo "File ${CI_CONFIG} does not exist. Please check your RFM_CI_SYSTEM_NAME (${EESSI_CI_SYSTEM_NAME}) and make sure the directory in which the current script resides (${SCRIPT_DIR}) contains a subdirectory with that name, and a CI configuration file (ci_config.sh) inside". > /dev/stderr
    exit 1
fi

# Set the CI configuration for this system
source ${CI_CONFIG}

# Set default configuration
if [ -z ${TEMPDIR} ]; then
    TEMPDIR=$(mktemp --directory --tmpdir=/tmp  -t rfm.XXXXXXXXXX)
fi
if [ -z ${REFRAME_ARGS} ]; then
    REFRAME_ARGS="--tag CI --tag 1_node"
fi
if [ -z ${REFRAME_URL} ]; then
    REFRAME_URL='https://github.com/reframe-hpc/reframe.git'
fi
if [ -z ${REFRAME_BRANCH} ]; then
    REFRAME_BRANCH="v${REFRAME_VERSION}"
fi
if [ -z ${EESSI_TESTSUITE_URL} ]; then
    EESSI_TESTSUITE_URL='https://github.com/EESSI/test-suite.git'
fi
if [ -z ${EESSI_TESTSUITE_BRANCH} ]; then
    EESSI_TESTSUITE_BRANCH='v0.1.0'
fi
if [ -z ${EESSI_VERSION} ]; then
    EESSI_VERSION='latest'
fi
if [ -z ${RFM_CONFIG_FILES} ]; then
    RFM_CONFIG_FILES="${TEMPDIR}/test-suite/config/${EESSI_CI_SYSTEM_NAME}.py"
fi
if [ -z ${RFM_CHECK_SEARCH_PATH} ]; then
    RFM_CHECK_SEARCH_PATH="${TEMPDIR}/test-suite/eessi/testsuite/tests/"
fi
if [ -z ${RFM_CHECK_SEARCH_RECURSIVE} ]; then
    RFM_CHECK_SEARCH_RECURSIVE=1
fi
if [ -z ${RFM_PREFIX} ]; then
    RFM_PREFIX="${HOME}/reframe_CI_runs"
fi

# Create virtualenv for ReFrame using system python
python3 -m venv ${TEMPDIR}/reframe_venv
source ${TEMPDIR}/reframe_venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install reframe-hpc==${REFRAME_VERSION}

# Clone reframe repo to have the hpctestlib:
git clone ${REFRAME_URL} --branch ${REFRAME_BRANCH} ${TEMPDIR}/reframe
export PYTHONPATH=${PYTHONPATH}:${TEMPDIR}/reframe

# Clone test suite repo
git clone ${EESSI_TESTSUITE_URL} --branch ${EESSI_TESTSUITE_BRANCH} ${TEMPDIR}/test-suite
export PYTHONPATH=${PYTHONPATH}:${TEMPDIR}/test-suite/

# Start the EESSI environment
unset MODULEPATH
source /cvmfs/pilot.eessi-hpc.org/versions/${EESSI_VERSION}/init/bash

# Needed in order to make sure the reframe from our TEMPDIR is first on the PATH,
# prior to the one shipped with the 2021.12 compat layer
# Probably no longer needed with newer compat layer that doesn't include ReFrame
deactivate
source ${TEMPDIR}/reframe_venv/bin/activate

# Print ReFrame config
echo "Starting CI run with the follwing settings:"
echo ""
echo "TEMPDIR: ${TEMPDIR}"
echo "PYTHONPATH: ${PYTHONPATH}"
echo "EESSI test suite URL: ${EESSI_TESTSUITE_URL}"
echo "EESSI test suite version: ${EESSI_TESTSUITE_VERSION}"
echo "HPCtestlib from ReFrame URL: ${REFRAME_URL}"
echo "HPCtestlib from ReFrame branch: ${REFRAME_BRANCH}"
echo "ReFrame executable: $(which reframe)"
echo "ReFrame version: $(reframe --version)"
echo "ReFrame config file: ${RFM_CONFIG_FILES}"
echo "ReFrame check search path: ${RFM_CHECK_SEARCH_PATH}"
echo "ReFrame check search recursive: ${RFM_CHECK_SEARCH_RECURSIVE}"
echo "ReFrame prefix: ${RFM_PREFIX}"
echo "ReFrame args: ${REFRAME_ARGS}"
echo ""

# List tests
echo "Listing tests:"
reframe ${REFRAME_ARGS} --list

# Run
echo "Run tests:"
reframe ${REFRAME_ARGS} --run

# Cleanup
rm -rf ${TEMPDIR}
