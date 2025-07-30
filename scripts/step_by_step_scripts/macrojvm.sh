#!/bin/bash

set -e

# usage: macrojvm.sh [linux|corten-rw|corten-adv] [aster_breakdown]

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

BENCH_OUTPUT_FILE="macrojvm_${SYS_NAME}_$(date +%Y%m%d%H%M%S).log"

THREAD_COUNTS=(1 2 4 8 16 32 64 128 192 256 320 384)
for THREAD_COUNT in "${THREAD_COUNTS[@]}"; do
    if [ $THREAD_COUNT -eq 320 ]; then
        export NR_CPUS=384
    else
        export NR_CPUS=$THREAD_COUNT
    fi
    export CORTEN_RUN_ARGS="FEATURES=mprotect_async_tlb"
    $BENCH_SCRIPT $SYS_NAME $BENCH_OUTPUT_FILE "/test/corten_benchjvm.sh $THREAD_COUNT $DO_ASTER_BREAKDOWN"
done
