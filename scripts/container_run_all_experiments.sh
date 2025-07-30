set -ex

SCRIPT_DIR=$(dirname "$0")
REPO_DIR=$(realpath ${SCRIPT_DIR}/..)

# --------------------------------------------------------------------------- #

# a1
${SCRIPT_DIR}/step_by_step_scripts/microbench.sh corten-rw

# a2
${SCRIPT_DIR}/step_by_step_scripts/microbench.sh corten-adv

# a3
${SCRIPT_DIR}/step_by_step_scripts/microbench.sh linux

# a4 RadixVM

# a5 NrOS

# --------------------------------------------------------------------------- #

# b1
${SCRIPT_DIR}/step_by_step_scripts/macrojvm.sh corten-rw

# b2
${SCRIPT_DIR}/step_by_step_scripts/macrojvm.sh corten-adv

# b3
${SCRIPT_DIR}/step_by_step_scripts/macrojvm.sh linux

# --------------------------------------------------------------------------- #

# c1
${SCRIPT_DIR}/step_by_step_scripts/macrometis.sh corten-rw

# c2
${SCRIPT_DIR}/step_by_step_scripts/macrometis.sh corten-adv

# c3
${SCRIPT_DIR}/step_by_step_scripts/macrometis.sh linux

# c4 RadixVM

# --------------------------------------------------------------------------- #

# d1
${SCRIPT_DIR}/step_by_step_scripts/macrodedup.sh corten-rw pt

# d2
${SCRIPT_DIR}/step_by_step_scripts/macrodedup.sh corten-adv pt

# d3
${SCRIPT_DIR}/step_by_step_scripts/macrodedup.sh corten-adv tc

# d4
${SCRIPT_DIR}/step_by_step_scripts/macrodedup.sh linux pt

# d5
${SCRIPT_DIR}/step_by_step_scripts/macrodedup.sh linux tc

# --------------------------------------------------------------------------- #

# e1
${SCRIPT_DIR}/step_by_step_scripts/macropsearchy.sh corten-rw pt

# e2
${SCRIPT_DIR}/step_by_step_scripts/macropsearchy.sh corten-adv pt

# e3
${SCRIPT_DIR}/step_by_step_scripts/macropsearchy.sh corten-adv tc

# e4
${SCRIPT_DIR}/step_by_step_scripts/macropsearchy.sh linux pt

# e5
${SCRIPT_DIR}/step_by_step_scripts/macropsearchy.sh linux tc

# --------------------------------------------------------------------------- #

# f1
${SCRIPT_DIR}/step_by_step_scripts/allparsec.sh corten-rw

# f2
${SCRIPT_DIR}/step_by_step_scripts/allparsec.sh corten-adv

# f3
${SCRIPT_DIR}/step_by_step_scripts/allparsec.sh linux
