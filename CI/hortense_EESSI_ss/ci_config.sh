# Configurable items
if [ -z "${UNSET_MODULEPATH}" ]; then
    export UNSET_MODULEPATH=False
    module --force purge
fi

if [[ "$TEST_SUITE_PARTITION" == "GPU" ]]; then
    if [ -z "${SET_LOCAL_MODULE_ENV}"]; then
         export SET_LOCAL_MODULE_ENV=True
    fi
    if [ -z "${LOCAL_MODULES}"]; then
         export LOCAL_MODULES="env/slurm/dodrio/gpu_rome_a100"
         module use /cvmfs/software.eessi.io/versions/2023.06/software/linux/x86_64/amd/zen2/accel/nvidia/cc80/modules/all
    fi
fi

if [ -z "${REFRAME_ARGS}" ]; then
    REFRAME_ARGS="--tag CI --tag 1_core"
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
    export LOCAL_MODULES="env/slurm/dodrio/cpu_rome"
fi
