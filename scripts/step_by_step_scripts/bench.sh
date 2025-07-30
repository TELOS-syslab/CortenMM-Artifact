
#!/bin/bash

# args: bench.sh [linux|corten-rw|corten-adv] [bench_output_file_name] [cmd_to_run_in_vm]
# envs: NR_CPUS CORTEN_RUN_ARGS

set -ex

export QMP_PORT=13336

NR_CPUS=${NR_CPUS:-$(nproc --all)}

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PIN_CPU_SCRIPT="$SCRIPT_DIR/pin_cpu.py"
TEST_RESULTS_DIR="$SCRIPT_DIR/../../experiment_outputs"
TMUX_SESSION_NAME="corten_experiment_session"
mkdir -p "$TEST_RESULTS_DIR"

BENCH_TARGET=$1
BENCH_OUTPUT_FILE_NAME=$2
COMMAND_IN_VM=$3

BENCH_OUTPUT_FILE="$TEST_RESULTS_DIR/$BENCH_OUTPUT_FILE_NAME"

if [ "$BENCH_TARGET" == "linux" ]; then
    START_VM_CMD="$SCRIPT_DIR/start_linux.sh $NR_CPUS"
    EXIT_COMMAND="; poweroff -f"
    pushd "$SCRIPT_DIR/../../cortenmm-adv"
elif [ "$BENCH_TARGET" == "corten-rw" ] || [ "$BENCH_TARGET" == "corten-adv" ]; then
    START_VM_CMD="make run SMP=$NR_CPUS MEM=240G RELEASE_LTO=1 $CORTEN_RUN_ARGS"
    EXIT_COMMAND="; exit"
    if [ "$BENCH_TARGET" == "corten-rw" ]; then
        pushd "$SCRIPT_DIR/../../cortenmm-rw"
    else
        pushd "$SCRIPT_DIR/../../cortenmm-adv"
    fi
else 
    echo "Unknown benchmark target: $BENCH_TARGET"
    exit 1
fi

COMMAND_IN_VM+=$EXIT_COMMAND

tmux new-session -d -s ${TMUX_SESSION_NAME}

ASTER_SESSION_KEYS=$START_VM_CMD
ASTER_SESSION_KEYS+=" 2>&1 | tee -a ${BENCH_OUTPUT_FILE}"
# Exit session when the command finishes
ASTER_SESSION_KEYS+="; exit"

echo "Starting VM in tmux session ${TMUX_SESSION_NAME}:0 with command:"
echo "# $ASTER_SESSION_KEYS"
tmux send-keys -t ${TMUX_SESSION_NAME}:0 "$ASTER_SESSION_KEYS" Enter

echo "Wait for \"~ \#\" shell prompt to appear in $BENCH_OUTPUT_FILE"
while [ ! -f "$BENCH_OUTPUT_FILE" ] || ! tail -n 1 "$BENCH_OUTPUT_FILE" | grep -q "~ #"; do
    echo "Waiting for the building process to complete..."
    sleep 5
done

# Bind cores
echo "Binding cores to VM"
python3 $PIN_CPU_SCRIPT $QMP_PORT $NR_CPUS

# Run the microbenchmark
echo "Running benchmark command: $COMMAND_IN_VM"
tmux select-window -t ${TMUX_SESSION_NAME}:0
tmux send-keys -t ${TMUX_SESSION_NAME}:0 "${COMMAND_IN_VM}" Enter

tmux attach -t ${TMUX_SESSION_NAME}:0

unset QMP_PORT

popd
