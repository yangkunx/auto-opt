#!/bin/bash
#Writon by Kun

# VARs
HARDWARE_PLATFORM="spr"
PRECISIONS="bfloat16"
BATCH_SIZES="1"
LOOP=1
CORES="56"
FREQUENCYS="3.8"
DRY_RUN=false

function usage() {
    cat << EOM
    Usage: $(basename "$0") [OPTION]...
    -h the Hardware platform of run case, default is "spr", eg: [-h "emr"].
    -l Run the case sequentially, default is "1", eg: [-l "2"].
    -p run precison, default is "bfloat16", eg: [-p "bfloat16 woq_int8"].
    -b run batch_size, default is "1", eg: [-b "1 2 4 8"].
    -c run core, default is "56", eg: [-c "50 52 54 56"].
    -f run frequencys, default is "3.8", eg: [-f "2.0 2.4 2.8 3.8"].
    -s pass the args to ctest.sh, eg: [-s "INPUT_TOKENS=1024/OUTPUT_TOKENS=128"].
    -d Generate he testcase configurations and then exit, default is "false", eg: [-d].
EOM
    exit 0
}

function process_args() {
    while getopts "c:h:l:p:b:p:f:s:d" opt; do
        case $opt in
        h) HARDWARE_PLATFORM="$OPTARG";;
        l) LOOP="$OPTARG";;
        p) PRECISIONS="$OPTARG" ;;
        b) BATCH_SIZES="$OPTARG";;
        c) CORES="$OPTARG";;
        f) FREQUENCYS="$OPTARG";;
        s) SET_ARGS="$OPTARG";;
        d) DRY_RUN=true ;;
        *) usage exit 1;;
        esac
    done
}

function _print_args(){
    echo "$1"
    echo "HARDWARE_PLATFORM: ${HARDWARE_PLATFORM}"
    echo "PRECISIONS: ${PRECISIONS}"
    echo "BATCH_SIZES: ${BATCH_SIZES}" 
    echo "LOOP: ${LOOP}"
    echo "CORES: ${CORES}"
    echo "FREQUENCYS: ${FREQUENCYS}"
    echo "SET_ARGS: ${SET_ARGS}"
    echo "DRY_RUN: ${DRY_RUN}"
    echo "$2"
}

function run_with_n_cores(){
    process_args "$@"
    # _print_args "run_with_n_cores开始" "run_with_n_cores结束" 
    startTime_s=`date +%s`

    for FRE in ${FREQUENCYS}
    do
        for i in $(seq 1 ${LOOP})
        do   
            FREQUENCY=${FRE}"Ghz"
            echo $DRY_RUN
            if [ "$DRY_RUN" = true ]; then
                echo "test"
                echo "Current $i-${CORE}-${PRECISION}-${FREQUENCY}-${BATCH_SIZE}"
                echo "Running cmd: ./ctest.sh -R pkm --set "${SET_ARGS}" -V  --loop=1 --reuse-sut"
            else
                echo "Setting frequency-${FREQUENCY}"
                sudo cpupower frequency-set -u ${FREQUENCY} >/dev/null ;sudo cpupower frequency-set -d ${FREQUENCY} >/dev/null
                echo "ending frequency-${FREQUENCY}"

                ./ctest.sh -R pkm --set "${SET_ARGS}" -V  --loop=1 --reuse-sut
                
                echo "Current $i-${CORE}-${PRECISION}-${FREQUENCY}-${BATCH_SIZE}"
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
    for PRECISION in ${PRECISIONS}
    do
        for BATCH_SIZE in ${BATCH_SIZES}
        do
            if [[ ${HARDWARE_PLATFORM} == "emr" ]]; then
                output_dir=${base_dir}/${HARDWARE_PLATFORM}
                mkdir -p ${output_dir}
                SET_ARGS="INPUT_TOKENS=1024/OUTPUT_TOKENS=128/USE_DEEPSPEED=True/PRECISION=${PRECISION}/BATCH_SIZE=${BATCH_SIZE}"
                output_log=${output_dir}/c_56_${PRECISION}_${BATCH_SIZE}.log
                run_with_n_cores -s "${SET_ARGS}" -l "${LOOP}" -f "${FREQUENCYS}" -p "${PRECISION}" -b "${BATCH_SIZES}" 2>&1 | tee ${output_log}
            elif [[ ${HARDWARE_PLATFORM} == "spr" ]]; then
                output_dir=${base_dir}/${HARDWARE_PLATFORM}
                mkdir -p ${output_dir}
                for CORE in $CORES
                do
                    SET_ARGS="INPUT_TOKENS=1024/OUTPUT_TOKENS=128/CORES_PER_INSTANCE=${CORE}/PRECISION=${PRECISION}/BATCH_SIZE=${BATCH_SIZE}"
                    output_log=${output_dir}/c_${CORE}_${PRECISION}_${BATCH_SIZE}.log
                    run_with_n_cores -s "${SET_ARGS}" -l "${LOOP}" -c "${CORE}" -f "${FREQUENCYS}" -p "${PRECISION}" -b "${BATCH_SIZES}" 2>&1 | tee ${output_log}
                done
            else
                exit 1
            fi
        
        done
        
    done
}

process_args "$@"
_print_args "脚本传入参数打印开始。。。。。。。" "脚本传入参数打印结束！！！！！！" 

HARDWARE_PLATFORM=$(echo $HARDWARE_PLATFORM | tr '[:upper:]' '[:lower:]')
run_with_platform -h ${HARDWARE_PLATFORM} -p "${PRECISIONS}" -c "${CORES}" -l ${LOOP} -f "${FREQUENCYS}" -b "${BATCH_SIZES}"
