set -ex

SCRIPT_DIR=$(dirname "$0")
REPO_DIR=$(realpath ${SCRIPT_DIR}/..)

pushd ${REPO_DIR}/verification

make clean
cargo xtask bootstrap --restart
make compile
make lock-protocol

popd
