# Configurable items
if [[ "$TEST_SUITE_PARTITION" == "GPU" ]]; then
    module --force purge
    if [ -z "${SET_LOCAL_MODULE_ENV}"]; then
        export SET_LOCAL_MODULE_ENV=True
    fi
    if [ -z "${LOCAL_MODULES}"]; then
        export LOCAL_MODULES="cluster/dodrio/gpu_rome_a100"
    fi
fi

if [ -z "${REFRAME_ARGS}" ]; then
    REFRAME_ARGS="--tag CI --tag 1_node|2_nodes"
fi

if [ -z "${USE_EESSI_SOFTWARE_STACK}" ]; then
    export USE_EESSI_SOFTWARE_STACK=False
fi

if [ -z "${RFM_CONFIG_FILES}" ]; then
    export RFM_CONFIG_FILES="${TEMPDIR}/configs/config/vsc_hortense.py"
fi

if [ -z "${UNSET_MODULEPATH}" ]; then
    export UNSET_MODULEPATH=False
fi
