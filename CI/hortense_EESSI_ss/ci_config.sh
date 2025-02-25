# Configurable items
if [ -z "${TEST_SUITE_PARTITION}" ]; then
   echo "You have to indicate on which partition the test-suite will run on vsc-Hortense"
   echo "This environment variable needs to be set TEST_SUITE_PARTITION=cpu_rome_256gb"
   echo "Can only set to 'cpu_rome_256gb' untill new functionality of 'sched_options' is part of"
   echo "the ReFrame release https://github.com/reframe-hpc/reframe/issues/2970"
   exit 1
fi

if [ -z "${REFRAME_ARGS}" ]; then
    REFRAME_ARGS="--tag CI --tag 1_core --system hortense:${TEST_SUITE_PARTITION}"
fi

if [ -z "${UNSET_MODULEPATH}" ]; then
    export UNSET_MODULEPATH=False
    module --force purge
fi

if [ -z "${USE_EESSI_SOFTWARE_STACK}" ]; then
    export USE_EESSI_SOFTWARE_STACK=True
fi

if [ -z "${RFM_CONFIG_FILES}" ]; then
    export RFM_CONFIG_FILES="${TEMPDIR}/configs/config/vsc_hortense.py"
fi

if [ -z "${SET_LOCAL_MODULE_ENV}"]; then
    export SET_LOCAL_MODULE_ENV=True
fi

if [ -z "${LOCAL_MODULES}"]; then
    export LOCAL_MODULES="env/vsc/dodrio/${TEST_SUITE_PARTITION} env/slurm/dodrio/${TEST_SUITE_PARTITION}"
fi
