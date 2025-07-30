#!/bin/bash

# 1. 返回上两级目录
cd ../..

# 2. 复制 microbenchmark/map.c 到当前目录
cp microbenchmark/map.c map.c

# 3. 编译 map.c 生成 map.o
PATH=/root/nrk/target/x86_64-nrk-none/debug/build/rumpkernel-c3fc831e341ffbb3/out/rumprun/bin:/root/asterinas/target/bin:/usr/local/grub/bin:/usr/local/qemu/bin:/root/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
x86_64-rumprun-netbsd-gcc -O2 -Wall -DLUA_ANSI -DENABLE_CJSON_GLOBAL -DREDIS_STATIC='' -I/root/nrk/target/x86_64-nrk-none/debug/build/rkapps-f2e7af59c747fb81/out/pkgs/include -o map.o map.c
if [ $? -ne 0 ]; then
    echo "Error during compilation. Stopping script."
    exit 1
fi

# 4. 使用 rumprun-bake 构建 map
PATH=/root/nrk/target/x86_64-nrk-none/debug/build/rumpkernel-c3fc831e341ffbb3/out/rumprun/bin:/root/asterinas/target/bin:/usr/local/grub/bin:/usr/local/qemu/bin:/root/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
RUMPRUN_TOOLCHAIN_TUPLE=x86_64-rumprun-netbsd rumprun-bake nrk_generic map map.o
if [ $? -ne 0 ]; then
    echo "Error during rumprun-bake. Stopping script."
    exit 1
fi

# 5. 进入 nrk/kernel 目录
cd nrk/kernel

# 6. 运行 Python 脚本
# python3 run.py --nic e1000 --cmd "log=trace init=redis.bin" --mods rkapps --ufeatures "rkapps:redis" --qemu-settings="-m 10G" --qemu-cores=1 > output.log 2>&1
python3 run.py --nic e1000 --cmd "log=trace init=redis.bin" --mods rkapps --ufeatures "rkapps:redis" --qemu-settings="-m 10G" --qemu-cores=8 --qemu-affinity []
