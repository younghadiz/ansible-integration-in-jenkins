# Ansible Integration in Jenkins

Automate the configuration of two AWS EC2 instances through a Jenkins pipeline
and a dedicated Ansible control server.

This capstone follows TechWorld with Nana's completed Ansible integration
project, with adaptations for Amazon Linux 2023, reproducible dependencies,
SSH host verification, automated provisioning and execution checks.

## Overview

Jenkins checks out the repository, transfers the Ansible configuration to the
control server and executes the playbook remotely. Ansible discovers the
project's EC2 instances and installs Docker and Docker Compose.

The workflow includes inventory validation, two playbook executions,
second-run idempotence checks and temporary SSH key cleanup.

## Architecture

| Component | Platform | Responsibility |
| --- | --- | --- |
| Jenkins server | DigitalOcean · Ubuntu | Pipeline orchestration and source checkout |
| Ansible control server | DigitalOcean · Ubuntu | EC2 discovery and remote configuration |
| Two managed nodes | AWS EC2 · Amazon Linux 2023 | Docker and Docker Compose installation |
| Operator workstation | Local environment | Git, infrastructure provisioning and administrative access |
| Source repositories | GitHub and GitLab | Primary repository and mirror |

Jenkins listens on loopback and is accessed through an SSH tunnel. The control
server connects to the managed nodes over SSH.

## What the project implements

- A two-stage Jenkins pipeline using `sshagent`, `scp`, `sshScript` and
  `sshCommand`.
- AWS EC2 dynamic inventory filtered by project and deployment tags.
- An isolated Python environment for Ansible and AWS SDK dependencies.
- Docker installation and service configuration on Amazon Linux 2023.
- A versioned Docker Compose CLI plugin.
- Validation that the inventory contains the two expected instances.
- Docker and Compose execution checks.
- Playbook result evaluation and second-run idempotence checks.
- Python automation for AWS provisioning, inventory credentials and teardown.
- A complete reproduction and operations runbook.

## Jenkins pipeline

### Stage 1: Copy files to the Ansible server

Transfers the configuration, inventory, playbook, dependency requirements,
verification scripts and source revision to the control server.

The managed-node SSH key is supplied through Jenkins Credentials and
transferred separately for temporary use.

### Stage 2: Execute the Ansible playbook

Prepares the control environment, discovers the managed nodes, validates the
inventory and executes the playbook twice.

The result checker evaluates failures, unreachable hosts and second-run
changes, then generates a verification report.

A post-build action attempts to remove the transferred managed-node key.

## Repository structure

| File or directory | Purpose |
| --- | --- |
| `Jenkinsfile` | Pipeline orchestration, remote execution and key cleanup |
| `prepare-ansible-server.sh` | Control-server dependency preparation |
| `ansible/ansible.cfg` | Ansible connection settings |
| `ansible/inventory_aws_ec2.yaml` | AWS dynamic inventory |
| `ansible/my-playbook.yaml` | Docker and Compose configuration |
| `ansible/requirements.txt` | Python dependency versions |
| `ansible/requirements.yml` | Ansible collection requirements |
| `scripts/manage-aws.py` | AWS provisioning, credentials, host verification and teardown |
| `scripts/check-inventory.py` | Expected-instance inventory validation |
| `scripts/check-results.py` | Execution and idempotence evaluation |
| `scripts/finalize-docs.py` | Documentation finalization from verification records |
| `Dockerfile` | Non-root Java application container |
| `pom.xml` and `src/` | Starting Java application |
| `script.groovy` | Retained upstream helper; unused by the current pipeline |
| `docs/RUNBOOK.md` | Full start-to-release reproduction guide |
| `docs/SOURCE_PROVENANCE.md` | Attribution, reference commits and adaptations |

## Reproduce the project

Use the [complete runbook](docs/RUNBOOK.md).

It contains:

1. Prerequisites and repository initialization.
2. Full source files and configuration.
3. SSH key preparation and server provisioning.
4. Jenkins installation, access and credentials.
5. AWS resource provisioning and dynamic inventory.
6. Pipeline configuration and execution.
7. Verification and idempotence checks.
8. Troubleshooting and recovery.
9. Infrastructure cleanup.
10. Documentation, Git merges and final release.

Provision cloud resources when ready to execute the cloud stages and remove
them after collecting the required evidence.

## Jenkins credentials

| Credential ID | Type | Purpose |
| --- | --- | --- |
| `ansible-server-key` | SSH username with private key | Control-server access as `root` |
| `ec2-server-key` | SSH username with private key | Managed-node access as `ec2-user` |
| `ansible-server-known-hosts` | Secret file | Verified control-server SSH host key |

