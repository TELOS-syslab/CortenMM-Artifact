#!/bin/bash

# metisbench.sh

set -e

export QMP_PORT=3336

# When the `NCPU` in `param.h` is greater than 128, `./metis_wrmem` cannot run.
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PARAM_H="$SCRIPT_DIR/../param.h"
if [ -f "$PARAM_H" ]; then
  sed -i 's/384   \/\/ HW_qemu maximum number of CPUs/128   \/\/ HW_qemu maximum number of CPUs/' "$PARAM_H"
fi

NR_CPUS=128

PIN_CPU_SCRIPT="$SCRIPT_DIR/pin_cpu.py"
TEST_RESULTS_DIR="$SCRIPT_DIR/../test_results"
TMUX_SESSION_NAME="metisbench_session"
mkdir -p "$TEST_RESULTS_DIR"

START_VM_CMD="make qemu QEMUSMP=$NR_CPUS QEMUMEM=240G"
BENCH_OUTPUT_FILE="$TEST_RESULTS_DIR/radix_metis_output.txt"
EXIT_COMMAND="; echo Finish."

pushd "$SCRIPT_DIR/.."

run_metisbench() {
    # Usage: run_metisbench <command>
    COMMAND=$1
    COMMAND+=$EXIT_COMMAND

    ASTER_SESSION_KEYS=$START_VM_CMD
    ASTER_SESSION_KEYS+=" 2>&1 | tee -a ${BENCH_OUTPUT_FILE}"
    # Exit session when the command finishes
    ASTER_SESSION_KEYS+="; exit"

    for try_id in $(seq 1 10); do
        tmux new-session -d -s ${TMUX_SESSION_NAME}

        echo "Starting VM in tmux session ${TMUX_SESSION_NAME}:0 with command:"
        echo "# $ASTER_SESSION_KEYS"
        tmux send-keys -t ${TMUX_SESSION_NAME}:0 "$ASTER_SESSION_KEYS" Enter

        echo "Wait for \"$\" shell prompt to appear in $BENCH_OUTPUT_FILE"
        while ! tail -n 1 $BENCH_OUTPUT_FILE | grep -q '\$'; do
            echo "Waiting..."
            sleep 5
        done

        # Bind cores
        echo "Binding cores to VM"
        python3 $PIN_CPU_SCRIPT $QMP_PORT $NR_CPUS

        # Run the metisbenchmark
        echo "Running metisbenchmark command: $COMMAND"
        tmux send-keys -t ${TMUX_SESSION_NAME}:0 "${COMMAND}" Enter

        echo "Wait for \"Finish.\" or \"Abort.\" to appear in $BENCH_OUTPUT_FILE"
        finished=0
        waiting_msg="Waiting..."
        while true; do
            last_two_lines=$(tail -n 2 "$BENCH_OUTPUT_FILE")
            if echo "$last_two_lines" | grep -q '^Finish.'; then
                finished=1
                break
            elif echo "$last_two_lines" | grep -q 'Abort.'; then
                finished=0
                break
            fi

            # Wait for at most 200 seconds.
            echo $waiting_msg
            waiting_msg="$waiting_msg."
            if [ ${#waiting_msg} -gt 50 ]; then
                finished=-1
                break
            fi
            sleep 5
        done

        if [ "$finished" -eq 1 ]; then
            kill -15 $(pgrep qemu)
            echo -e "\nmetisbench done." >> $BENCH_OUTPUT_FILE
            sleep 5
            break
        elif [ "$finished" -eq 0 ]; then
            echo "Found Abort, retrying..."
            sleep 5
        elif [ "$finished" -eq -1 ]; then
            echo "Stuck, retrying..."
            kill -15 $(pgrep qemu)
            sleep 5
        fi
    done
}

if [ -f "$BENCH_OUTPUT_FILE" ]; then
    rm "$BENCH_OUTPUT_FILE"
fi

THREAD_COUNTS=( 1 2 4 8 16 32 64 128 )
for THREAD_COUNT in "${THREAD_COUNTS[@]}"; do
    run_metisbench "./metis_wrmem -s 1600 -p $THREAD_COUNT -a 8388608"
done

unset QMP_PORT

popd
