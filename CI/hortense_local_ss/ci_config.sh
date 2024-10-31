# Configurable items
if [ -z "${REFRAME_ARGS}" ]; then
    REFRAME_ARGS="--tag CI --tag 1_node|2_nodes --system hortense:cpu_rome_256gb"
fi

if [ -z "${UNSET_MODULEPATH}" ]; then
    export UNSET_MODULEPATH=False
fi

if [ -z "${USE_EESSI_SOFTWARE_STACK}" ]; then
    export USE_EESSI_SOFTWARE_STACK=False
fi

if [ -z "${RFM_CONFIG_FILES}" ]; then
    export RFM_CONFIG_FILES="/dodrio/scratch/users/vsc46128/vsc_hortense.py"
fi
