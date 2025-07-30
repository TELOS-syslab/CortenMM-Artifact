# /usr/local/qemu/bin/qemu-system-x86_64 \
#     --no-reboot \
#     -smp 128 \
#     -m 96G \
#     -machine q35,kernel-irqchip=split \
#     -cpu Icelake-Server,-pcid,+x2apic \
#     --enable-kvm \
#     -kernel ${LINUX_KERNEL} \
#     -initrd test/build/initramfs.cpio.gz \
#     -drive if=none,format=raw,id=x0,file=test/build/ext2.img \
#     -device virtio-blk-pci,bus=pcie.0,addr=0x6,drive=x0,serial=vext2,disable-legacy=on,disable-modern=off,queue-size=64,num-queues=1,config-wce=off,request-merging=off,write-cache=off,backend_defaults=off,discard=off,event_idx=off,indirect_desc=off,ioeventfd=off,queue_reset=off \
#     -netdev user,id=net01,hostfwd=tcp::11211-:11211 \
#     -qmp tcp:127.0.0.1:${QMP_PORT:-19889},server,nowait \
#     -device virtio-net-pci,netdev=net01,disable-legacy=on,disable-modern=off,mrg_rxbuf=off,ctrl_rx=off,ctrl_rx_extra=off,ctrl_vlan=off,ctrl_vq=off,ctrl_guest_offloads=off,ctrl_mac_addr=off,event_idx=off,queue_reset=off,guest_announce=off,indirect_desc=off \
#     -append 'console=ttyS0 rdinit=/usr/bin/busybox quiet mitigations=off hugepages=0 transparent_hugepage=never SHELL=/bin/sh LOGNAME=root HOME=/ USER=root PATH=/bin:/benchmark -- sh -l' \
#     -nographic

/usr/bin/env qemu-system-x86_64 \
    --no-reboot \
    -smp 128 \
    -m 96G \
    -machine q35,kernel-irqchip=split \
    -cpu Icelake-Server,-pcid,+x2apic \
    --enable-kvm \
    -device virtio-blk-pci,bus=pcie.0,addr=0x6,drive=x0,serial=vext2,disable-legacy=on,disable-modern=off,queue-size=64,num-queues=1,config-wce=off,request-merging=off,write-cache=off,backend_defaults=off,discard=off,event_idx=off,indirect_desc=off,ioeventfd=off,queue_reset=off \
    -netdev user,id=net01,hostfwd=tcp::11211-:11211 \
    -qmp tcp:127.0.0.1:${QMP_PORT:-19889},server,nowait \
    -device virtio-net-pci,netdev=net01,disable-legacy=on,disable-modern=off,mrg_rxbuf=off,ctrl_rx=off,ctrl_rx_extra=off,ctrl_vlan=off,ctrl_vq=off,ctrl_guest_offloads=off,ctrl_mac_addr=off,event_idx=off,queue_reset=off,guest_announce=off,indirect_desc=off \
    -drive if=pflash,format=raw,file=/root/nrk/bootloader/OVMF_CODE.fd,readonly=on \
    -drive if=pflash,format=raw,file=/root/nrk/bootloader/OVMF_VARS.fd,readonly=on \
    -drive if=none,format=raw,file=fat:rw:/root/nrk/target/x86_64-uefi/release/esp,id=esp \
    -device ahci,id=ahci,multifunction=on \
    -device ide-hd,bus=ahci.0,drive=esp \
    -device isa-debug-exit,iobase=0xf4,iosize=0x04 \
    -device e1000,netdev=n1,mac=56:b4:44:e9:62:d0 \
    -netdev tap,id=n1,script=no,ifname=tap0 \
    -name nrk,debug-threads=on \
    -nographic \
    -display none \
    -serial stdio

# Do the following in VM:
# Mount necessary fs
# mount -t devtmpfs devtmpfs /dev
# Enable network
# ip link set lo up
# ip link set eth0 up
# ifconfig eth0 10.0.2.15
# Mount ext2
# mount -t ext2 /dev/vda /ext2


# Original command in NrOS:
/usr/bin/env qemu-system-x86_64 -no-reboot -enable-kvm -cpu host,migratable=no,+invtsc,+tsc,+x2apic,+fsgsbase -display none -serial stdio -drive if=pflash,format=raw,file=/root/nrk/bootloader/OVMF_CODE.fd,readonly=on -drive if=pflash,format=raw,file=/root/nrk/bootloader/OVMF_VARS.fd,readonly=on -device ahci,id=ahci,multifunction=on -drive if=none,format=raw,file=fat:rw:/root/nrk/target/x86_64-uefi/release/esp,id=esp -device ide-hd,bus=ahci.0,drive=esp -device isa-debug-exit,iobase=0xf4,iosize=0x04 -device e1000,netdev=n1,mac=56:b4:44:e9:62:d0 -netdev tap,id=n1,script=no,ifname=tap0 -smp 96,sockets=1 -name nrk,debug-threads=on -m 10G