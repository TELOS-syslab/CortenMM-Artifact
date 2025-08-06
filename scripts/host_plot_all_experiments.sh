set -ex

SCRIPT_DIR=$(dirname "$0")
REPO_DIR=$(realpath ${SCRIPT_DIR}/..)

docker run \
    -it --rm --privileged --network=host --device=/dev/kvm \
    --name cortenmm-ae \
    -v ${REPO_DIR}:/root/asterinas \
    ghcr.io/telos-syslab/cortenmm-artifact-env:v2 \
    bash "./scripts/container_plot_all_experiments.sh"
