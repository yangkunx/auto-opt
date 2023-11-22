#!/bin/bash
#Writon by Kun

# VARs
HARDWARE_PLATFORM="spr"
PRECISIONS=(bfloat16 woq_int8 static_int8)
BATCH_SIZES="1 4 8 16"
LOOP=1
DRY_RUN=false
CORES="50 51 52 53 54 56"
FREQUENCYS="2.2 2.2 2.4 2.6 2.8 3.0 3.2 3.4 3.6 3.8"

function usage() {
    cat << EOM
    Usage: $(basename "$0") [OPTION]...
    -h the Hardware platform of run case, default is "spr"
    -l Run the case sequentially, default is "1"
    -p the array of run precison, default is "("bfloat16" "woq_int8" "static_int8")"
    -b the array of run batch_size, default is "("1")"
    -c the array of core, default is "(50 51 52 53 54 56)"
    -f the array of frequencys, default is "("2.0 2.2 2.4 2.6 2.8 3.0 3.2 3.4 3.6 3.8")"
    -s pass the args to ctest.sh
    -d Generate he testcase configurations and then exit.
EOM
    exit 0
}

function process_args() {
    #  BATCH_SIZE CORES FREQUENCYS 
    unset -v PRECISIONS
    while getopts "c:h:l:p:b:p:f:s:d" opt; do
        case $opt in
        h) HARDWARE_PLATFORM="$OPTARG";;
        l) LOOP="$OPTARG";;
        p) PRECISIONS="($OPTARG)" ;;
        b) BATCH_SIZE="($OPTARG)";;
        c) CORES="($OPTARG)";;
        f) FREQUENCYS="($OPTARG)";;
        s) SET_ARGS="$OPTARG";;
        d) DRY_RUN=true ;;
        *) usage;;
        esac
    done
}

function _print_args(){
    echo $1
    echo HARDWARE_PLATFORM: ${HARDWARE_PLATFORM} 
    echo PRECISIONS: ${PRECISIONS} 
    echo BATCH_SIZE: ${BATCH_SIZE} 
    echo LOOP: ${LOOP}
    echo CORE: ${CORE}
    echo FREQUENCYS: ${FREQUENCYS}
    echo SET_ARGS: ${SET_ARGS}
    echo DRY_RUN: ${DRY_RUN}
    echo $2
}

function run_with_n_cores(){
    process_args "$@"
    # _print_args "run_with_n_cores开始" "run_with_n_cores结束" 
    startTime_s=`date +%s`

    for FREQUENCY in "${FREQUENCYS[@]}"
    do
        for i in $(seq 1 ${LOOP})
        do   
            FREQUENCY=${FREQUENCY}"Ghz"
            if $DRY_RUN; then
                echo ${i}-${CORE}-${PRECISION}-${FREQUENCY}
                #echo "Running cmd: ./ctest.sh -R pkm --set "${SET_ARGS}" -V  --loop=1 --reuse-sut"
            else
                echo "Setting frequency-${FREQUENCY}"
                sudo cpupower frequency-set -u ${FREQUENCY} >/dev/null ;sudo cpupower frequency-set -d ${FREQUENCY} >/dev/null
                echo "ending frequency-${FREQUENCY}"
                #./ctest.sh -R pkm --set "${SET_ARGS}" -V  --loop=1 --reuse-sut
                echo "running"
                echo "Current {$i} frequency-${FREQUENCY}"
                current_policy="$( sudo cpupower frequency-info | grep 'current policy' | awk -F ":" '{print $2}' )"
                echo "Current frequency policy: ${current_policy}"
                echo sleep 1m
            fi
            
        done
    done

    endTime_s=`date +%s`

    sumTime=$(( $endTime_s - $startTime_s ))

    echo "Total:${sumTime} seconds"
}


function run_with_platform(){
    process_args "$@"
    # _print_args "run_with_platform开始" "run_with_platform结束" 
    base_dir="report"
    echo "${PRECISIONS[@]}"
    for precision in "${PRECISIONS[@]}"
    do
        echo ${precision}
        # if [ ${HARDWARE_PLATFORM} == "emr" ]; then
        #     output_dir=${base_dir}/${HARDWARE_PLATFORM}
        #     mkdir -p ${output_dir}
        #     SET_ARGS="INPUT_TOKENS=1024/OUTPUT_TOKENS=128/USE_DEEPSPEED=True/PRECISION=${PRECISION}"
        #     output_log=${output_dir}/c_${PRECISION}.log
        #     # run_with_n_cores -s ${SET_ARGS} -l ${LOOP} -f ${FREQUENCYS} 2>&1 | tee ${output_log}
        # elif [ ${HARDWARE_PLATFORM} == "spr" ]; then
        #     output_dir=${base_dir}/${HARDWARE_PLATFORM}
        #     mkdir -p ${output_dir}
        #     for CORE in "${CORES[@]}"
        #     do
        #         SET_ARGS="INPUT_TOKENS=1024/OUTPUT_TOKENS=128/CORES_PER_INSTANCE=${CORE}/PRECISION=${PRECISION}"
        #         output_log=${output_dir}/c_${PRECISION}_${CORE}.log
        #         #run_with_n_cores -s "${SET_ARGS}" -l "${LOOP}" -c "${CORE}" -f "${FREQUENCYS}" -p "${PRECISION}"  2>&1 | tee ${output_log}
        #     done
        # else
        #     exit 1
        # fi
        # echo "Input_args: ${set_args}"
        
    done
}


echo $@
process_args "$@"
# _print_args "外面开始" "外面结束" 

HARDWARE_PLATFORM=$(echo $HARDWARE_PLATFORM | tr '[:upper:]' '[:lower:]')
run_with_platform -h ${HARDWARE_PLATFORM} -p "${PRECISIONS}" -c "${CORES}" -l ${LOOP} -f "${FREQUENCYS}"

