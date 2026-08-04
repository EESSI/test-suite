#!/bin/bash
# Author: Caspar van Leeuwen
# Description: This script can be used to do regular runs of the ReFrame test suite, e.g. from a cronjob.
# Setup instructions:
# 1) make sure you have your github access key configured in your .ssh/config
#    i.e. configure an entry with HostName github.com and IdentityFile pointing to the ssh key registered with Github
# 2) set environment variable EESSI_CI_TEMPROOT, a path in a shared filesystem in which the temporary directory will be created
#    if $EESSI_CI_TEMPROOT is not set, $HOME will be used.

# Print on which host this CI is running
echo "Running CI on host $(hostname)"

# Get directory of the current script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo $SCRIPT_DIR
# Check if EESSI_CI_SYSTEM_NAME is defined
if [ -z "${EESSI_CI_SYSTEM_NAME}" ]; then 
    echo "You have to define the EESSI_CI_SYSTEM_NAME environment variable in order to run the EESSI test suite CI" > /dev/stderr
    echo "Valid EESSI_CI_SYSTEM_NAME's are:"
    echo "$(find $SCRIPT_DIR -mindepth 1 -maxdepth 1 -type d -exec basename {} \;)"
    exit 1
fi

# Check if CI_CONFIG file file exists
CI_CONFIG="${SCRIPT_DIR}/${EESSI_CI_SYSTEM_NAME}/ci_config.sh"
if [ ! -f "${CI_CONFIG}" ]; then
    echo "File ${CI_CONFIG} does not exist. Please check your EESSI_CI_SYSTEM_NAME (${EESSI_CI_SYSTEM_NAME}) and make sure the directory in which the current script resides (${SCRIPT_DIR}) contains a subdirectory with that name, and a CI configuration file (ci_config.sh) inside". > /dev/stderr
    exit 1
fi

# Create temporary directory
if [ -z "${TEMPDIR}" ]; then
    TEMPDIR=$(mktemp --directory --tmpdir=${EESSI_CI_TEMPROOT:-$HOME}  -t rfm.XXXXXXXXXX)
fi

# Set the CI configuration for this system
source "${CI_CONFIG}"

# Set default configuration, but let anything set by CI_CONFIG take priority
# Arguments that will be passed to the `reframe` command
REFRAME_ARGS="${REFRAME_ARGS:---tag CI --tag 1_node}"
# Version of ReFrame that will be pip-installed
REFRAME_VERSION="${REFRAME_VERSION:-4.8.1}"
# URL that will be used to clone the testsuite from.
# The same URL will be used by default to get the ReFrame config files from, unless EESSI_CONFIGS_TESTSUITE_URL is explicitely set
EESSI_TESTSUITE_URL="${EESSI_TESTSUITE_URL:-https://github.com/EESSI/test-suite.git}"
if [ -z "${EESSI_TESTSUITE_BRANCH}" ]; then
    git clone -n --depth=1 --filter=tree:0 ${EESSI_TESTSUITE_URL} "${TEMPDIR}/test-suite-version-checkout"
    cd "${TEMPDIR}/test-suite-version-checkout"
    git fetch --tags
    # This assumes we stick to a version-tagging scheme vX.Y.Z
    LATEST_VERSION=$(git tag --list 'v*' | sort -V | tail -n1)
    # Use the latest release by default
    EESSI_TESTSUITE_BRANCH="${LATEST_VERSION}"
    cd ${TEMPDIR}
fi
# The URL used to clone the ReFrame configuration files from
EESSI_CONFIGS_TESTSUITE_URL="${EESSI_CONFIGS_TESTSUITE_URL:-${EESSI_TESTSUITE_URL}}"
# The branch to clone for the ReFrame configuration files
EESSI_CONFIGS_TESTSUITE_BRANCH="${EESSI_CONFIGS_TESTSUITE_BRANCH:-${EESSI_TESTSUITE_BRANCH}}"
# If no module command is available from the system, the lmod init script will be sourced from the EESSI
# version defined by USE_MODULECMD_FROM_EESSI_VERSION
export USE_MODULECMD_FROM_EESSI_VERSION="${USE_MODULECMD_FROM_EESSI_VERSION:-2025.06}"
# The CVMFS repository that will be used to provide the module command or
# (if testing the EESSI software stack AND a module command is already available) to provide the modules to initialize EESSI
export EESSI_CVMFS_REPO="${EESSI_CVMFS_REPO:-/cvmfs/software.eessi.io}"
# Determines if the EESSI software stack will be tested (as opposed to just local modules)
export USE_EESSI_SOFTWARE_STACK="${USE_EESSI_SOFTWARE_STACK:-True}"
if [ "$USE_EESSI_SOFTWARE_STACK" == "True" ]; then
    # Which versions of EESSI will be tested. Note that these are names of ReFrame programming environments.
    # These need to match names that are defined in the ReFrame configuration file
    export REFRAME_EESSI_PROGRAMMING_ENVS="${REFRAME_EESSI_PROGRAMMING_ENVS:-EESSI-2023.06,EESSI-2025.06}"
