#!/bin/bash

set -e

# usage: macrometis.sh [linux|corten-rw|corten-adv] [aster_breakdown]

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
BENCH_SCRIPT="$SCRIPT_DIR/bench.sh"

SYS_NAME=$1

if [ "$SYS_NAME" != "linux" ] && [ "$SYS_NAME" != "corten-rw" ] && [ "$SYS_NAME" != "corten-adv" ]; then
    echo "Usage: $0 <linux|corten-rw|corten-adv> [aster_breakdown]"
    exit 1
fi

DO_ASTER_BREAKDOWN=$2
if [ "$SYS_NAME" == "linux" ]; then
    DO_ASTER_BREAKDOWN=""
fi

BENCH_OUTPUT_FILE="macrometis_${SYS_NAME}_$(date +%Y%m%d%H%M%S).log"

THREAD_COUNTS=(1 2 4 8 16 32 64 128 192 256 320 384)
NUM_HOST_CPUS=$(nproc)
for THREAD_COUNT in "${THREAD_COUNTS[@]}"; do
    if [ $THREAD_COUNT -gt $NUM_HOST_CPUS ]; then
        echo "$THREAD_COUNT is greater than the number of host CPUs ($NUM_HOST_CPUS), skipping..."
        continue
    fi
    export NR_CPUS=$THREAD_COUNT
    $BENCH_SCRIPT $SYS_NAME $BENCH_OUTPUT_FILE "/test/corten_benchmetis.sh $THREAD_COUNT $DO_ASTER_BREAKDOWN"
done
