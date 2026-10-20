#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()

parser.add_argument(
    "--digitalocean-deleted",
    action="store_true",
    help="Confirm both project droplets and unwanted associated resources are deleted",
)

args = parser.parse_args()

root = Path(__file__).resolve().parent.parent

verification = json.loads(
    (root / ".local/project-verification.json").read_text()
)

state = json.loads(
    (root / ".local/aws-state.json").read_text()
)

verified_commit = verification.get("source_commit")

subprocess.run(
    ["git", "merge-base", "--is-ancestor", verified_commit, "HEAD"],
    cwd=root,
    check=True,
)

subprocess.run(
    [
        "git",
        "diff",
        "--exit-code",
        verified_commit,
        "--",
        "Jenkinsfile",
        "prepare-ansible-server.sh",
        "ansible",
        "scripts/manage-aws.py",
        "scripts/check-inventory.py",
        "scripts/check-results.py",
    ],
    cwd=root,
    check=True,
)

if verification.get("node_count") != 2:
    raise SystemExit("A successful two-node verification report is required.")

if verification.get("idempotence") != "passed":
    raise SystemExit("Idempotence verification did not pass.")

if not state.get("destroyed_at"):
    raise SystemExit("AWS cleanup has not been recorded.")

if not args.digitalocean_deleted:
    raise SystemExit("Confirm DigitalOcean deletion before finalizing.")

readme = f"""# Ansible Integration in Jenkins

Jenkins copies Ansible configuration and a managed-node SSH key to a dedicated
control server, then executes Ansible remotely to install Docker and Docker
Compose on two Amazon Linux 2023 EC2 nodes.

## Verified result

- Live deployment verified at {verification['verified_at_utc']}.
- Two expected EC2 nodes passed the Docker and Docker Compose checks.
- A second playbook run completed with zero changes, failures and unreachable hosts.
- Verified implementation commit: `{verification['source_commit']}`.
- AWS teardown completed at {state['destroyed_at']}.
- DigitalOcean project-resource deletion confirmed by the operator.

## Project scope

This project follows the completed teaching reference's two-stage Jenkins flow:

1. Copy Ansible files and the dedicated managed-node key to the control server.
2. Prepare the control environment and execute Ansible remotely.

The pipeline configures managed-node infrastructure. It does not publish a
Docker Hub image or deploy the Java application.

The starting Java application and previously verified local Dockerfile are
retained in the repository.

## Architecture

| Component | Responsibility |
| --- | --- |
| Jenkins on DigitalOcean | Source checkout, file transfer and remote execution |
| Dedicated Ansible control server | EC2 discovery and SSH orchestration |
| Two AWS EC2 nodes | Docker service and user-scoped Docker Compose plugin |
| GitHub | Primary source repository |
| GitLab | Manual repository mirror |

## Implementation

- Jenkins HTTP binds to localhost and is accessed through an SSH tunnel.
- Control authentication uses a passphrase-protected SSH key and verified host keys.
- Dynamic inventory filters project nodes in Canada Central.
- Preflight requires exactly the provisioned EC2 instance IDs.
- Dedicated AWS credentials provide restricted inventory access.
- Compose uses a pinned release with checksum verification.
- The transferred EC2 key is removed in pipeline post actions.
- Deployment checks and second-run idempotence guard against false success.
- Project lifecycle scripts provision and remove recorded AWS resources.

## Reproduce

Use the complete [runbook](docs/RUNBOOK.md).

It contains fresh setup, credentials, provisioning, the complete source and
configuration files, Jenkins job setup, verification, troubleshooting, cleanup
and release instructions.

## Attribution

Starting application and training reference: TechWorld with Nana.

Independent implementation, adaptations and documentation:
Gafari Oladele Salaudeen.

See [source provenance](docs/SOURCE_PROVENANCE.md).

## Operational history

An earlier Jenkins droplet was reported by DigitalOcean as sending malicious
traffic. The affected lab resources were removed and replacement credentials
and clean server images were used. The original entry point was not established.

No private keys, cloud credentials or local provisioning state are committed.
"""

(root / "README.md").write_text(readme)

runbook = root / "docs/RUNBOOK.md"
text = runbook.read_text()

marker = "\n## Operator completion record\n"
text = text.split(marker)[0]

record = f"""
## Operator completion record

- Deployment verified: {verification['verified_at_utc']}.
- Verified implementation commit: `{verification['source_commit']}`.
- Two nodes passed Docker and Compose verification.
- Second-run changes, failures and unreachable hosts: zero.
- AWS cleanup completed: {state['destroyed_at']}.
- DigitalOcean project-resource deletion confirmed by the operator.
"""

runbook.write_text(text + record)

print("Final README and runbook completion record generated from local evidence.")