fi
# Which ReFrame configuration file to use.
# Defaults to the ones from the EESSI_CONFIGS_TESTSUITE_URL and EESSI_CONFIGS_TESTSUITE_BRANCH for the provided EESSI_CI_SYSTEM_NAME
export RFM_CONFIG_FILES="${RFM_CONFIG_FILES:-${TEMPDIR}/configs/config/${EESSI_CI_SYSTEM_NAME}.py}"
# Path that ReFrame should search for tests
export RFM_CHECK_SEARCH_PATH="${RFM_CHECK_SEARCH_PATH:-${TEMPDIR}/test-suite/eessi/testsuite/tests/}"
# Should ReFrame search the path recursively
export RFM_CHECK_SEARCH_RECURSIVE="${RFM_CHECK_SEARCH_RECURSIVE:-1}"
# Where should reframe store the staging / output dirs etc
export RFM_PREFIX="${RFM_PREFIX:-${HOME}/reframe_CI_runs}"
# 10 minutes short of 1 day, since typically the test suite will be run daily.
# This will prevent multiple ReFrame runs from piling up and exceeding the quota on our Magic Castle clusters
export REFRAME_TIMEOUT="${REFRAME_TIMEOUT:-1430m}"
# Unsets the MODULEPATH before loading any EESSI or local environment modules
export UNSET_MODULEPATH="${UNSET_MODULEPATH:-True}"
# Which local programming environments to test. Note that these are names of ReFrame programming environments.
# These need to match names that are defined in the ReFrame configuration file
export REFRAME_LOCAL_PROGRAMMING_ENVS="${REFRAME_LOCAL_PROGRAMMING_ENVS:-}"  # Assumed to be a comma seperated list

# Check that SOME programming env has been defined. If not, exit early with instructions
if [ -z $REFRAME_EESSI_PROGRAMMING_ENVS ] && [ -z $REFRAME_LOCAL_PROGRAMMING_ENVS ]; then
    msg="You should define at least one ReFrame programming environment that needs to be tested (by defining either"
    msg="$msg REFRAME_EESSI_PROGRAMMING_ENVS or REFRAME_LOCAL_PROGRAMMING_ENVS). Note that"
    msg="$msg REFRAME_EESSI_PROGRAMMING_ENVS can be set indirectly by setting USE_EESSI_SOFTWARE_STACK=True."
    msg="$msg Exiting..."
    echo "$msg"
    exit 1
fi

# Create virtualenv for ReFrame using system python
python3 -m venv "${TEMPDIR}"/reframe_venv
source "${TEMPDIR}"/reframe_venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install reframe-hpc=="${REFRAME_VERSION}"

# Clone configs from test suite repo
EESSI_CONFIGS_CLONE_ARGS="-n --filter=tree:0 ${EESSI_CONFIGS_TESTSUITE_URL} --branch ${EESSI_CONFIGS_TESTSUITE_BRANCH} --depth 1 ${TEMPDIR}/configs"
echo "Cloning configs from EESSI test suite repo:"
echo "git clone ${EESSI_CONFIGS_CLONE_ARGS}"
git clone ${EESSI_CONFIGS_CLONE_ARGS}
echo "cd ${TEMPDIR}/configs"
cd ${TEMPDIR}/configs
echo "git sparse-checkout set --no-cone config"
git sparse-checkout set --no-cone config
echo "git checkout"
git checkout
# Return to TEMPDIR
echo "cd ${TEMPDIR}"
cd ${TEMPDIR}

# Clone test suite repo
EESSI_CLONE_ARGS="${EESSI_TESTSUITE_URL} --branch ${EESSI_TESTSUITE_BRANCH} --depth 1 ${TEMPDIR}/test-suite"
echo "Cloning EESSI repo: git clone ${EESSI_CLONE_ARGS}"
git clone ${EESSI_CLONE_ARGS}
export PYTHONPATH="${PYTHONPATH}":"${TEMPDIR}"/test-suite/

# Unset the ModulePath on systems where it is required
unset MODULEPATH_ORIGINAL  # Make sure this isn't defined, or we might restore from some external value later on
if [ "$UNSET_MODULEPATH" == "True" ]; then
    unset MODULEPATH
else
    # Store the original modulepath. If we need to use the module command from EESSI, we need
    # to restore this modulepath after initializing the module command
    MODULEPATH_ORIGINAL=$MODULEPATH
fi

