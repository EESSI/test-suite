#!/bin/bash
# Author: Caspar van Leeuwen
# Description: wraps the run_reframe.sh script so that all stdout and stderr is easily be collected in a logfile

# logfile
mkdir -p ~/rfm_weekly_logs

datestamp=$(date +%Y%m%d_%H%M%S)
LOGFILE=~/rfm_weekly_logs/rfm_weekly_${datestamp}.log
touch $LOGFILE

~/run_reframe.sh > $LOGFILE 2>&1
