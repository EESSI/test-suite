# Configurable items
if [ -z "${REFRAME_ARGS}" ]; then
   REFRAME_ARGS="--tag CI --tag 1_node|2_nodes"
fi
# For now, software.eessi.io is not yet deployed on login nodes of the AWS MC cluster
if [ -z "${EESSI_CVMFS_REPO}" ]; then
   EESSI_CVMFS_REPO="/cvmfs/pilot.eessi-hpc.org"
fi
