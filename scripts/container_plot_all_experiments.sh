set -ex

SCRIPT_DIR=$(dirname "$0")
REPO_DIR=$(realpath ${SCRIPT_DIR}/..)
OUTPUT_DIR=${REPO_DIR}/experiment_outputs
PLOT_SCRIPTS_DIR=${SCRIPT_DIR}/plot_scripts

python3 ${PLOT_SCRIPTS_DIR}/plot_intro_two_micro.py
python3 ${PLOT_SCRIPTS_DIR}/plot_macro_all.py
python3 ${PLOT_SCRIPTS_DIR}/plot_macro_notc.py
python3 ${PLOT_SCRIPTS_DIR}/plot_macro_single.py
python3 ${PLOT_SCRIPTS_DIR}/plot_macro_tc.py
python3 ${PLOT_SCRIPTS_DIR}/plot_micro_scale.py
python3 ${PLOT_SCRIPTS_DIR}/plot_micro_single.py
python3 ${PLOT_SCRIPTS_DIR}/plot_parsec_multi.py
