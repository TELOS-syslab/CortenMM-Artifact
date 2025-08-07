{ lib, stdenv, fetchFromGitHub, hostPlatform, writeClosure, busybox, apps
, linux_vdso, benchmark, syscall, jdk21_headless }:
let
  etc = lib.fileset.toSource {
    root = ./../src/etc;
    fileset = ./../src/etc;
  };
  host_shared_libs = builtins.path {
    name = "host-shared-libs";
    path = "/lib/x86_64-linux-gnu";
  };
  host_usr_bin = builtins.path {
    name = "host-usr-bin";
    path = "/usr/bin";
  };
  all_pkgs = [ busybox etc linux_vdso ]
    ++ lib.optionals (apps != null) [ apps.package ]
    ++ lib.optionals (benchmark != null) [ benchmark.package ]
    ++ lib.optionals (syscall != null) [ syscall.package ];
in stdenv.mkDerivation {
  name = "initramfs";
  buildCommand = ''
    mkdir -p $out/{dev,etc,root,usr,opt,tmp,var,proc,sys}
    mkdir -p $out/{benchmark,test,ext2,exfat}
    mkdir -p $out/usr/{bin,sbin,lib,lib64,local}
    ln -sfn usr/bin $out/bin
    ln -sfn usr/sbin $out/sbin
    ln -sfn usr/lib $out/lib
    ln -sfn usr/lib64 $out/lib64
    cp -r ${busybox}/bin/* $out/bin/

    # Install JDK 21 headless
    mkdir -p $out/usr/lib
    mkdir -p $out/usr/bin
    cp -r ${jdk21_headless} $out/usr/lib/jvm

    mkdir -p $out/usr/lib/x86_64-linux-gnu
    ${lib.optionalString hostPlatform.isx86_64 ''
      cp -r ${linux_vdso}/vdso64.so $out/usr/lib/x86_64-linux-gnu/vdso64.so
    ''}
    ${lib.optionalString hostPlatform.isRiscV64 ''
      cp -r ${linux_vdso}/riscv64-vdso.so $out/usr/lib/x86_64-linux-gnu/vdso64.so
    ''}

    cp -r ${etc}/* $out/etc/

    ${lib.optionalString (apps != null) ''
      cp -r ${apps.package}/* $out/test/
    ''}

    ${lib.optionalString (benchmark != null) ''
      cp -r "${benchmark.package}"/* $out/benchmark/
    ''}

    ${lib.optionalString (syscall != null) ''
      cp -r "${syscall.package}"/opt/* $out/opt/
    ''}

    # FIXME: Build gvisor syscall test & parsec with nix to avoid manual library copying.
    cp -L ${host_shared_libs}/ld-linux-x86-64.so.2 $out/lib64/ld-linux-x86-64.so.2
    cp -L ${host_shared_libs}/libstdc++.so.6 $out/lib/x86_64-linux-gnu/libstdc++.so.6
    cp -L ${host_shared_libs}/libgcc_s.so.1 $out/lib/x86_64-linux-gnu/libgcc_s.so.1
    cp -L ${host_shared_libs}/libc.so.6 $out/lib/x86_64-linux-gnu/libc.so.6
    cp -L ${host_shared_libs}/libm.so.6 $out/lib/x86_64-linux-gnu/libm.so.6
    cp -L ${host_shared_libs}/libdb-5.3.so $out/lib/x86_64-linux-gnu/libdb-5.3.so
    cp -L ${host_shared_libs}/libgomp.so.1.0.0 $out/lib/x86_64-linux-gnu/libgomp.so.1
    cp -L ${host_shared_libs}/libtcmalloc_minimal.so.4 $out/lib/x86_64-linux-gnu/libtcmalloc_minimal.so.4
    cp -L ${host_shared_libs}/libtinfo.so.6.3 $out/lib/x86_64-linux-gnu/libtinfo.so.6

    cp ${host_usr_bin}/bash $out/usr/bin/bash

    # Use `writeClosure` to retrieve all dependencies of the specified packages.
    # This will generate a text file containing the complete closure of the packages,
    # including the packages themselves.
    # The output of `writeClosure` is equivalent to `nix-store -q --requisites`.
    mkdir -p $out/nix/store
    pkg_path=${lib.strings.concatStringsSep ":" all_pkgs}
    while IFS= read -r dep_path; do
      if [[ "$pkg_path" == *"$dep_path"* ]]; then
        continue
      fi
      cp -r $dep_path $out/nix/store/
    done < ${writeClosure all_pkgs}
  '';
}
