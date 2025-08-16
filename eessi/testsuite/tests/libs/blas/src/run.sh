#!/bin/bash

# threading: st or mt
tsuf=$1

# Number of repeats per problem size.
nrepeats=$2

# Problem size range for single- and multithreaded execution.
# psr_st="100 1000 100"
# psr_mt="200 2000 200"
psr=$3

# Datatypes to test.
# test_dts="s d c z"
test_dts=$4

# Operations to test.
# test_ops="gemm_nn hemm_ll herk_ln trmm_llnn trsm_runn"
test_ops=$5

# The induced method to use ('auto', 'native', or '1m') for executing
# complex-domain level-3 operations.
ind="auto"

delay=0.1

# Implementations to test.
im=flexiblas

mkdir -p output

# Iterate over the datatypes.
for dt in ${test_dts}; do

    # Iterate over the operations.
    for op in ${test_ops}; do

        # Strip everything before the understore so that what remains is
        # the operation parameter string.
        oppars=${op##*_};

        # Strip everything after the understore so that what remains is
        # the operation name (sans parameter encoding).
        opname=${op%%_*}

        # Problem size range
        # psrvar="psr_${tsuf}"
        # psr=${!psrvar}

        # Construct the name of the test executable.
        exec_name="test_${opname}_${im}_${tsuf}.x"

        # Construct the name of the output file.
        out_file="output/${dt}${opname}_${oppars}_${im}.m"

        set -x
        ./${exec_name} -d ${dt} -c ${oppars} -i ${ind} -p "${psr}" -r ${nrepeats} ${qv} > ${out_file}
        set +x

        # Bedtime!
        sleep ${delay}

    done
done

