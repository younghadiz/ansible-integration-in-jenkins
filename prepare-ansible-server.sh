#!/usr/bin/env bash
set -euo pipefail

cd /root

echo "Installing Python prerequisites..."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-venv \
    ca-certificates \
    openssh-client

echo "Installing Ansible and Boto3..."
python3 -m venv /opt/ansible-project
/opt/ansible-project/bin/python -m pip install \
    -r /root/requirements.txt
/opt/ansible-project/bin/python -m pip check

echo "Installing the AWS collection..."
/opt/ansible-project/bin/ansible-galaxy collection install \
    -r /root/requirements.yml

echo "Setting managed-node key permissions..."
chmod 600 /root/ssh-key.pem

echo "Checking Ansible..."
/opt/ansible-project/bin/ansible --version
