#!/bin/bash
# Author: Caspar van Leeuwen
# Description: This script can be used to do regular runs of the ReFrame test suite, e.g. from a cronjob.
# 

# Configurable items 
TEMPDIR=$(mktemp --directory --tmpdir=/tmp  -t rfm.XXXXXXXXXX)
RFM_CONFIG_NAME=izum_vega.py
TAGS="-t 1_node|2_nodes"
GIT_PRIVATE_KEY="~/.ssh/id_github_ed25519"  # Location of git private key, to be added to ssh-agent
REFRAME_VERSION=4.2.1
REFRAME_VENV=reframe_421

# Add SSH key to agent, needed for git clone commands
eval "$(ssh-agent -s)"
ssh-add ${GIT_PRIVATE_KEY}

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
reframe -C ${TEMPDIR}/test-suite/config/${RFM_CONFIG_NAME} -c ${TEMPDIR}/test-suite/eessi/testsuite/tests/apps/ -R -t CI ${TAGS} -r

# Cleanup
rm -rf ${TEMPDIR}
