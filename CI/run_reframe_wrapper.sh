#!/bin/bash
# Author: Caspar van Leeuwen
# Description: wraps the run_reframe.sh script so that all stdout and stderr is easily be collected in a logfile
# which has a datestamp in the name.

# logfile
if [ ! -z ${EESSI_CI_LOGDIR} ]; then
    LOGDIR=${EESSI_CI_LOGDIR}
else
    LOGDIR=${HOME}/EESSI_CI_LOGS
fi
mkdir -p ${LOGDIR}

datestamp=$(date +%Y%m%d_%H%M%S)
LOGFILE=${LOGDIR}/rfm_${datestamp}.log
touch $LOGFILE

# Get directory of the current script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Execute run_reframe.sh, which should be in the same directory as the current script
${SCRIPT_DIR}/run_reframe.sh > $LOGFILE 2>&1
