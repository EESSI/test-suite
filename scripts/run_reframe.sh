#!/bin/bash
# Author: Caspar van Leeuwen
# Description: This script can be used to do regular runs of the ReFrame test suite, e.g. from a cronjob.
# Setup instructions: make sure you have your github access key configured in your .ssh/config
# i.e. configure an entry with HostName github.com and IdentityFile pointing to the ssh key registered with Github

# Print info on the when and where this is ran
# Allows easy localization of the host with the cronjob
DATE=$(date)
HOST=$(hostname)
echo "Starting test suite on ${HOST} at ${date}"

# Configurable items 
TEMPDIR=$(mktemp --directory --tmpdir=/tmp  -t rfm.XXXXXXXXXX)
RFM_CONFIG_NAME=izum_vega.py
TAGS="-t 1_node|2_nodes"
# The hpctestlib as well as the reframe command will be based on this version
# May be adapted later to simply use reframe from the EESSI software stack
REFRAME_VERSION=4.2.1
REFRAME_VENV=reframe_421

# Create virtualenv for ReFrame using system python
python3 -m venv ${TEMPDIR}/${REFRAME_VENV}
source ${TEMPDIR}/${REFRAME_VENV}/bin/activate
python3 -m pip install reframe-hpc==${REFRAME_VERSION}

# Clone reframe repo to have the hpctestlib:
git clone git@github.com:reframe-hpc/reframe.git --branch v${REFRAME_VERSION} ${TEMPDIR}/reframe
export PYTHONPATH=${PYTHONPATH}:${TEMPDIR}/reframe

# Clone test suite repo
git clone git@github.com:EESSI/test-suite.git ${TEMPDIR}/test-suite
export PYTHONPATH=${PYTHONPATH}:${TEMPDIR}/test-suite/

# Start the EESSI environment
unset MODULEPATH
source /cvmfs/pilot.eessi-hpc.org/latest/init/bash

# Needed in order to make sure the reframe from our TEMPDIR is first on the PATH,
# prior to the one shipped with the 2021.12 compat layer
# Probably no longer needed with newer compat layer that doesn't include ReFrame
deactivate
source ${TEMPDIR}/${REFRAME_VENV}/bin/activate

# Run ReFrame
echo "PYTHONPATH: ${PYTHONPATH}"
options=(
    --config-file ${TEMPDIR}/test-suite/config/${RFM_CONFIG_NAME}
    --checkpath ${TEMPDIR}/test-suite/eessi/testsuite/tests/apps/
    --recursive  # Search for checks in the search path recursively
    --tag CI ${TAGS}
    --run
    --performance-report
)
reframe "${options[@]}"

# Cleanup
rm -rf ${TEMPDIR}
