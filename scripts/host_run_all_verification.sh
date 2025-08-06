set -ex

SCRIPT_DIR=$(dirname "$0")
REPO_DIR=$(realpath ${SCRIPT_DIR}/..)

docker run \
    --rm --privileged --network=host --device=/dev/kvm \
    --name cortenmm-ae \
    -v ${REPO_DIR}:/root/asterinas \
    ghcr.io/telos-syslab/cortenmm-artifact-env:v4 \
    bash "./scripts/container_run_all_verification.sh"