# With https://github.com/EESSI/test-suite/pull/326 we no longer need to load the EESSI module
# before running the reframe command (reframe will load the modules for us)
# However, on systems in which there is no module command, we do need to initialize an
# EESSI environment to get a module command
if ! command -v module &>/dev/null; then
    # No module command available
    if [ ! -z "$USE_MODULECMD_FROM_EESSI_VERSION" ]; then
        echo "Using module command from EESSI version ${USE_MODULECMD_FROM_EESSI_VERSION}"
        source "${EESSI_CVMFS_REPO}/versions/${USE_MODULECMD_FROM_EESSI_VERSION}/init/lmod/bash"
        module unload EESSI
	if [ ! -z "$MODULEPATH_ORIGINAL" ]; then
	    echo "Prepending original modulepath: $MODULEPATH_ORIGINAL"
	    module use "$MODULEPATH_ORIGINAL"
        fi
    else
        msg="No module command available, and this CI run was not configured to use the EESSI module command."
        msg="$msg Consider setting 'USE_MODULECMD_FROM_EESSI_VERSION=<eessi_version>' in your CI runs to use a module"
        msg="$msg command from the EESSI compatibility layer. Exiting..."
        echo $msg
        exit 1
    fi
else
    # Module command available. Make sure the EESSI modules are on the PATH if we are testing EESSI environments
    if [ "$USE_EESSI_SOFTWARE_STACK" == "True" ]; then
        module use "${EESSI_CVMFS_REPO}/init/modules/"
    fi
fi

# Needed in order to make sure the reframe from our TEMPDIR is first on the PATH,
# prior to the one shipped with the 2021.12 compat layer
# Probably no longer needed with newer compat layer that doesn't include ReFrame
deactivate
source "${TEMPDIR}"/reframe_venv/bin/activate

# Modify the REFRAME_ARGS to take the requested programming environments into account
REFRAME_PROGRAMMING_ENVS="${REFRAME_LOCAL_PROGRAMMING_ENVS},${REFRAME_EESSI_PROGRAMMING_ENVS}"
REFRAME_PROGRAMMING_ENVS="${REFRAME_PROGRAMMING_ENVS%,}"  # Remove any leading comma in case 1st list is empty
REFRAME_PROGRAMMING_ENVS="${REFRAME_PROGRAMMING_ENVS#,}"  # Remove any trailing comma in case 2nd list is empty
# Replace commas by | since ReFrame expects a regex and we want tests to run if they match any of the programming envs
REFRAME_PROGRAMMING_ENVS_PIPED="${REFRAME_PROGRAMMING_ENVS//,/|}"
# This should always be true, as either REFRAME_LOCAL_PROGRAMMING_ENVS or REFRAME_EESSI_PROGRAMMING_ENVS should be
# defined (otherwise this script would have already hit an early exit, see above). But check in case the manipulation
# of these envirionment variables above somehow failed
if [ -n "$REFRAME_PROGRAMMING_ENVS_PIPED" ]; then
    REFRAME_ARGS="${REFRAME_ARGS} -p $REFRAME_PROGRAMMING_ENVS_PIPED"
else
    msg="REFRAME_PROGRAMMING_ENVS_PIPED appears to be unset or emtpy. This should never happen."
    msg="$msg It is constructed from REFRAME_EESSI_PROGRAMMING_ENVS=$REFRAME_EESSI_PROGRAMMING_ENVS and"
    msg="$msg REFRAME_LOCAL_PROGRAMMING_ENVS=$REFRAME_LOCAL_PROGRAMMING_ENVS. Please check that either of these"
    msg="$msg has been set. Exiting..."
    echo "$msg"
    exit 1
fi

# Print ReFrame config
echo "Starting CI run with the follwing settings:"
echo ""
echo "TEMPDIR: ${TEMPDIR}"
echo "PYTHONPATH: ${PYTHONPATH}"
echo "EESSI test suite URL: ${EESSI_TESTSUITE_URL}"
echo "EESSI test suite version: ${EESSI_TESTSUITE_BRANCH}"
echo "EESSI test suite URL for configs: ${EESSI_CONFIGS_TESTSUITE_URL}"
echo "EESSI test suite version for configs: ${EESSI_CONFIGS_TESTSUITE_BRANCH}"
echo "ReFrame executable: $(which reframe)"
echo "ReFrame version: $(reframe --version)"
echo "ReFrame config file: ${RFM_CONFIG_FILES}"
echo "ReFrame check search path: ${RFM_CHECK_SEARCH_PATH}"
echo "ReFrame check search recursive: ${RFM_CHECK_SEARCH_RECURSIVE}"
echo "ReFrame prefix: ${RFM_PREFIX}"
echo "Testing ReFrame programming environments: ${REFRAME_PROGRAMMING_ENVS}"
echo "ReFrame args: ${REFRAME_ARGS}"
echo "Using EESSI: ${USE_EESSI_SOFTWARE_STACK}"
echo "MODULEPATH: ${MODULEPATH}"
echo ""

# List tests
echo "Listing tests:"
reframe ${REFRAME_ARGS} --list

# Run
echo "Run tests:"
timeout -v --preserve-status -s SIGTERM ${REFRAME_TIMEOUT} reframe ${REFRAME_ARGS} --run --setvar EESSI_CONFIGS_URL=${EESSI_CONFIGS_TESTSUITE_URL} --setvar EESSI_CONFIGS_BRANCH=${EESSI_CONFIGS_TESTSUITE_BRANCH}

# Cleanup
rm -rf "${TEMPDIR}"
