# The Difference Between Artifact Image Versions

We are updating `ghcr.io/telos-syslab/cortenmm-artifact-env` for fixes. If you are using an older version and do not want to download the new image entirely. You can follow it to patch the old image.

## Upgrading v2 to v4

Inside the container, do:

```bash
apt update && apt upgrade
apt install -y \
    libtcmalloc-minimal4 texlive-latex-base fonts-linuxlibertine \
    dvipng texlive-latex-extra texlive-fonts-extra cm-super
python3 -m pip install matplotlib
```

## Upgrading v4 to v4.1

Inside the container, do:

```bash
apt update && apt install -y libssl-dev
```
