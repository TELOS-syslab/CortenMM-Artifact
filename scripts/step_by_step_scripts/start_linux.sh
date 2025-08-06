set -ex

# args: start_linux.sh [core_count]

CORE_COUNT=${1:-128}

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
IMG_SRC_DIR="$SCRIPT_DIR/../../cortenmm-adv/test"
INITRAMFS_PATH="$IMG_SRC_DIR/build/initramfs.cpio.gz"
BENCH_IMG_PATH="$IMG_SRC_DIR/build/bench_data.img"

if [ ! -f "$INITRAMFS_PATH" ] || [ ! -f "$BENCH_IMG_PATH" ]; then
    make build -C $IMG_SRC_DIR
fi

LINUX_KERNEL="/root/linux-6.13.8/bzImage"

# Disable unsupported ext2 features of Asterinas on Linux to ensure fairness
mke2fs -F -O ^ext_attr -O ^resize_inode -O ^dir_index ${BENCH_IMG_PATH}

/usr/local/qemu/bin/qemu-system-x86_64 \
    --no-reboot \
    -smp $CORE_COUNT \
    -m 256G \
    -machine q35,kernel-irqchip=split \
    -cpu host,migratable=off,-pcid,+x2apic \
    --enable-kvm \
    -kernel ${LINUX_KERNEL} \
    -initrd ${INITRAMFS_PATH} \
    -drive if=none,format=raw,id=x0,file=${BENCH_IMG_PATH} \
    -device virtio-blk-pci,bus=pcie.0,addr=0x6,drive=x0,serial=vext2,disable-legacy=on,disable-modern=off,queue-size=64,num-queues=1,config-wce=off,request-merging=off,write-cache=off,backend_defaults=off,discard=off,event_idx=off,indirect_desc=off,ioeventfd=off,queue_reset=off \
    -drive if=none,format=raw,id=x2,file=./test/build/bench_data.img \
    -device virtio-blk-pci,bus=pcie.0,addr=0x7,drive=x2,serial=vbench,disable-legacy=on,disable-modern=off,queue-size=64,num-queues=1,config-wce=off,request-merging=off,write-cache=off,backend_defaults=off,discard=off,event_idx=off,indirect_desc=off,ioeventfd=off,queue_reset=off \
    -append 'console=ttyS0 rdinit=/usr/bin/busybox quiet mitigations=off hugepages=0 transparent_hugepage=never SHELL=/bin/sh LOGNAME=root HOME=/ USER=root PATH=/bin:/benchmark -- sh -l' \
    -qmp tcp:127.0.0.1:${QMP_PORT-9889},server,nowait \
    -nographic