#!/bin/bash -e
#Writon by Kun

function run_with_n_cores(){
    set_args=$1
    startTime_s=`date +%s`

    FREQUENCYS=("2.0Ghz" "2.2Ghz" "2.4Ghz" "2.6Ghz" "2.8Ghz" "3.0Ghz" "3.2Ghz" "3.4Ghz" "3.6Ghz" "3.8Ghz")
    for FREQUENCY in ${FREQUENCYS[@]}
    do
        for i in {1..3}
        do
            echo "Setting frequency-${FREQUENCY}"
            sudo cpupower frequency-set -u $FREQUENCY >/dev/null ;sudo cpupower frequency-set -d $FREQUENCY >/dev/null
            echo "ending frequency-${FREQUENCY}"
            # echo "Restart docker"
            # sudo systemctl restart docker
            # echo "ending{$i}"
            pwd
            echo ${set_args}
            ./ctest.sh -R pkm --set "${set_args}" -V  --loop=1 --reuse-sut
            echo "Current {$i} frequency-${FREQUENCY}"
            current_policy="$( sudo cpupower frequency-info | grep 'current policy' | awk -F ":" '{print $2}' )"
            echo "Current frequency policy: ${current_policy}"
            echo sleep 1m
        done
    done

    endTime_s=`date +%s`

    sumTime=$(( $endTime_s - $startTime_s ))

    echo "Total:${sumTime} seconds"
}

# function foo(){
#     echo in foo cores=$1
# }

if [ "$#" -eq 0 ]; then
    echo "Please pass 'emr' or 'spr' platform"
    exit 1
fi

platform=$1
base_dir="report"
if [ ${platform} == "emr" ] || [ ${platform} == "EMR" ]; then
    emr_dir=${base_dir}/${platform}
    mkdir -p ${emr_dir}
    for precision in "bloat16" "woq_int8" "static_int8"
    do
        
        set_args="INPUT_TOKENS=1024/OUTPUT_TOKENS=128/PRECISION=${precision}"
        run_with_n_cores ${set_args} 2>&1 | tee ${emr_dir}/c_${precision}.log
    done
elif [ ${platform} == "spr" ] || [ ${platform} == "SPR" ]; then
    spr_dir=${base_dir}/${platform}
    mkdir -p ${spr_dir}
    for cores in 50 51 52 53 54 56
    do
        for precision in "bloat16" "woq_int8" "static_int8"
        do  
            set_args="INPUT_TOKENS=1024/OUTPUT_TOKENS=128/CORES_PER_INSTANCE=${cores}/PRECISION=${precision}"
            run_with_n_cores ${set_args} 2>&1 | tee ${spr_dir}/c_${precision}_${cores}.log
        done
    done
else
   exit 1
fi