The control-server credential includes its key passphrase where applicable.
The managed-node automation key must support noninteractive execution.

Private keys, AWS credentials and private runtime records are excluded from Git.

## Application container

The repository also includes the starting Java application and a non-root
Dockerfile.

Local verification completed successfully:

- Maven packaged the executable application.
- The application returned HTTP 200 and the expected welcome page.
- The Docker image built and served the same page.
- The container ran as the non-root application user.
- The smoke-test container was stopped and removed.

The current Jenkins Ansible pipeline configures Docker and Compose on EC2.
Application image publishing and application deployment to EC2 are outside
this pipeline's scope.

### Build

```bash
mvn --batch-mode clean verify

docker build \
  -t ansible-integration-in-jenkins:local .
```

### Run

```bash
docker run -d \
  --name ansible-jenkins-local \
  -p 127.0.0.1:18080:8080 \
  ansible-integration-in-jenkins:local
```

### Verify

After startup:

```bash
docker logs ansible-jenkins-local

curl --fail --silent --show-error \
  http://127.0.0.1:18080/
```

Expected content:

```text
Welcome to Java Maven Application
```

### Clean up

```bash
docker stop ansible-jenkins-local
docker rm ansible-jenkins-local
docker image rm ansible-integration-in-jenkins:local

mvn clean
```

## Cloud verification

The automated checks require:

| Check | Success condition |
| --- | --- |
| Inventory | Exactly the two expected EC2 instances |
| SSH trust | Host-key entries available for both nodes |
| Configuration | No failed or unreachable hosts |
| Docker | Docker daemon responds successfully |
| Compose | Installed version matches the configured version |
| Idempotence | Second execution reports zero changes |

The verification report records the source revision and playbook recap results.
Refer to the runbook's operator completion record, when present, for recorded
cloud execution and cleanup outcomes.

## Security considerations

The implementation uses:

- Loopback-only Jenkins access through an SSH tunnel.
- Restricted SSH ingress.
- SSH host-key verification.
- Jenkins Credentials for private keys.
- Project-scoped inventory filters.
- Inventory IAM permissions restricted by region and control-server source IP.
- Temporary managed-node key transfer and post-build cleanup.
- Explicit infrastructure teardown.

During development, the original Jenkins Droplet was reported sending malicious
outbound traffic. The original Jenkins and control Droplets were destroyed,
the original managed nodes were terminated and replacement SSH keys were
created. The entry point was not established.

The replacement configuration incorporates the controls above. Incident context
and operational recovery guidance are documented in the runbook.

## Cleanup and cost control

Follow the runbook to remove the project's:

- Inventory IAM access keys, inline policy and IAM user.
- EC2 managed nodes.
- Security group and imported EC2 key pair.
- Remaining project storage resources.
- Jenkins and Ansible DigitalOcean Droplets.
- Unneeded backups, snapshots and reserved addresses.
- Temporary local credentials.

AWS teardown is automated through `scripts/manage-aws.py`. DigitalOcean cleanup
is performed separately.

Resource deletion stops future resource usage; previously incurred charges
remain payable.

## Development workflow

Changes follow feature and documentation branches into `develop`, then `main`.

- Conventional commit messages describe individual changes.
- `--no-ff` merges preserve branch history.
- GitHub is the primary remote.
- GitLab mirrors project branches and release tags.
- An annotated release tag identifies a reviewed release revision.

## Documentation

- [Complete runbook](docs/RUNBOOK.md)
- [Source provenance](docs/SOURCE_PROVENANCE.md)

## Attribution

Starting application and training material: **TechWorld with Nana**.

Independent implementation, adaptations and documentation:
**Gafari Oladele Salaudeen**.

The implementation references Nana's completed `feature/ansible` branch.
Adaptations and reference commits are recorded in the source provenance document.

No licence file was present in the imported baseline. This repository does not
grant additional rights to upstream material.

## Links

- [GitHub repository](https://github.com/younghadiz/ansible-integration-in-jenkins)
- [GitLab mirror](https://gitlab.com/devops-engineering-projects/ansible-integration-in-jenkins)
- [Upstream training repository](https://gitlab.com/twn-devops-bootcamp/latest/15-ansible/java-maven-app)
- [Completed upstream implementation](https://gitlab.com/twn-devops-bootcamp/latest/15-ansible/java-maven-app/-/tree/feature/ansible)
