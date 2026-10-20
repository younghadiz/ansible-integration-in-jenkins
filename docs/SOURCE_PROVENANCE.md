# Source provenance

## Imported baseline

- Training source: TechWorld with Nana, Module 15 — Ansible
- Project: Ansible Integration in Jenkins
- Upstream repository: https://gitlab.com/twn-devops-bootcamp/latest/15-ansible/java-maven-app.git
- Starting branch: master
- Baseline commit: 283193313583e0973e4d90d876c460064045f7b5
- Imported on: 2026-10-15

The starting application and pipeline files were imported from this repository.
The inspected baseline commit identifies Nana Janashia as its author; this does
not independently establish original authorship of every application component.

No licence file was present in the imported baseline. This project does not
assert ownership of upstream code or grant additional rights to it.

## Historical baseline status

At initial import, independent implementation and deployment verification were
pending. The imported Jenkinsfile also contained trailing whitespace.

These are historical observations about the starting baseline, rather than
the status of the current implementation.

## Completed implementation reference

After importing the starting baseline, the completed upstream implementation
was inspected to align the project with Nana's teaching.

- Reference branch: feature/ansible
- Reference commit: f7b73f6e990cb87d142297d21da1ed04ab4e0215
- Reference scope: Jenkinsfile, prepare-ansible-server.sh, Ansible configuration,
  EC2 dynamic inventory and Docker/Docker Compose installation playbook.

The implementation retains the two-stage file-transfer and remote-execution
flow using sshagent, scp, sshScript and sshCommand.

## Independent implementation and adaptations

Gafari Oladele Salaudeen is responsible for the independent adaptations and
documentation added after the imported baseline.

Adaptations include:

- Ubuntu 24.04 Jenkins and Ansible control servers.
- Jenkins loopback binding with SSH-tunnel access.
- Verified SSH host keys and replacement credentials.
- An isolated control-node Python environment.
- Amazon Linux 2023 managed nodes and DNF.
- Project-scoped EC2 dynamic inventory in ca-central-1.
- Restricted AWS inventory credentials.
- Expected-instance-ID and host-count validation.
- A pinned Docker Compose release with checksum verification.
- Passphrase-aware control-server authentication.
- Temporary managed-node key transfer and cleanup.
- Two-run playbook result and idempotence checks.
- AWS provisioning and teardown automation.
- A non-root Dockerfile and local application smoke testing.
- A standalone reproduction and operations runbook.

The current Jenkins workflow configures Docker and Docker Compose on EC2.
It does not publish an application image or deploy the Java application.

## Current implementation and evidence status

The Jenkins integration, Ansible configuration, provisioning automation,
verification scripts and documentation are committed to the repository.

The project history records feature and documentation branches merged through
develop into main.

Local application build and container smoke testing were completed during
development. Ansible syntax checks also passed.

The public repository does not currently include a saved successful cloud
verification report, Jenkins build evidence or replacement-environment cleanup
evidence. Their absence does not establish whether execution occurred; it
limits what a reviewer can independently verify.

See the Operator completion record in docs/RUNBOOK.md for the documented
status. Future completion claims must reference actual execution evidence.

## Development incident and rebuild

DigitalOcean reported malicious outbound traffic from the original Jenkins
Droplet. The original Jenkins and control Droplets were destroyed, the original
EC2 managed nodes were terminated and replacement SSH credentials were created.

The original entry point was not established. This historical cleanup must
not be treated as evidence of cleanup for the replacement environment.
