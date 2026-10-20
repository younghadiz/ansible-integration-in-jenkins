# Source provenance

## Imported baseline

- Upstream repository: https://gitlab.com/twn-devops-bootcamp/latest/15-ansible/java-maven-app.git
- Starting branch: master
- Baseline commit: 283193313583e0973e4d90d876c460064045f7b5
- Imported on: 2026-10-15
- Training source: TechWorld with Nana, Module 15 — Ansible
- Project: Ansible Integration in Jenkins

The starting application and pipeline files were imported from this repository.
The inspected baseline commit identifies Nana Janashia as its author; this does
not independently establish original authorship of every application component.

No licence file was present in the imported baseline. This project does not
assert ownership of upstream code or grant additional rights to it.

## Independent implementation

Gafari Oladele Salaudeen is responsible for the independent DevOps implementation
and documentation added after this baseline.

## Initial inspection findings

The imported Jenkinsfile contains trailing whitespace on lines 3, 39 and 41.
These formatting issues are preserved in the baseline for later correction.

Implementation and deployment verification are pending.

## Completed implementation reference

After importing the master baseline, the completed feature/ansible branch
was inspected to align the implementation with Nana's teaching.

- Reference commit: f7b73f6e990cb87d142297d21da1ed04ab4e0215
- Reference branch: feature/ansible
- Reference scope: Jenkinsfile, prepare-ansible-server.sh, Ansible configuration,
  EC2 dynamic inventory and Docker/Docker Compose installation playbook.

The implementation follows the two-stage file-transfer and remote-execution
flow using sshagent, scp, sshScript and sshCommand.

Adaptations include project-scoped inventory in ca-central-1, DNF for Amazon
Linux 2023 managed nodes, an isolated control-node Python environment,
SSH host-key verification and transferred EC2 key cleanup.

Live Jenkins and managed-node execution remain pending.

## Clean rebuild and final integration adaptations

The completed teaching reference remains:

- Branch: feature/ansible
- Commit: f7b73f6e990cb87d142297d21da1ed04ab4e0215

The final implementation retains the two-stage Jenkins file-transfer and
remote-execution flow.

Independent adaptations include:

- Fresh Ubuntu 24.04 Jenkins and Ansible control servers.
- Jenkins localhost binding with SSH-tunnel access.
- Replacement SSH credentials and verified server host keys.
- An isolated control-node Python environment.
- Amazon Linux 2023 managed nodes and DNF.
- Project-scoped EC2 dynamic inventory in ca-central-1.
- Dedicated restricted AWS inventory credentials.
- Expected-instance-ID and host-count validation.
- Pinned Docker Compose release with checksum verification.
- Passphrase-aware control-server authentication.
- Transferred managed-node key cleanup.
- Two-run deployment and idempotence verification.
- Project-scoped AWS provisioning and cleanup scripts.

An earlier Jenkins droplet was reported by DigitalOcean as sending malicious
traffic. The affected project resources were removed and replacement
credentials were created. The original entry point was not established.

Live completion claims are generated only after successful deployment
verification and resource cleanup.

## Clean rebuild and final integration adaptations

The completed teaching reference remains:

- Branch: feature/ansible
- Commit: f7b73f6e990cb87d142297d21da1ed04ab4e0215

The final implementation retains the two-stage Jenkins file-transfer and
remote-execution flow.

Independent adaptations include:

- Fresh Ubuntu 24.04 Jenkins and Ansible control servers.
- Jenkins localhost binding with SSH-tunnel access.
- Replacement SSH credentials and verified server host keys.
- An isolated control-node Python environment.
- Amazon Linux 2023 managed nodes and DNF.
- Project-scoped EC2 dynamic inventory in ca-central-1.
- Dedicated restricted AWS inventory credentials.
- Expected-instance-ID and host-count validation.
- Pinned Docker Compose release with checksum verification.
- Passphrase-aware control-server authentication.
- Transferred managed-node key cleanup.
- Two-run deployment and idempotence verification.
- Project-scoped AWS provisioning and cleanup scripts.

An earlier Jenkins droplet was reported by DigitalOcean as sending malicious
traffic. The affected project resources were removed and replacement
credentials were created.

Live completion claims are generated only after successful deployment
verification and resource cleanup.
