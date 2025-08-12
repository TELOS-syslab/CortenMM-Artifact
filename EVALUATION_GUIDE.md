# Artifact Evaluation Guide

## Overview

CortenMM's artifact includes, for each lock protocol (CortenMM-rw and CortenMM-adv),
 - the formal verification of the core implementation,
 - and the kernel that includes the CortenMM subsystem.

## Setup

An x86-64 machine with an arbitrary Linux install is suffice. The more cores the better. To avoid unstable results, it is recommended to disable turbo boost and hyperthreading. We've tested CortenMM on both an AMD machine with 384 cores (two Epyc 9965 processors) and an Intel machine with 128 cores (two Xeon Platinum 8592+ processors).

Please [install Docker](https://docs.docker.com/engine/install/) if your machine hasn't installed it. We have prepared a docker image (~29 GB) containing the running environment and the benchmark input data. Please pull it first.

```bash
docker pull ghcr.io/telos-syslab/cortenmm-artifact-env:v4.1
```

See [the difference between artifact image versions](./DOCKER_ENV_IMAGE_VERSIONS.md) if you want to use an older image version.

You can add your user to the `docker` user group to use the Docker commands and the automated scripts without `sudo`. Otherwise, please add `sudo` to run all the `host_` prefixed scripts and docker commands mentioned in this guide.

The code is not included in the docker container. Please clone this repository, and change the working directory into it.

```bash
git clone https://github.com/TELOS-syslab/CortenMM-Artifact.git
cd CortenMM-Artifact
```

Congratulations! You are all set. The following guide will assume that you are in this directory.

### *Playing the OS in the Container

Reading sections marked with "*" is not strictly neccessary. However it is better to follow them to

 1. do evaluations step by step instead of running them all by once,
 2. make changes or test other applications, or to
 3. debug if there would be platform-specific problems that are easy to solve.

The following command will start a container named `cortenmm-ae`; put you into the container's interactive shell (`-it` option); and mount the host's current directory inside the container (`-v option`). So that modifications (if any) to the downloaded repository in the host side can be directly seen and compiled in the container, which is convienient if you are using host side GUI editors like VSCode. Reproduction results can also be seen from the host's file explorer.

```bash
docker run --name cortenmm-ae -it --privileged --network=host --device=/dev/kvm -v $(pwd):/root/asterinas ghcr.io/telos-syslab/cortenmm-artifact-env:v4.1
```

In fact, the automated scripts use this technique. So your modifications will also effect the automated runs.

To halt your progress of evaluation, simply type `exit` to get out of the container. Execute `docker ps -a` to see current active containers. To resume, execute `docker start cortenmm-ae` if it is exited, and execute `docker exec -it cortenmm-ae bash` to regain the shell. To cleanup, do `docker stop cortenmm-ae` and `docker rm cortenmm-ae`.

We promise that all the automated scripts will not effect your host's settings.

## Reproducing Verification

This may take 3 to 10 minutes.

```bash
./scripts/host_run_all_verification.sh
```

If you see something like `verification results:: 806 verified, 0 errors`, you have successfully reproduced verification.

Running it still requires a good network connection (to Github and crates.io), since Rust will check and update dependencies. If you keep seeing `network failure seems to have happened`, `SSL error` or similar, you may try reproducing step-by-step so that you can retry certain steps.

### *Step by Step

Inside the docker container, at the path of `/root/asterinas`, follow these steps to do machine-checked verification.

Firstly, setup the environment. This command will download, update, compile and verify neccessary packages such as Z3 and Verus. It could take 3 to 10 minutes depending on your network connection and CPU speed.

```bash
cd verification
cargo xtask bootstrap
```

Secondly, the following commands will compile and verify the dependent packages (`aster_common` and `vstd_extra`). It should take around 10 seconds. 

```bash
make compile
```

Finally, compile and verify the lock protocols. It should take around 10 seconds.

```bash
make lock-protocol
```

### Verification Code Walkthrough

Please see [the verification walkthrough](./VERIFICATION_WALKTHROUGH.md) to understand our verfication efforts in a high level.

### Key Claim and Limitations

We claim that we have finished verification of

 1. the RCU based lock-protocol (`./verification/lock-protocol/src/exec/rcu`),
 2. the RW-lock based lock-protocol (`./verification/lock-protocol/src/exec/rw`),
 3. and the RCursor's page table operations (`./verification/lock-protocol/src/mm/page_table/cursor/mod.rs`).

These claims can be justified though [the verification walkthrough](./VERIFICATION_WALKTHROUGH.md).

Note that the artifact still has the following limitations, which are noted in the paper or considered trivial.

 - The verified code is ported to the kernel manually;
 - The interface that the rest of the kernel provides are unverified;
 - Some trivial numerical/bit operation proofs are admitted using lemmas.

## Reproducing Performance Evaluation Figures

This may take several hours.

```bash
./scripts/host_run_all_experiments.sh
```

After all the experiments are finished, you can generate all the figures via the following command.

```bash
./scripts/host_plot_all_experiments.sh
```

### *Step by Step

There are chances that the evaluation couldn't finish by once due to download failures or platform specific issues that leads to errors. You can follow this guide to reproduce each figures individually.

Below is a table of checkboxes that corresponds to each benchmark run. And each benchmark run often corresponds to one line or one set of bars presented in the paper.

| Figure           | 11&12   | 13&14   | 13&14   | 13&15   | 13&15    | 13&17   |
| ---------------- | ------- | ------- | ------- | ------- | -------- | ------- |
| System\Benchmark | Micro   | JVM     | Metis   | Dedup   | Psearchy | PARSEC  |
| CortenMM-rw      | a1. [ ] | b1. [ ] | c1. [ ] | d1. [ ] | e1. [ ]  | f1. [ ] |
| CortenMM-adv     | a2. [ ] | b2. [ ] | c2. [ ] | d2. [ ] | e2. [ ]  | f2. [ ] |
| CortenMM-adv+TC  |         |         |         | d3. [ ] | e3. [ ]  |         |
| Linux            | a3. [ ] | b3. [ ] | c3. [ ] | d4. [ ] | e4. [ ]  | f3. [ ] |
| Linux+TC         |         |         |         | d5. [ ] | e5. [ ]  |         |
| RadixVM          | a4. [ ] |         | c4. [ ] |         |          |         |
| NrOS             | a5. [ ] |         |         |         |          |         |

To see the specific command to run for each checkbox, see [this script](scripts/container_run_all_experiments.sh).

After all commands in related columns are run, the corresponding plotting script can be used to generate plots in the paper. For example, to have Figure 14, you need to run b1\~b3 and c1\~c4. Each run will generate one log file in `./experiment_outputs`, which is later parsed by the plotting scripts.
