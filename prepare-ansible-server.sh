#!/usr/bin/env bash
set -euo pipefail

test "$(id -u)" -eq 0
cd /root

test -s ssh-key.pem
test -s .ssh/known_hosts
chmod 600 ssh-key.pem

apt-get update

DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-venv \
    ca-certificates \
    openssh-client

python3 -m venv /opt/ansible-project

/opt/ansible-project/bin/python -m pip install \
    -r /root/requirements.txt

/opt/ansible-project/bin/python -m pip check

/opt/ansible-project/bin/ansible-galaxy collection install \
    -r /root/requirements.yml

/opt/ansible-project/bin/ansible --version
