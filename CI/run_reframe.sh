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
if [ -z "${REFRAME_ARGS}" ]; then
    REFRAME_ARGS="--tag CI --tag 1_node"
fi
if [ -z "${REFRAME_VERSION}"]; then
    REFRAME_VERSION=4.7.3
fi
if [ -z "${REFRAME_URL}" ]; then
    REFRAME_URL='https://github.com/reframe-hpc/reframe.git'
fi
if [ -z "${REFRAME_BRANCH}" ]; then
    REFRAME_BRANCH="v${REFRAME_VERSION}"
fi
if [ -z "${EESSI_TESTSUITE_URL}" ]; then
    EESSI_TESTSUITE_URL='https://github.com/EESSI/test-suite.git'
fi
if [ -z "${EESSI_TESTSUITE_BRANCH}" ]; then
    git clone -n --depth=1 --filter=tree:0 ${EESSI_TESTSUITE_URL} "${TEMPDIR}/test-suite-version-checkout"
    cd "${TEMPDIR}/test-suite-version-checkout"
    git fetch --tags
    # This assumes we stick to a version-tagging scheme vX.Y.Z
    LATEST_VERSION=$(git tag | grep '^v[0-9]\+\.[0-9]\+\.[0-9]\+$' | sort -t. -k 1,1n -k 2,2n -k 3,3n | tail -1)
    # Use the latest release by default
    EESSI_TESTSUITE_BRANCH="${LATEST_VERSION}"
    cd ${TEMPDIR}
fi
if [ -z "${EESSI_CONFIGS_TESTSUITE_URL}" ]; then
    EESSI_CONFIGS_TESTSUITE_URL="${EESSI_TESTSUITE_URL}"
fi
if [ -z "${EESSI_CONFIGS_TESTSUITE_BRANCH}" ]; then
    EESSI_CONFIGS_TESTSUITE_BRANCH="${EESSI_TESTSUITE_BRANCH}"
fi
if [ -z "${USE_EESSI_SOFTWARE_STACK}" ] || [ "$USE_EESSI_SOFTWARE_STACK" == "True" ]; then
    export USE_EESSI_SOFTWARE_STACK=True
    if [ -z "${EESSI_CVMFS_REPO}" ]; then
        export EESSI_CVMFS_REPO=/cvmfs/software.eessi.io
    fi
    if [ -z "${EESSI_VERSION}" ]; then
        export EESSI_VERSION=2023.06
    fi
fi
if [ -z "${RFM_CONFIG_FILES}" ]; then
    export RFM_CONFIG_FILES="${TEMPDIR}/configs/config/${EESSI_CI_SYSTEM_NAME}.py"
fi
if [ -z "${RFM_CHECK_SEARCH_PATH}" ]; then
    export RFM_CHECK_SEARCH_PATH="${TEMPDIR}/test-suite/eessi/testsuite/tests/"
fi
if [ -z "${RFM_CHECK_SEARCH_RECURSIVE}" ]; then
    export RFM_CHECK_SEARCH_RECURSIVE=1
fi
if [ -z "${RFM_PREFIX}" ]; then
    export RFM_PREFIX="${HOME}/reframe_CI_runs"
fi
if [ -z "${REFRAME_TIMEOUT}" ]; then
    # 10 minutes short of 1 day, since typically the test suite will be run daily.
    # This will prevent multiple ReFrame runs from piling up and exceeding the quota on our Magic Castle clusters
    export REFRAME_TIMEOUT=1430m
fi
if [ -z "${UNSET_MODULEPATH}" ]; then
    export UNSET_MODULEPATH=True
fi
if [ -z "${SET_LOCAL_MODULE_ENV}" ]; then
    export SET_LOCAL_MODULE_ENV=False
fi

# Create virtualenv for ReFrame using system python
python3 -m venv "${TEMPDIR}"/reframe_venv
source "${TEMPDIR}"/reframe_venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install reframe-hpc=="${REFRAME_VERSION}"

# Clone reframe repo to have the hpctestlib:
REFRAME_CLONE_ARGS="${REFRAME_URL} --branch ${REFRAME_BRANCH} --depth 1 ${TEMPDIR}/reframe"
echo "Cloning ReFrame repo: git clone ${REFRAME_CLONE_ARGS}"
git clone ${REFRAME_CLONE_ARGS}
export PYTHONPATH="${PYTHONPATH}":"${TEMPDIR}"/reframe

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
if [ "$UNSET_MODULEPATH" == "True" ]; then
    unset MODULEPATH
fi

# Set local module environment
if [ "$SET_LOCAL_MODULE_ENV" == "True" ]; then
    if [ -z "${LOCAL_MODULES}" ]; then
        echo "You have to add the name of the module in the ci_config.sh file of your system"
        exit 1
    fi
    module load "${LOCAL_MODULES}"
fi

# Start the EESSI environment
if [ "$USE_EESSI_SOFTWARE_STACK" == "True" ]; then
    eessi_init_path="${EESSI_CVMFS_REPO}"/versions/"${EESSI_VERSION}"/init/bash
    source "${eessi_init_path}"
fi

# Needed in order to make sure the reframe from our TEMPDIR is first on the PATH,
# prior to the one shipped with the 2021.12 compat layer
# Probably no longer needed with newer compat layer that doesn't include ReFrame
deactivate
source "${TEMPDIR}"/reframe_venv/bin/activate

# Print ReFrame config
echo "Starting CI run with the follwing settings:"
echo ""
echo "TEMPDIR: ${TEMPDIR}"
echo "PYTHONPATH: ${PYTHONPATH}"
echo "EESSI test suite URL: ${EESSI_TESTSUITE_URL}"
echo "EESSI test suite version: ${EESSI_TESTSUITE_BRANCH}"
echo "EESSI test suite URL for configs: ${EESSI_CONFIGS_TESTSUITE_URL}"
echo "EESSI test suite version for configs: ${EESSI_CONFIGS_TESTSUITE_BRANCH}"
echo "HPCtestlib from ReFrame URL: ${REFRAME_URL}"
echo "HPCtestlib from ReFrame branch: ${REFRAME_BRANCH}"
echo "ReFrame executable: $(which reframe)"
echo "ReFrame version: $(reframe --version)"
echo "ReFrame config file: ${RFM_CONFIG_FILES}"
echo "ReFrame check search path: ${RFM_CHECK_SEARCH_PATH}"
echo "ReFrame check search recursive: ${RFM_CHECK_SEARCH_RECURSIVE}"
echo "ReFrame prefix: ${RFM_PREFIX}"
echo "ReFrame args: ${REFRAME_ARGS}"
echo "Using EESSI: ${USE_EESSI_SOFTWARE_STACK}"
echo "Using local software stack ${SET_LOCAL_MODULE_ENV}"
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
