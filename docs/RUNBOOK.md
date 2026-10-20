# Ansible Integration in Jenkins — Complete Deployment and Operations Runbook

## 1. Purpose

This runbook recreates the project from an empty local working directory through
repository setup, server preparation, credentials, AWS provisioning, Jenkins
execution, verification, troubleshooting, cleanup, documentation and final release.

It includes the complete implementation files in its source appendix.
No chat history is required.

The intended outcome follows the completed TechWorld with Nana reference:

1. Jenkins copies Ansible files and a dedicated managed-node SSH key to a
   separate Ansible control server.
2. Jenkins prepares the control environment and executes Ansible remotely.
3. Ansible installs Docker and Docker Compose on two Amazon Linux 2023 EC2 nodes.

The final Jenkins pipeline configures infrastructure. It does not publish a
Docker image or deploy the Java application.

The original Java application, script.groovy and independently added Dockerfile
are retained. The final Jenkinsfile does not load script.groovy.

## 2. Evidence and status

Use the Operator completion record at the end of this document, when present,
for actual verification and cleanup dates.

The presence of this runbook does not itself establish successful deployment.

Live success requires:

- The intended implementation commit checked out by Jenkins.
- Exactly two expected EC2 instances in inventory.
- Verified managed-node SSH host keys.
- Successful Docker and Compose checks on both nodes.
- A second playbook run with zero changes, failures and unreachable hosts.
- Confirmation that the transferred EC2 private key was removed.
- Actual cleanup of AWS and DigitalOcean project resources.

Do not claim these outcomes merely because syntax checking passed.

## 3. Architecture and responsibilities

| Component | Location | Responsibility |
| --- | --- | --- |
| Operator workstation | Mac | Git, AWS provisioning, trusted administration and cleanup |
| Jenkins | DigitalOcean Ubuntu 24.04 | SCM checkout, file transfer and remote execution |
| Ansible control server | Separate DigitalOcean Ubuntu 24.04 | Python environment, AWS discovery and SSH orchestration |
| Two managed nodes | AWS Canada Central | Docker service and Docker Compose installation |
| GitHub | Primary repository | Source history and release |
| GitLab | Manual mirror | Mirrored source history and release |

No NAT gateway, custom VPC, load balancer or application ingress is required.

The control server connects to the managed nodes over their public IPv4
addresses. Security groups restrict SSH to the control-server source address.

## 4. Prerequisites

### Operator workstation

- Git.
- OpenSSH client.
- Python 3.12–3.14 for the pinned Ansible controller environment.
- AWS CLI.
- AWS credentials authorized to provision and remove the project resources.
- DigitalOcean account access.
- Access to the GitHub repository and GitLab mirror.

For the optional Java/container smoke test:

- Java 17.
- Maven.
- Docker.

### AWS permissions

The operator identity needs the actions used by scripts/manage-aws.py:

- EC2 instance launch, describe, tagging and termination.
- EC2 security-group creation, rule authorization and deletion.
- EC2 key-pair import, describe and deletion.
- EC2 image, networking, route-table and volume discovery.
- EC2 console-output retrieval.
- SSM GetParameter for the public Amazon Linux AMI parameter.
- Creation and deletion of the dedicated inventory IAM user.
- Inline-policy and access-key lifecycle operations for that user.

The script stops if permissions are missing. Use an authorized account
administrator to resolve provisioning permission errors.

Do not copy the operator's broad AWS credentials onto Jenkins or the control
server as a workaround.

### Costs

DigitalOcean droplets, EC2 instances, EBS volumes and public IPv4 addresses may
incur charges.

Provision managed nodes only when the pipeline is ready. Verify and clean up
during the same work session where practical.

Powered-off DigitalOcean droplets remain billable.
Stopped EC2 instances can retain billable storage.
Deleting resources does not cancel historical charges or outstanding balances.

## 5. Source repositories and attribution

Primary repository:

https://github.com/younghadiz/ansible-integration-in-jenkins

Mirror:

https://gitlab.com/devops-engineering-projects/ansible-integration-in-jenkins

Starting teaching repository:

https://gitlab.com/twn-devops-bootcamp/latest/15-ansible/java-maven-app

Starting branch:

master

Starting commit:

283193313583e0973e4d90d876c460064045f7b5

Completed teaching reference:

feature/ansible

Completed reference commit:

f7b73f6e990cb87d142297d21da1ed04ab4e0215

Independent implementation and documentation:

Gafari Oladele Salaudeen.

See SOURCE_PROVENANCE.md for attribution, source limitations and adaptations.
Do not invent a license for upstream code.

## 6. Start from an empty local directory

The preferred reproduction route preserves the independent repository history.

On Mac:

```bash
mkdir -p "$HOME/Documents/tech-workspace/devops-capstone-projects"

cd "$HOME/Documents/tech-workspace/devops-capstone-projects"

git clone \
  https://github.com/younghadiz/ansible-integration-in-jenkins.git

cd ansible-integration-in-jenkins
```

After the completed project is released, main contains the final implementation.

To reproduce an exact published release:

```bash
git checkout v1.0.0
```

If the published version is different, use that actual release tag.

For further development, work on a branch rather than editing a detached tag:

```bash
git switch main

git switch -c feature/reproduce-ansible-integration
```

For the original completion workflow, the implementation branch was:

feature/jenkins-ansible-integration

Configure the GitLab mirror once:

```bash
git remote add gitlab \
  git@gitlab.com:devops-engineering-projects/ansible-integration-in-jenkins.git

git remote -v
```

If gitlab already exists, do not add it again.

GitHub may be cloned with HTTPS for public read access. Publishing changes
requires your authorized GitHub authentication.

## 7. Reconstruct files using this runbook alone

If source files must be reconstructed, create the project directory and place
this document at docs/RUNBOOK.md.

The source appendix contains a separate complete block for every included file.

Create each file at its stated relative path and copy its entire block.

Alternatively, from that project's root, extract the appendix automatically:

```bash
python3 - <<'PY'
from pathlib import Path
import re

root = Path.cwd()
runbook = root / "docs/RUNBOOK.md"

text = runbook.read_text()

pattern = re.compile(
    r"^### File: `([^`]+)`\n\n"
    r"````[^\n]*\n"
    r"(.*?)\n````\n",
    re.MULTILINE | re.DOTALL,
)

matches = pattern.findall(text)

if not matches:
    raise SystemExit("No complete source appendix found.")

for filename, content in matches:
    relative = Path(filename)

    if relative.is_absolute() or ".." in relative.parts:
        raise SystemExit(f"Unsafe source path: {filename}")

    if filename == "docs/RUNBOOK.md":
        raise SystemExit("Refusing to overwrite the runbook itself.")

    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content + "\n")

    print("Restored:", filename)
PY

chmod +x prepare-ansible-server.sh scripts/*.py
```

Do this in a clean reconstruction directory, because extraction replaces the
listed files.

If reconstructing without Git history, initialize a new independent repository
only in that new directory:

```bash
git init -b main
git add .
git diff --cached --check
git commit -m "chore: reconstruct documented project baseline"
```

Do not remove .git or reinitialize your existing independent repository.

## 8. Local private state and environment

From the project root:

```bash
mkdir -p .local
chmod 700 .local

python3 -m venv .venv
source .venv/bin/activate
rehash

python -m pip install -r ansible/requirements.txt
python -m pip check
```

In Bash use hash -r instead of rehash.

If the default Python is outside the supported controller range, use an
installed Python 3.12 executable to create the environment:

```bash
python3.12 -m venv .venv
```

Do not recreate a virtual environment while its installation is running.

Verify ignored paths:

```bash
git check-ignore .local/ .venv/ .ansible/
```

Expected: all three paths are printed.

.local contains resource IDs, temporary credentials and verification results.
It must not be committed.

Authenticate the Mac AWS identity:

```bash
aws sts get-caller-identity --query Arn --output text
aws configure get region
```

The project scripts explicitly use ca-central-1.

## 9. Create separate SSH identities

Use separate keys for:

1. Operator-to-Jenkins administration.
2. Jenkins-to-control authentication.
3. Control-to-EC2 authentication.

On Mac, if these filenames do not already exist:

```bash
ssh-keygen -t ed25519 \
  -f ~/.ssh/ansible-project-jenkins-admin-v2 \
  -C ansible-project-jenkins-admin-v2

ssh-keygen -t ed25519 \
  -f ~/.ssh/ansible-project-control-v2 \
  -C ansible-project-control-v2

ssh-keygen -t rsa -b 4096 \
  -f ~/.ssh/ansible-project-ec2-v2 \
  -C ansible-project-ec2-v2
```

Use strong passphrases for the originals.

Do not overwrite existing legitimate keys. For another deployment choose fresh
filenames and update corresponding script paths consistently.

Upload only public .pub files to DigitalOcean.

The administrator private key remains only on the Mac. Never add it to Jenkins
credentials.

The AWS provisioning script imports the EC2 public key.

Public fingerprints identify keys; they are not private login credentials.

## 10. Create DigitalOcean servers

Create fresh Ubuntu 24.04 LTS droplets:

| Name | Suggested temporary lab size | SSH key |
| --- | --- | --- |
| ansible-project-jenkins-v2 | 2 vCPU / 4 GB RAM | Jenkins administrator public key |
| ansible-project-control-v2 | 2 GB RAM | Control-server public key |

Use the same region for the droplets.

Do not restore a compromised server image, Jenkins home, credentials database
or unreviewed backup.

Historical addresses for the documented rebuild:

| Server | Historical address |
| --- | --- |
| Jenkins | 159.203.26.61 |
| Control | 138.197.140.196 |

For a new reproduction replace those addresses throughout this runbook's
commands and Jenkins parameters.

Do not reuse historical host fingerprints for a new server.

## 11. Configure DigitalOcean firewalls

Get the Mac's current public IPv4:

```bash
curl -4 --fail --silent --show-error https://checkip.amazonaws.com
```

Configure inbound rules:

| Destination | Source | Port |
| --- | --- | --- |
| Jenkins | Current operator public IPv4 /32 | TCP 22 |
| Control | Current operator public IPv4 /32 | TCP 22 |
| Control | Current Jenkins public IPv4 /32 | TCP 22 |

Remove broad inbound IPv4/IPv6 rules.

Do not add public Jenkins TCP 8080.

Retain default outbound rules for package downloads, AWS API access and SSH from
control to EC2.

Attach the firewalls before installing application services.

If your home/VPN public IP changes, update the relevant /32 rule. Do not solve
access problems by opening Jenkins publicly.

## 12. Verify first SSH host identities

In DigitalOcean's trusted console run on the relevant server:

```bash
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Compare this value with the first SSH connection's displayed fingerprint.

From Mac:

```bash
ssh \
  -i ~/.ssh/ansible-project-jenkins-admin-v2 \
  root@159.203.26.61
```

And separately:

```bash
ssh \
  -i ~/.ssh/ansible-project-control-v2 \
  root@138.197.140.196
```

Accept only after verifying the fingerprint.

A mismatch must be investigated. Do not bypass it by disabling host-key checking.

## 13. Install Jenkins on the fresh Jenkins server

Run as root on Jenkins:

```bash
apt-get update
apt-get upgrade -y

apt-get install -y \
  fontconfig \
  openjdk-21-jre \
  git \
  curl \
  ca-certificates \
  openssh-client
```

Configure loopback binding before installing Jenkins:

```bash
mkdir -p /etc/systemd/system/jenkins.service.d

cat > /etc/systemd/system/jenkins.service.d/override.conf <<'EOF'
[Service]
Environment="JENKINS_LISTEN_ADDRESS=127.0.0.1"
EOF

systemctl daemon-reload
```

Add the official repository and signing key:

```bash
install -d -m 0755 /etc/apt/keyrings

curl -fsSL \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key \
  -o /etc/apt/keyrings/jenkins-keyring.asc

chmod 644 /etc/apt/keyrings/jenkins-keyring.asc

echo 'deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/' \
  > /etc/apt/sources.list.d/jenkins.list

apt-get update
apt-get install -y jenkins

systemctl enable --now jenkins
```

For future reproductions check the official Jenkins installation documentation
if repository signing keys or supported Java requirements have changed.

Verify:

```bash
systemctl is-active jenkins

ss -ltnp 'sport = :8080'

curl --max-time 15 -s -o /dev/null \
  -w 'HTTP %{http_code}\n' \
  http://127.0.0.1:8080/login
```

Expected:

- active.
- A loopback listener.
- HTTP 200 after startup.

The listener may display as [::ffff:127.0.0.1]:8080.

If apt cannot locate Jenkins, verify the repository and signing key were
actually created. Do not bypass signature checking.

## 14. Open the SSH tunnel and finish Jenkins setup

On Mac in a separate terminal:

```bash
ssh -N \
  -i ~/.ssh/ansible-project-jenkins-admin-v2 \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  -L 127.0.0.1:18080:127.0.0.1:8080 \
  root@159.203.26.61
```

Keep this terminal open.

Browse:

http://127.0.0.1:18080/

On Jenkins retrieve:

```bash
cat /var/lib/jenkins/secrets/initialAdminPassword
```

Paste the value directly into the unlock page. Do not publish it.

Install suggested plugins and create an administrator with a new unique
password.

Set Jenkins URL to:

http://127.0.0.1:18080/

Install:

- SSH Agent.
- SSH Pipeline Steps.

Git, Pipeline and Credentials Binding must also be available.

Complete plugin installation and restart when requested.

Retain authentication, disable self-signup, deny anonymous administrative/job
access and keep CSRF protection and the Groovy sandbox enabled.

The temporary teaching-aligned lab uses the built-in executor. Production
environments should isolate build agents.

## 15. Update the control server

Run as root on the control server:

```bash
apt-get update
apt-get upgrade -y
```

If updates require a reboot, reboot and reconnect before continuing.

Jenkins prepares Ansible later through prepare-ansible-server.sh.

Do not manually install an unrelated global Ansible environment as a workaround.

## 16. Prepare the control known-hosts file

On Mac, after independently verifying the current control fingerprint:

```bash
ssh \
  -i ~/.ssh/ansible-project-control-v2 \
  -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes \
  root@138.197.140.196 \
  'printf "138.197.140.196 "; cat /etc/ssh/ssh_host_ed25519_key.pub' \
  > ~/.ssh/ansible-project-control-v2-known-hosts

ssh-keygen -lf ~/.ssh/ansible-project-control-v2-known-hosts
```

This retrieves a public host key over authenticated SSH.

An empty file is invalid. An unauthenticated scan alone is not sufficient to
establish host identity.

## 17. Prepare the EC2 automation copy

Keep the original Mac EC2 private key encrypted.

The teaching flow copies a private key to the control server. For unattended
OpenSSH use create an unencrypted copy dedicated to disposable managed nodes:

```bash
cp ~/.ssh/ansible-project-ec2-v2 .local/ec2-jenkins-key
chmod 600 .local/ec2-jenkins-key

ssh-keygen -p -f .local/ec2-jenkins-key
```

Enter the existing passphrase. Press Enter for the new passphrase, then Enter
again to confirm.

This modifies only the temporary copy.

The pipeline transfers that key under restrictive permissions and removes it
after execution. Controller/control compromise can expose the automation key;
it must remain dedicated to the disposable project nodes.

## 18. Create Jenkins credentials

Manage Jenkins → Credentials → System → Global → Add Credentials.

| ID | Kind | Username | Value |
| --- | --- | --- | --- |
| ansible-server-key | SSH Username with private key | root | Original control key and its actual passphrase |
| ec2-server-key | SSH Username with private key | ec2-user | Unencrypted automation copy; empty passphrase |
| ansible-server-known-hosts | Secret file | — | Verified control known-hosts file |

Use Enter directly → Add for private keys.

On Mac copy the control key when filling its field:

```bash
pbcopy < ~/.ssh/ansible-project-control-v2
```

Copy the EC2 automation copy when filling its field:

```bash
pbcopy < .local/ec2-jenkins-key
```

Upload this file for the host-key credential:

~/.ssh/ansible-project-control-v2-known-hosts

After saving the EC2 credential:

```bash
rm -f .local/ec2-jenkins-key
```

Never paste private keys into documentation, screenshots, chat or command-line
arguments.

## 19. Implementation file responsibilities

| File | Purpose |
| --- | --- |
| Jenkinsfile | Two-stage transfer/execution workflow and post cleanup |
| prepare-ansible-server.sh | Ubuntu prerequisites and isolated Ansible environment |
| ansible/ansible.cfg | Inventory, login user, key and strict SSH settings |
| ansible/inventory_aws_ec2.yaml | Project-scoped EC2 dynamic inventory |
| ansible/my-playbook.yaml | Docker/Compose installation and verification |
| ansible/requirements.txt | Pinned Python dependencies |
| ansible/requirements.yml | AWS collection dependency |
| scripts/manage-aws.py | Provisioning, inventory credentials, host trust and cleanup |
| scripts/check-inventory.py | Expected-node and trusted-host validation |
| scripts/check-results.py | Deployment recap and idempotence validation |
| scripts/finalize-docs.py | Evidence-based final documentation |
| Dockerfile and .dockerignore | Retained local application containerization |
| pom.xml and src/ | Starting Java application |
| script.groovy | Retained upstream helper, unused by final pipeline |

The complete file contents are in the source appendix.

Internal managed-node platform detection selects the correct Compose binary.
Publishing your personal machine architecture is unnecessary.

## 20. Validate before provisioning

On Mac:

```bash
bash -n prepare-ansible-server.sh

.venv/bin/python -m py_compile scripts/*.py

.venv/bin/ansible-galaxy collection install \
  -r ansible/requirements.yml \
  -p .ansible/collections

ANSIBLE_CONFIG="$PWD/ansible/ansible.cfg" \
ANSIBLE_COLLECTIONS_PATH="$PWD/.ansible/collections" \
.venv/bin/ansible-playbook \
  -i 'syntax-check-host,' \
  ansible/my-playbook.yaml \
  --syntax-check

git diff --check
```

Expected: successful parsing and syntax checks.

The dummy inline host avoids premature AWS discovery.
These checks do not execute modules remotely or validate Jenkins Groovy.

Commit and push implementation changes before Jenkins fetches them.

## 21. Provision two EC2 nodes

Run on Mac:

```bash
.venv/bin/python scripts/manage-aws.py provision \
  --control 138.197.140.196

.venv/bin/python scripts/manage-aws.py status
```

The script:

1. Checks AWS account ownership against saved state.
2. Discovers default public networking with an internet-gateway route.
3. Imports the replacement EC2 public key.
4. Creates a dedicated security group with SSH from control only.
5. Resolves the official Amazon Linux 2023 AMI.
6. Launches exactly two t3.micro nodes.
7. Uses encrypted 8 GB gp3 root disks and delete-on-termination.
8. Requires IMDSv2 and uses standard CPU credits.
9. Tags instances and volumes for this deployment.
10. Saves resource IDs/client token and waits for status checks.

Expected: two running managed nodes.

Keep .local/aws-state.json. Do not delete it to bypass conflicts.
A partial failure can leave resources; clean them with the destroy action if
abandoning execution.

The script deliberately does not create an alternative VPC if default public
networking is unavailable.

## 22. Install restricted inventory credentials

On Mac:

```bash
.venv/bin/python scripts/manage-aws.py credentials
```

The script creates a dedicated IAM user and inline policy for EC2 discovery.
The policy is restricted by region and the control-server source IP.

Discovery APIs use wildcard resources. Inventory tag filters select deployment
targets but are not IAM per-instance authorization.

The script stores a temporary access-key secret under ignored .local and
transfers credentials into /root/.aws/credentials with restrictive permissions.

Secrets are not printed. Broad Mac AWS credentials remain on Mac.

If an IAM key exists but its local secret file is lost, revoke the dedicated
orphaned key before retrying.

Allow for IAM propagation after inspecting any initial authorization failure.

## 23. Verify managed-node host keys

On Mac:

```bash
.venv/bin/python scripts/manage-aws.py hostkeys
```

This compares ED25519 fingerprints scanned from control with the nodes'
authenticated AWS console boot output.

Only after both match does it install:

- /root/.ssh/known_hosts
- /root/expected-instance-ids.json

If boot output has not arrived, retry after a minute.
If port 22 is unreachable, troubleshoot network access.
If a fingerprint mismatches, stop and investigate.

Do not disable host-key checking.

## 24. Configure the Jenkins Pipeline job

Create a Pipeline job:

- Name: ansible-integration-in-jenkins
- Definition: Pipeline script from SCM
- SCM: Git
- Repository: https://github.com/younghadiz/ansible-integration-in-jenkins.git
- Checkout credentials: none for the public repository
- Script path: Jenkinsfile
- Automatic triggers: off for the temporary lab

During original implementation the branch specifier was:

*/feature/jenkins-ansible-integration

For a published release use the intended released main/revision.
For a new development branch configure that actual branch.

Build with Parameters:

ANSIBLE_SERVER=138.197.140.196

If necessary enable "This project is parameterized" and add the String parameter
ANSIBLE_SERVER.

A first build with an empty parameter can fail before file transfer. Rebuild
with the correct value rather than modifying validation.

Maven and Docker installations on Jenkins are unnecessary for this final
infrastructure-only pipeline.

## 25. Understand Jenkins execution

First stage:

- Validates the destination parameter.
- Records the checked-out Git commit.
- Copies explicit Ansible and verification files.
- Transfers the dedicated EC2 key under umask 077.

Second stage:

- Supplies control username, identity, passphrase and known-hosts file.
- Runs prepare-ansible-server.sh through sshScript.
- Uses sshCommand to discover and validate inventory.
- Requires exactly the expected two instance IDs and trusted host entries.
- Runs the playbook twice.
- Uses pipefail so tee cannot hide playbook failures.
- Validates both recaps and second-run idempotence.

Post action:

- Attempts to remove /root/ssh-key.pem after success or failure.
- Network failure can prevent cleanup and requires manual removal.

## 26. Verify live results

Expected final Jenkins result:

SUCCESS

Both recaps must show exactly the two expected nodes:

- failed=0
- unreachable=0
- ok greater than zero

Second-run changed must equal zero.

The playbook also verifies the Docker daemon and pinned Compose version.

Retrieve the report on Mac:

```bash
scp \
  -i ~/.ssh/ansible-project-control-v2 \
  -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes \
  root@138.197.140.196:/root/project-verification.json \
  .local/project-verification.json

chmod 600 .local/project-verification.json

.venv/bin/python -m json.tool .local/project-verification.json
```

Confirm transferred-key cleanup:

```bash
ssh \
  -i ~/.ssh/ansible-project-control-v2 \
  -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes \
  root@138.197.140.196 \
  'test ! -e /root/ssh-key.pem && echo "Transferred EC2 key removed"'
```

If needed remove it manually:

```bash
ssh \
  -i ~/.ssh/ansible-project-control-v2 \
  -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes \
  root@138.197.140.196 \
  'rm -f /root/ssh-key.pem; test ! -e /root/ssh-key.pem'
```

Record manual intervention truthfully.

After functional fixes commit/push, rerun Jenkins and retrieve a new report.
An old report does not verify untested functional changes.

## 27. Optional Java/container smoke test

This is separate from the infrastructure pipeline.

On Mac:

```bash
mvn --batch-mode clean verify

docker build \
  -t ansible-integration-in-jenkins:local .

docker run -d \
  --name ansible-jenkins-local \
  -p 127.0.0.1:18081:8080 \
  ansible-integration-in-jenkins:local

docker logs ansible-jenkins-local

curl --fail --silent --show-error -i \
  http://127.0.0.1:18081/

docker exec ansible-jenkins-local id
```

Allow startup before curl.

Expected:

- HTTP 200.
- Welcome to Java Maven Application.
- UID/GID 10001.

The baseline has no Maven test sources. Do not describe build success as
automated tests having run.

Cleanup only this optional local container/image:

```bash
docker stop ansible-jenkins-local
docker rm ansible-jenkins-local
docker image rm ansible-integration-in-jenkins:local

mvn --batch-mode clean
```

Do not run global Docker prune commands that could affect other projects.

## 28. Troubleshooting Jenkins access

Keep the Mac tunnel open.

On Jenkins:

```bash
systemctl is-active jenkins
ss -ltnp 'sport = :8080'

curl --max-time 10 -s -o /dev/null \
  -w 'HTTP %{http_code}\n' \
  http://127.0.0.1:8080/login

journalctl -u jenkins \
  --since '15 minutes ago' \
  --no-pager -n 80
```

On Mac:

```bash
curl --max-time 10 -s -o /dev/null \
  -w 'HTTP %{http_code}\n' \
  http://127.0.0.1:18080/login
```

If a tunnel reports Address already in use, stop an older tunnel or choose a
different local port and corresponding browser URL.

Do not expose public 8080 as a shortcut.

## 29. Troubleshooting plugins and authentication

Missing sshagent: install SSH Agent.
Missing sshScript/sshCommand: install SSH Pipeline Steps.
Complete plugin installation and any requested restart.

Control credentials:

- Exact ID ansible-server-key.
- Username root.
- Replacement control private key.
- Actual key passphrase supplied.
- Verified current control known-hosts file.

Managed-node credentials:

- Exact ID ec2-server-key.
- Username ec2-user.
- Unencrypted dedicated automation copy.
- Empty Jenkins passphrase field for that copy.

Timeout usually indicates reachability.
Permission denied (publickey) indicates authentication.
Host-key mismatch requires independent identity verification.

Do not disable strict host checking to bypass errors.

## 30. Troubleshooting EC2 reachability

On Mac:

```bash
.venv/bin/python scripts/manage-aws.py status

aws ec2 describe-security-groups \
  --region ca-central-1 \
  --filters Name=group-name,Values=ansible-project-app-v2 \
  --query 'SecurityGroups[].{ID:GroupId,Ingress:IpPermissions}' \
  --output json
```

On control, substitute current node IPs:

```bash
nc -vz -w 5 NODE_1_IP 22
nc -vz -w 5 NODE_2_IP 22
```

If nc is unavailable on Ubuntu:

```bash
apt-get update
apt-get install -y netcat-openbsd
```

Check:

- Current node public IPs.
- Correct security-group attachment.
- Port22 source=current control IP/32.
- Public subnet internet-gateway route.
- NACL return traffic.
- DigitalOcean control outbound TCP22.
- Provider-imposed networking restrictions.

The Mac is intentionally not allowed direct SSH to EC2 by this security group.

An empty ssh-keyscan file does not establish that the EC2 private key is wrong.
The scan does not use that private key.

## 31. Troubleshooting inventory and package execution

For AWS discovery check:

- Root's dedicated credentials on control.
- Region ca-central-1.
- IAM source-IP/region conditions.
- Running instance state.
- Exact Project, Role and Deployment tags.
- No conflicting AWS_PROFILE/environment credentials.

Do not substitute broad Mac credentials or remove the expected-node guard.

The playbook is for Amazon Linux 2023, not Ubuntu managed nodes.
The control server is Ubuntu24 with the pinned Python environment.

If the shell uses global Ansible unexpectedly, use .venv/bin commands explicitly.

Compose is installed for ec2-user:

- docker compose version as ec2-user.
- sudo docker info for daemon access.

sudo docker compose may search root's plugin directories instead.

For checksum/download errors inspect DNS, outbound HTTPS, release URL and
published asset. Do not remove checksum validation.

For second-run changed greater than zero, inspect the changed task, fix,
commit/push and rerun before claiming idempotence.

## 32. Slowness and incident response

On Jenkins:

```bash
uptime
free -h
vmstat 1 10

ps -u jenkins \
  -o pid,ppid,etime,time,pcpu,pmem,args \
  --sort=-pcpu | head -25

ss -tunap

journalctl -u ssh \
  --since '6 hours ago' \
  --no-pager | grep 'Accepted'
```

The first vmstat row is an average since boot; later rows are current samples.
Sustained CPU steal can indicate virtual-host scheduling contention.

Successful SSH logs do not establish who accessed Jenkins through HTTP.

An earlier project droplet was reported by DigitalOcean as sending malicious
traffic. A restart removed symptoms but did not establish remediation.
The original entry point was not determined.

For a new abuse report:

1. Verify the report through the provider account.
2. Isolate/power off the affected host.
3. Revoke exposed credentials.
4. Preserve evidence before destruction if investigation is required.
5. Rebuild from clean images and reviewed source.

Do not restore its image, Jenkins home or credentials database.

## 33. Cleanup remote runtime credentials

Retrieve the successful verification report before destroying control.

If abandoning a failed deployment, still clean up without claiming success.

From Mac:

```bash
ssh \
  -i ~/.ssh/ansible-project-control-v2 \
  -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes \
  root@138.197.140.196 \
  'rm -f /root/ssh-key.pem /root/.aws/credentials /root/.aws/config'
```

## 34. Destroy recorded AWS resources

On Mac:

```bash
.venv/bin/python scripts/manage-aws.py destroy \
  --confirm ansible-integration-in-jenkins

.venv/bin/python scripts/manage-aws.py status
```

The script:

- Revokes access keys for the owned dedicated inventory IAM user.
- Deletes its inline policy and user.
- Terminates the recorded EC2 nodes and waits.
- Retries security-group deletion while interfaces detach.
- Deletes the imported project key pair.
- Checks for tagged project volumes.
- Records cleanup time.

It does not delete default networking or unrelated resources.

If remaining-volume or dependency checks fail, investigate and retry.
Do not mark cleanup complete on a failed command.

## 35. Independently check AWS cleanup

```bash
aws ec2 describe-instances \
  --region ca-central-1 \
  --filters \
    Name=tag:Project,Values=ansible-integration-in-jenkins \
    Name=tag:Deployment,Values=capstone-v2 \
  --query 'Reservations[].Instances[].{ID:InstanceId,State:State.Name}' \
  --output table

aws ec2 describe-volumes \
  --region ca-central-1 \
  --filters \
    Name=tag:Project,Values=ansible-integration-in-jenkins \
    Name=tag:Deployment,Values=capstone-v2 \
  --query 'Volumes[].{ID:VolumeId,State:State}' \
  --output table

aws ec2 describe-security-groups \
  --region ca-central-1 \
  --filters Name=group-name,Values=ansible-project-app-v2 \
  --query 'SecurityGroups[].GroupId' \
  --output text

aws iam get-user \
  --user-name ansible-project-inventory-v2
```

Expected:

- Project instances terminated, possibly visible temporarily.
- No matching volumes.
- No project security group.
- IAM NoSuchEntity.

The script creates no EIP, NAT gateway, load balancer, snapshot or custom VPC.
Inspect any additional resources you manually created.

## 36. Destroy DigitalOcean project resources

After source is pushed and verification is saved:

1. Destroy ansible-project-control-v2.
2. Destroy ansible-project-jenkins-v2.
3. Delete unwanted project snapshots, backups and volumes.
4. Release unused project Reserved IPs if allocated manually.
5. Delete dedicated project firewalls after their droplets are removed.
6. Review provider inventory and billing.
7. Close the SSH tunnel.

Do not merely power off droplets when intending to stop usage charges.

Removing a public-key record from the provider account does not revoke a key
already installed on an existing host. Host destruction here removes those
installed keys.

Rotate any additional tokens/passwords that were stored on an incident host.
Mac-only provisioning does not automatically expose Mac AWS credentials.

Keep the local project and GitHub/GitLab repositories.

## 37. Finalize README and verification record

Only after successful live verification and actual cleanup:

```bash
.venv/bin/python scripts/finalize-docs.py \
  --digitalocean-deleted
```

The flag attests that the operator verified DigitalOcean deletion.
It is not an automatic DigitalOcean API check.

The script requires successful two-node/idempotence evidence and AWS cleanup.
It also checks that the implementation matches the verified source revision.

Review the generated README and runbook record.
Add actual troubleshooting and manual-cleanup interventions.

Do not publish private keys, cloud credentials, local state or raw sensitive
logs.

If deployment failed, retain pending/failed status and document cleanup honestly.

When source files change, regenerate the source appendix before final release.

## 38. Git implementation workflow

Use meaningful feature commits and push both remotes:

```bash
git add SPECIFIC_REVIEWED_FILES
git diff --cached --check
git commit -m "type: describe the actual change"

git push origin CURRENT_FEATURE_BRANCH
git push gitlab CURRENT_FEATURE_BRANCH
```

SPECIFIC_REVIEWED_FILES and CURRENT_FEATURE_BRANCH are placeholders.
Do not paste them literally.

Do not force-add ignored state or secrets.

For the original project the main implementation branch was
feature/jenkins-ansible-integration.

If GitLab rejects a push during an internal pre_receive API failure, preserve
the local commit and GitHub copy. Retry the mirror and compare remote hashes.
Do not recreate the commit or force-push as a response to that error.

## 39. Git documentation workflow

Use a documentation branch for the completed runbook:

```bash
git switch -c docs/complete-runbook

git add \
  README.md \
  docs/RUNBOOK.md \
  docs/SOURCE_PROVENANCE.md

git diff --cached --check

git commit -m "docs: provide complete reproducible project runbook"

git push -u origin docs/complete-runbook
git push gitlab docs/complete-runbook
```

If the branch already exists, switch to it instead of trying to create it again.

Commit intended local changes before switching branches.
Never discard documentation simply to make checkout succeed.

## 40. Merge implementation and documentation into develop

After verification, cleanup and review, run from a clean working tree.

This block stops on the first failure:

```bash
bash <<'BASH'
set -euo pipefail

if [ -n "$(git status --porcelain)" ]; then
    echo "Working tree is not clean."
    exit 1
fi

git switch develop
git pull --ff-only origin develop

git merge --no-ff feature/jenkins-ansible-integration \
  -m "merge: integrate verified Jenkins Ansible workflow"

git merge --no-ff docs/complete-runbook \
  -m "merge: integrate complete project runbook"

git push origin develop
git push gitlab develop
BASH
```

If a branch was already merged Git reports it up to date.
Resolve genuine conflicts before continuing.
Do not force-push rejected updates.

## 41. Release main

```bash
bash <<'BASH'
set -euo pipefail

if [ -n "$(git status --porcelain)" ]; then
    echo "Working tree is not clean."
    exit 1
fi

git switch main
git pull --ff-only origin main

git merge --no-ff develop \
  -m "release: complete Ansible integration in Jenkins"

git push origin main
git push gitlab main

git diff --exit-code main develop
git status --short --branch
git log --graph --oneline --decorate -12

git ls-remote --heads origin main develop
git ls-remote --heads gitlab main develop
BASH
```

Expected:

- Clean working tree.
- main/develop file content identical.
- Matching corresponding branch hashes across remotes.

A command reporting Already up to date after an earlier failed checkout is not
proof of the intended release. Use the branch/status checks and stop-on-failure
blocks.

## 42. Tag the release

Check local and remote tags:

```bash
git fetch origin --tags

git tag --list 'v1.0.*'

git ls-remote --tags origin 'v1.0.*'
git ls-remote --tags gitlab 'v1.0.*'
```

For the first completed release, if v1.0.0 does not exist:

```bash
git tag -a v1.0.0 \
  -m "Verified Jenkins Ansible integration with cleanup and full runbook"

git push origin v1.0.0
git push gitlab v1.0.0
```

If v1.0.0 already exists and new documentation is being released, choose a new
available version such as v1.0.1. Do not move the existing tag.

Annotated tags have both a tag-object hash and a peeled commit hash.
Compare matching row types across remotes.

Optionally publish a GitHub release using the existing tag. Describe only actual
verified behavior and link the README/runbook.

## 43. Final completion checklist

- Fresh hosts and replacement credentials used.
- Jenkins bound to localhost and accessed through a tunnel.
- Firewalls restricted to intended SSH sources.
- Exactly two expected managed nodes discovered.
- AWS inventory identity restricted.
- Managed host keys independently verified.
- Docker and Compose checks passed on both nodes.
- Second-run changed=0, failed=0 and unreachable=0.
- Verification commit/time saved.
- Transferred key removed.
- AWS resources and inventory identity removed.
- DigitalOcean project droplets and unwanted associated resources deleted.
- README and runbook reflect actual outcomes.
- Full source/configuration appendix included.
- Implementation and documentation merged into develop/main.
- Both remotes synchronized.
- Final release tag published.

## 44. Primary references

- https://www.jenkins.io/doc/book/installing/linux/
- https://www.jenkins.io/doc/book/system-administration/systemd-services/
- https://plugins.jenkins.io/ssh-steps/
- https://plugins.jenkins.io/ssh-agent/
- https://docs.ansible.com/projects/ansible/latest/collections/amazon/aws/aws_ec2_inventory.html
- https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html
- https://docs.aws.amazon.com/linux/al2023/ug/ec2.html
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connection-prereqs-general.html
- https://github.com/docker/compose/releases
- https://docs.digitalocean.com/support/my-droplet-is-sending-an-outgoing-flood-or-ddos/
- https://docs.digitalocean.com/products/droplets/how-to/destroy/

## 45. Complete source appendix

Each following section contains the complete file contents from the checkout
used to generate this runbook.

README is included as a documentation snapshot.
The runbook does not embed itself, avoiding recursive duplication.

### File: `Jenkinsfile`

````groovy
pipeline {
    agent any

    parameters {
        string(
            name: 'ANSIBLE_SERVER',
            defaultValue: '',
            description: 'Ansible control-server public IP or hostname'
        )
    }

    options {
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('copy files to ansible server') {
            steps {
                script {
                    if (!(params.ANSIBLE_SERVER ==~ /[A-Za-z0-9][A-Za-z0-9.-]*/)) {
                        error('Supply a valid Ansible server IP address or hostname.')
                    }

                    env.CONTROL_HOST = params.ANSIBLE_SERVER
                }

                withCredentials([
                    file(
                        credentialsId: 'ansible-server-known-hosts',
                        variable: 'CONTROL_KNOWN_HOSTS'
                    )
                ]) {
                    sshagent(['ansible-server-key']) {
                        sh '''
                            set -eu

                            git rev-parse HEAD > source-revision.txt

                            scp \
                                -o BatchMode=yes \
                                -o StrictHostKeyChecking=yes \
                                -o UserKnownHostsFile="$CONTROL_KNOWN_HOSTS" \
                                ansible/ansible.cfg \
                                ansible/my-playbook.yaml \
                                ansible/inventory_aws_ec2.yaml \
                                ansible/requirements.txt \
                                ansible/requirements.yml \
                                scripts/check-inventory.py \
                                scripts/check-results.py \
                                source-revision.txt \
                                "root@$CONTROL_HOST:/root/"
                        '''

                        withCredentials([
                            sshUserPrivateKey(
                                credentialsId: 'ec2-server-key',
                                keyFileVariable: 'EC2_KEY'
                            )
                        ]) {
                            script {
                                env.EC2_KEY_TRANSFER_STARTED = 'true'
                            }

                            sh '''
                                set +x
                                set -eu

                                ssh \
                                    -o BatchMode=yes \
                                    -o StrictHostKeyChecking=yes \
                                    -o UserKnownHostsFile="$CONTROL_KNOWN_HOSTS" \
                                    "root@$CONTROL_HOST" \
                                    'umask 077; cat > /root/ssh-key.pem' \
                                    < "$EC2_KEY"
                            '''
                        }
                    }
                }
            }
        }

        stage('execute ansible playbook') {
            steps {
                script {
                    withCredentials([
                        sshUserPrivateKey(
                            credentialsId: 'ansible-server-key',
                            keyFileVariable: 'CONTROL_KEY',
                            usernameVariable: 'CONTROL_USER',
                            passphraseVariable: 'CONTROL_PASSPHRASE'
                        ),
                        file(
                            credentialsId: 'ansible-server-known-hosts',
                            variable: 'CONTROL_KNOWN_HOSTS'
                        )
                    ]) {
                        if (env.CONTROL_USER != 'root') {
                            error('The Ansible control credential must use root.')
                        }

                        def remote = [
                            name: 'ansible-server',
                            host: params.ANSIBLE_SERVER,
                            user: env.CONTROL_USER,
                            identityFile: env.CONTROL_KEY,
                            passphrase: env.CONTROL_PASSPHRASE,
                            knownHosts: env.CONTROL_KNOWN_HOSTS,
                            allowAnyHosts: false
                        ]

                        sshScript(
                            remote: remote,
                            script: 'prepare-ansible-server.sh'
                        )

                        sshCommand(
                            remote: remote,
                            command: '''bash -lc '
                                set -euo pipefail
                                cd /root

                                export PATH=/opt/ansible-project/bin:$PATH
                                export ANSIBLE_CONFIG=/root/ansible.cfg
                                export ANSIBLE_NOCOLOR=1
                                export ANSIBLE_STDOUT_CALLBACK=default

                                rm -f project-verification.json

                                ansible-inventory --list > project-inventory.json

                                python check-inventory.py project-inventory.json

                                ansible-playbook my-playbook.yaml |
                                    tee playbook-first.log

                                ansible-playbook my-playbook.yaml |
                                    tee playbook-second.log

                                python check-results.py
                            ' '''
                        )
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                if (env.EC2_KEY_TRANSFER_STARTED == 'true') {
                    withCredentials([
                        file(
                            credentialsId: 'ansible-server-known-hosts',
                            variable: 'CONTROL_KNOWN_HOSTS'
                        )
                    ]) {
                        sshagent(['ansible-server-key']) {
                            sh '''
                                set -eu

                                ssh \
                                    -o BatchMode=yes \
                                    -o StrictHostKeyChecking=yes \
                                    -o UserKnownHostsFile="$CONTROL_KNOWN_HOSTS" \
                                    "root@$CONTROL_HOST" \
                                    'rm -f /root/ssh-key.pem'
                            '''
                        }
                    }
                }
            }
        }
    }
}
````

### File: `prepare-ansible-server.sh`

````bash
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
````

### File: `ansible/ansible.cfg`

````ini
[defaults]
inventory = ./inventory_aws_ec2.yaml
remote_user = ec2-user
private_key_file = /root/ssh-key.pem
host_key_checking = True
retry_files_enabled = False
timeout = 30
interpreter_python = /usr/bin/python3

[inventory]
any_unparsed_is_failed = True

[ssh_connection]
ssh_args = -o BatchMode=yes -o StrictHostKeyChecking=yes -o ControlMaster=auto -o ControlPersist=60s
````

### File: `ansible/inventory_aws_ec2.yaml`

````yaml
---
plugin: amazon.aws.aws_ec2

regions:
  - ca-central-1

filters:
  instance-state-name: running
  "tag:Project": ansible-integration-in-jenkins
  "tag:Role": app
  "tag:Deployment": capstone-v2

hostnames:
  - public-ip-address

keyed_groups:
  - key: tags
    prefix: tag
  - key: instance_type
    prefix: instance_type
````

### File: `ansible/my-playbook.yaml`

````yaml
---
- name: Install and start Docker
  hosts: all
  become: true
  tasks:
    - name: Require Amazon Linux 2023
      ansible.builtin.assert:
        that:
          - ansible_facts.distribution == 'Amazon'
          - ansible_facts.distribution_major_version == '2023'

    - name: Install Docker
      ansible.builtin.dnf:
        name: docker
        state: present
        update_cache: true

    - name: Enable and start Docker
      ansible.builtin.systemd_service:
        name: docker
        state: started
        enabled: true

- name: Install Docker Compose for the login user
  hosts: all
  vars:
    compose_version: v5.6.0

  tasks:
    - name: Create the Docker CLI plugin directory
      ansible.builtin.file:
        path: /home/ec2-user/.docker/cli-plugins
        state: directory
        mode: '0755'

    - name: Detect the managed-node binary platform
      ansible.builtin.command: uname -m
      register: remote_arch
      changed_when: false

    - name: Download the pinned Docker Compose binary
      ansible.builtin.get_url:
        url: "https://github.com/docker/compose/releases/download/{{ compose_version }}/docker-compose-linux-{{ remote_arch.stdout }}"
        checksum: "sha256:https://github.com/docker/compose/releases/download/{{ compose_version }}/docker-compose-linux-{{ remote_arch.stdout }}.sha256"
        dest: /home/ec2-user/.docker/cli-plugins/docker-compose
        mode: '0755'

    - name: Verify the Compose CLI plugin
      ansible.builtin.command: docker compose version
      register: compose_check
      changed_when: false

    - name: Verify the Docker daemon
      become: true
      ansible.builtin.command: docker info
      changed_when: false

    - name: Verify the pinned Compose version
      ansible.builtin.assert:
        that:
          - compose_version in compose_check.stdout
````

### File: `ansible/requirements.txt`

````text
ansible-core==2.20.10
boto3==1.43.114
botocore==1.43.114
````

### File: `ansible/requirements.yml`

````yaml
---
collections:
  - name: amazon.aws
    version: "11.4.0"
````

### File: `scripts/manage-aws.py`

````python
#!/usr/bin/env python3
"""Project-only AWS provisioning, inventory credentials, host trust and teardown."""

import argparse
import base64
import datetime
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid

import boto3
from botocore.exceptions import ClientError


REGION = "ca-central-1"
PROJECT = "ansible-integration-in-jenkins"
DEPLOYMENT = "capstone-v2"

USER = "ansible-project-inventory-v2"
POLICY = "ProjectInventoryReadOnly"

KEY_NAME = "ansible-project-ec2-v2"
SG_NAME = "ansible-project-app-v2"

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / ".local"
STATE = LOCAL / "aws-state.json"
ACCESS = LOCAL / "inventory-access-key.json"


def save(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)


def project_tags():
    return [
        {"Key": "Project", "Value": PROJECT},
        {"Key": "Deployment", "Value": DEPLOYMENT},
    ]


def run(command, **kwargs):
    return subprocess.run(command, check=True, **kwargs)


def ssh_args(control):
    return [
        "ssh",
        "-i",
        str(Path.home() / ".ssh/ansible-project-control-v2"),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        f"root@{control}",
    ]


def instances_by_id(ec2, ids):
    response = ec2.describe_instances(InstanceIds=ids)
    return [
        instance
        for reservation in response["Reservations"]
        for instance in reservation["Instances"]
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "action",
        choices=["provision", "credentials", "hostkeys", "status", "destroy"],
    )

    parser.add_argument("--control")
    parser.add_argument("--confirm")

    args = parser.parse_args()

    os.umask(0o077)
    LOCAL.mkdir(mode=0o700, exist_ok=True)
    os.chdir(ROOT)

    session = boto3.Session(region_name=REGION)
    ec2 = session.client("ec2")
    iam = session.client("iam")

    account = session.client("sts").get_caller_identity()["Account"]
    state = json.loads(STATE.read_text()) if STATE.exists() else {}

    if state and state["account"] != account:
        raise SystemExit("AWS account differs from saved project state.")

    if args.action not in ["provision", "status"] and not state:
        raise SystemExit("No project state found. Provision first.")

    if args.control:
        ipaddress.IPv4Address(args.control)

    if args.action == "provision":
        if not args.control:
            raise SystemExit("--control is required.")

        if state.get("destroyed_at"):
            raise SystemExit(
                "Deployment already destroyed. Archive .local before a new deployment."
            )

        if state and state.get("control") != args.control:
            raise SystemExit("Control IP differs from the saved deployment.")

        if not state:
            state = {
                "account": account,
                "region": REGION,
                "control": args.control,
                "client_token": str(uuid.uuid4()),
            }
            save(STATE, state)

        vpcs = ec2.describe_vpcs(
            Filters=[{"Name": "is-default", "Values": ["true"]}]
        )["Vpcs"]

        if len(vpcs) != 1:
            raise SystemExit("Exactly one default VPC is required.")

        vpc = vpcs[0]["VpcId"]

        subnets = ec2.describe_subnets(
            Filters=[
                {"Name": "vpc-id", "Values": [vpc]},
                {"Name": "default-for-az", "Values": ["true"]},
            ]
        )["Subnets"]

        subnet = next(
            (
                candidate
                for candidate in sorted(
                    subnets, key=lambda item: item["AvailabilityZone"]
                )
                if candidate.get("MapPublicIpOnLaunch")
                and candidate["AvailableIpAddressCount"] >= 2
            ),
            None,
        )

        if not subnet:
            raise SystemExit("No suitable public default subnet found.")

        tables = ec2.describe_route_tables(
            Filters=[
                {
                    "Name": "association.subnet-id",
                    "Values": [subnet["SubnetId"]],
                }
            ]
        )["RouteTables"]

        if not tables:
            tables = ec2.describe_route_tables(
                Filters=[
                    {"Name": "vpc-id", "Values": [vpc]},
                    {"Name": "association.main", "Values": ["true"]},
                ]
            )["RouteTables"]

        internet_route = any(
            route.get("DestinationCidrBlock") == "0.0.0.0/0"
            and route.get("GatewayId", "").startswith("igw-")
            and route.get("State") == "active"
            for table in tables
            for route in table["Routes"]
        )

        if not internet_route:
            raise SystemExit("Selected subnet has no active internet-gateway route.")

        state.update(vpc=vpc, subnet=subnet["SubnetId"])
        save(STATE, state)

        public_key = (
            Path.home() / ".ssh/ansible-project-ec2-v2.pub"
        ).read_text().strip()

        try:
            key = ec2.describe_key_pairs(
                KeyNames=[KEY_NAME],
                IncludePublicKey=True,
            )["KeyPairs"][0]

            if key.get("PublicKey", "").split()[:2] != public_key.split()[:2]:
                raise SystemExit("Existing AWS key has different public-key contents.")

            if not state.get("key_id"):
                raise SystemExit("Existing AWS key is not owned by recorded state.")

        except ClientError as error:
            if error.response["Error"]["Code"] != "InvalidKeyPair.NotFound":
                raise

            key = ec2.import_key_pair(
                KeyName=KEY_NAME,
                PublicKeyMaterial=public_key.encode(),
                TagSpecifications=[
                    {
                        "ResourceType": "key-pair",
                        "Tags": project_tags(),
                    }
                ],
            )

        state.update(key_name=KEY_NAME, key_id=key["KeyPairId"])
        save(STATE, state)

        if not state.get("sg_id"):
            existing = ec2.describe_security_groups(
                Filters=[
                    {"Name": "vpc-id", "Values": [vpc]},
                    {"Name": "group-name", "Values": [SG_NAME]},
                ]
            )["SecurityGroups"]

            if existing:
                raise SystemExit(
                    "Security-group name exists without saved ownership."
                )

            group = ec2.create_security_group(
                GroupName=SG_NAME,
                VpcId=vpc,
                Description="Project SSH from Ansible control only",
                TagSpecifications=[
                    {
                        "ResourceType": "security-group",
                        "Tags": project_tags(),
                    }
                ],
            )

            state["sg_id"] = group["GroupId"]
            save(STATE, state)

        permission = {
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22,
            "IpRanges": [
                {
                    "CidrIp": args.control + "/32",
                    "Description": "Ansible control",
                }
            ],
        }

        try:
            ec2.authorize_security_group_ingress(
                GroupId=state["sg_id"],
                IpPermissions=[permission],
            )

        except ClientError as error:
            if error.response["Error"]["Code"] != "InvalidPermission.Duplicate":
                raise

        if "ami" not in state:
            state["ami"] = session.client("ssm").get_parameter(
                Name=(
                    "/aws/service/ami-amazon-linux-latest/"
                    "al2023-ami-kernel-default-x86_64"
                )
            )["Parameter"]["Value"]

            save(STATE, state)

        if not state.get("instance_ids"):
            existing = ec2.describe_instances(
                Filters=[
                    {"Name": "tag:Project", "Values": [PROJECT]},
                    {"Name": "tag:Deployment", "Values": [DEPLOYMENT]},
                    {
                        "Name": "instance-state-name",
                        "Values": ["pending", "running", "stopping", "stopped"],
                    },
                ]
            )

            recovered = [
                instance
                for reservation in existing["Reservations"]
                for instance in reservation["Instances"]
            ]

            if recovered:
                if len(recovered) != 2 or any(
                    instance.get("ClientToken") != state["client_token"]
                    for instance in recovered
                ):
                    raise SystemExit(
                        "Existing project nodes do not match this deployment token."
                    )

                state["instance_ids"] = [
                    instance["InstanceId"] for instance in recovered
                ]

            else:
                image = ec2.describe_images(
                    ImageIds=[state["ami"]]
                )["Images"][0]

                launched = ec2.run_instances(
                    ImageId=state["ami"],
                    InstanceType="t3.micro",
                    MinCount=2,
                    MaxCount=2,
                    ClientToken=state["client_token"],
                    KeyName=KEY_NAME,
                    CreditSpecification={"CpuCredits": "standard"},
                    NetworkInterfaces=[
                        {
                            "DeviceIndex": 0,
                            "SubnetId": state["subnet"],
                            "Groups": [state["sg_id"]],
                            "AssociatePublicIpAddress": True,
                        }
                    ],
                    MetadataOptions={
                        "HttpTokens": "required",
                        "HttpEndpoint": "enabled",
                    },
                    BlockDeviceMappings=[
                        {
                            "DeviceName": image["RootDeviceName"],
                            "Ebs": {
                                "VolumeSize": 8,
                                "VolumeType": "gp3",
                                "Encrypted": True,
                                "DeleteOnTermination": True,
                            },
                        }
                    ],
                    TagSpecifications=[
                        {
                            "ResourceType": "instance",
                            "Tags": project_tags()
                            + [
                                {"Key": "Role", "Value": "app"},
                                {
                                    "Key": "Name",
                                    "Value": "ansible-project-node-v2",
                                },
                            ],
                        },
                        {
                            "ResourceType": "volume",
                            "Tags": project_tags(),
                        },
                    ],
                )

                state["instance_ids"] = [
                    instance["InstanceId"]
                    for instance in launched["Instances"]
                ]

            save(STATE, state)

        print("Waiting for EC2 status checks...", flush=True)

        ec2.get_waiter("instance_status_ok").wait(
            InstanceIds=state["instance_ids"]
        )

        instances = instances_by_id(ec2, state["instance_ids"])

        for index, instance in enumerate(
            sorted(instances, key=lambda item: item["InstanceId"]),
            start=1,
        ):
            ec2.create_tags(
                Resources=[instance["InstanceId"]],
                Tags=[
                    {
                        "Key": "Name",
                        "Value": f"ansible-project-node-v2-{index}",
                    }
                ],
            )

        state["nodes"] = [
            {
                "id": instance["InstanceId"],
                "ip": instance["PublicIpAddress"],
            }
            for instance in instances
        ]

        save(STATE, state)
        print(json.dumps(state["nodes"], indent=2))

    elif args.action == "credentials":
        if state.get("destroyed_at"):
            raise SystemExit("Deployment is already destroyed.")

        if not state.get("iam_owned"):
            try:
                iam.get_user(UserName=USER)

            except ClientError as error:
                if error.response["Error"]["Code"] != "NoSuchEntity":
                    raise

                iam.create_user(
                    UserName=USER,
                    Tags=project_tags(),
                )

                state["iam_owned"] = True
                save(STATE, state)

            else:
                raise SystemExit(
                    "IAM user exists without saved ownership. Inspect it first."
                )

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ec2:DescribeInstances",
                        "ec2:DescribeTags",
                        "ec2:DescribeRegions",
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "aws:RequestedRegion": REGION,
                        },
                        "IpAddress": {
                            "aws:SourceIp": state["control"] + "/32",
                        },
                    },
                }
            ],
        }

        iam.put_user_policy(
            UserName=USER,
            PolicyName=POLICY,
            PolicyDocument=json.dumps(policy),
        )

        if not ACCESS.exists():
            existing_keys = iam.list_access_keys(
                UserName=USER
            )["AccessKeyMetadata"]

            if existing_keys:
                raise SystemExit(
                    "An access key exists but its local secret file is missing. "
                    "Revoke that dedicated key before retrying."
                )

            access = iam.create_access_key(
                UserName=USER
            )["AccessKey"]

            save(
                ACCESS,
                {
                    "AccessKeyId": access["AccessKeyId"],
                    "SecretAccessKey": access["SecretAccessKey"],
                },
            )

        access = json.loads(ACCESS.read_text())

        credentials = (
            "[default]\n"
            "aws_access_key_id = " + access["AccessKeyId"] + "\n"
            "aws_secret_access_key = " + access["SecretAccessKey"] + "\n"
        )

        run(
            ssh_args(state["control"])
            + [
                "install -d -m 700 /root/.aws; "
                "umask 077; cat > /root/.aws/credentials"
            ],
            input=credentials,
            text=True,
        )

        run(
            ssh_args(state["control"])
            + [
                "umask 077; "
                "printf '[default]\\nregion = ca-central-1\\n' "
                "> /root/.aws/config"
            ]
        )

        print("Dedicated inventory credentials installed. Secrets were not printed.")

    elif args.action == "hostkeys":
        if len(state.get("nodes", [])) != 2:
            raise SystemExit("Provision two project nodes first.")

        verified_lines = []

        for node in state["nodes"]:
            console = ec2.get_console_output(
                InstanceId=node["id"],
                Latest=True,
            ).get("Output", "")

            if "SHA256:" not in console:
                try:
                    console = base64.b64decode(console).decode(
                        "utf-8", errors="replace"
                    )
                except Exception:
                    pass

            scan = run(
                ssh_args(state["control"])
                + [f"ssh-keyscan -T 15 -t ed25519 {node['ip']}"],
                capture_output=True,
                text=True,
            ).stdout

            lines = [
                line
                for line in scan.splitlines()
                if line.startswith(node["ip"] + " ssh-ed25519 ")
            ]

            if len(lines) != 1:
                raise SystemExit(
                    "No unique host key returned. Check network access."
                )

            candidate = LOCAL / "host-key.candidate"
            candidate.write_text(lines[0] + "\n")

            fingerprint = run(
                ["ssh-keygen", "-lf", str(candidate)],
                capture_output=True,
                text=True,
            ).stdout

            match = re.search(r"SHA256:[A-Za-z0-9+/]+", fingerprint)

            if not match or match.group() not in console:
                raise SystemExit(
                    "Fingerprint not confirmed by AWS console output. "
                    "Retry after boot logs arrive; do not bypass verification."
                )

            print(node["id"], node["ip"], match.group(), "verified")
            verified_lines.append(lines[0])

        (LOCAL / "host-key.candidate").unlink(missing_ok=True)

        hosts = LOCAL / "ec2-known-hosts"
        hosts.write_text("\n".join(verified_lines) + "\n")

        run(
            ssh_args(state["control"])
            + [
                "install -d -m 700 /root/.ssh; "
                "umask 077; cat > /root/.ssh/known_hosts"
            ],
            input=hosts.read_text(),
            text=True,
        )

        run(
            ssh_args(state["control"])
            + [
                "umask 077; cat > /root/expected-instance-ids.json"
            ],
            input=json.dumps(state["instance_ids"]) + "\n",
            text=True,
        )

        print("Verified host keys and expected instance IDs installed.")

    elif args.action == "status":
        if not state:
            print("No local project state.")
            return

        print(
            json.dumps(
                {
                    key: value
                    for key, value in state.items()
                    if key != "client_token"
                },
                indent=2,
            )
        )

        if state.get("instance_ids"):
            for instance in instances_by_id(ec2, state["instance_ids"]):
                print(
                    instance["InstanceId"],
                    instance["State"]["Name"],
                    instance.get("PublicIpAddress", ""),
                )

    elif args.action == "destroy":
        if args.confirm != PROJECT:
            raise SystemExit(
                "--confirm ansible-integration-in-jenkins is required."
            )

        if state.get("iam_owned"):
            try:
                for key in iam.list_access_keys(
                    UserName=USER
                )["AccessKeyMetadata"]:
                    iam.delete_access_key(
                        UserName=USER,
                        AccessKeyId=key["AccessKeyId"],
                    )

                try:
                    iam.delete_user_policy(
                        UserName=USER,
                        PolicyName=POLICY,
                    )

                except ClientError as error:
                    if error.response["Error"]["Code"] != "NoSuchEntity":
                        raise

                iam.delete_user(UserName=USER)

            except ClientError as error:
                if error.response["Error"]["Code"] != "NoSuchEntity":
                    raise

            ACCESS.unlink(missing_ok=True)

        if state.get("instance_ids"):
            ec2.terminate_instances(
                InstanceIds=state["instance_ids"]
            )

            print("Waiting for instance termination...", flush=True)

            ec2.get_waiter("instance_terminated").wait(
                InstanceIds=state["instance_ids"]
            )

        if state.get("sg_id"):
            for attempt in range(12):
                try:
                    ec2.delete_security_group(
                        GroupId=state["sg_id"]
                    )
                    break

                except ClientError as error:
                    code = error.response["Error"]["Code"]

                    if code == "InvalidGroup.NotFound":
                        break

                    if code != "DependencyViolation" or attempt == 11:
                        raise

                    time.sleep(5)

        if state.get("key_id"):
            ec2.delete_key_pair(
                KeyPairId=state["key_id"]
            )

        volumes = ec2.describe_volumes(
            Filters=[
                {"Name": "tag:Project", "Values": [PROJECT]},
                {"Name": "tag:Deployment", "Values": [DEPLOYMENT]},
            ]
        )["Volumes"]

        if volumes:
            raise SystemExit(
                "Tagged volumes remain: "
                + ", ".join(volume["VolumeId"] for volume in volumes)
                + ". Inspect before finalizing cleanup."
            )

        state["destroyed_at"] = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()

        save(STATE, state)

        print(
            "Project EC2 nodes, security group, AWS key pair and "
            "inventory IAM user/keys removed; no tagged volumes remain."
        )

        print(
            "Delete the two DigitalOcean project droplets and "
            "unwanted associated resources separately."
        )


if __name__ == "__main__":
    main()
````

### File: `scripts/check-inventory.py`

````python
#!/usr/bin/env python3

import json
import subprocess
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    inventory = json.load(stream)

hosts = inventory.get("_meta", {}).get("hostvars", {})

if len(hosts) != 2:
    raise SystemExit(
        f"Expected exactly two project nodes; discovered {len(hosts)}"
    )

with open("/root/expected-instance-ids.json", encoding="utf-8") as stream:
    expected_ids = set(json.load(stream))

actual_ids = {
    variables.get("instance_id")
    for variables in hosts.values()
}

if actual_ids != expected_ids:
    raise SystemExit(
        "Inventory instance IDs differ from the provisioned project nodes"
    )

for host in hosts:
    subprocess.run(
        [
            "ssh-keygen",
            "-F",
            host,
            "-f",
            "/root/.ssh/known_hosts",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )

print(
    "Inventory verified: exactly two expected nodes with trusted SSH host keys"
)
````

### File: `scripts/check-results.py`

````python
#!/usr/bin/env python3

import datetime
import json
from pathlib import Path
import re

inventory = json.loads(
    Path("/root/project-inventory.json").read_text()
)

expected = set(inventory["_meta"]["hostvars"])

pattern = re.compile(
    r"^([^\s]+)\s*:\s*ok=(\d+)\s+changed=(\d+)"
    r"\s+unreachable=(\d+)\s+failed=(\d+)",
    re.MULTILINE,
)

results = {}

for name in ["first", "second"]:
    log = Path(f"/root/playbook-{name}.log").read_text()

    recap = {
        match[0]: dict(
            zip(
                ["ok", "changed", "unreachable", "failed"],
                map(int, match[1:]),
            )
        )
        for match in pattern.findall(log)
    }

    if set(recap) != expected:
        raise SystemExit(
            f"{name}: recap host set does not equal expected inventory"
        )

    if any(
        value["failed"]
        or value["unreachable"]
        or value["ok"] == 0
        for value in recap.values()
    ):
        raise SystemExit(
            f"{name}: deployment or verification failed"
        )

    if name == "second" and any(
        value["changed"] for value in recap.values()
    ):
        raise SystemExit(
            "Second run changed resources; investigate before claiming idempotence"
        )

    results[name] = recap

report = {
    "verified_at_utc": datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat(),
    "source_commit": Path(
        "/root/source-revision.txt"
    ).read_text().strip(),
    "node_count": len(expected),
    "docker_and_compose_checks": "passed in playbook",
    "idempotence": "passed",
    "recaps": results,
}

Path("/root/project-verification.json").write_text(
    json.dumps(report, indent=2) + "\n"
)

print(
    "Two-node deployment, Docker/Compose checks and "
    "second-run idempotence passed"
)
````

### File: `scripts/finalize-docs.py`

````python
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
````

### File: `Dockerfile`

````dockerfile
FROM eclipse-temurin:17-jre-jammy

WORKDIR /app

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

COPY --chown=app:app target/java-maven-app-*.jar /app/app.jar

USER app

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
````

### File: `.dockerignore`

````text
**
!Dockerfile
!target/
!target/java-maven-app-*.jar
````

### File: `.gitignore`

````text
.idea/*
target
# macOS and editors
.DS_Store
.idea/
.vscode/
*.iml

# Build output
target/
*.log

# Python and Ansible
.venv/
venv/
__pycache__/
*.py[cod]
*.retry
.ansible/

# Local credentials and environment files
.env
.env.*
!.env.example
*.pem
*.key
id_rsa*
id_ed25519*
.aws/
secrets/
.vault-password*

.local/

source-revision.txt
````

### File: `pom.xml`

````xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
                             http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>java-maven-app</artifactId>
    <version>1.1.0-SNAPSHOT</version>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <version>3.5.5</version>
                <executions>
                    <execution>
                        <goals>
                            <goal>repackage</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>

            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>17</source>
                    <target>17</target>
                </configuration>
            </plugin>
        </plugins>
    </build>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
            <version>3.5.5</version>
        </dependency>

        <dependency>
            <groupId>net.logstash.logback</groupId>
            <artifactId>logstash-logback-encoder</artifactId>
            <version>9.0</version>
        </dependency>

        <dependency>
            <groupId>javax.annotation</groupId>
            <artifactId>javax.annotation-api</artifactId>
            <version>1.3.2</version>
        </dependency>

        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

</project>
````

### File: `script.groovy`

````groovy
def buildJar() {
    echo 'building the application...'
    sh 'mvn package'
}

def buildImage() {
    echo "building the docker image..."
    withCredentials([usernamePassword(credentialsId: 'docker-hub-repo', passwordVariable: 'PASS', usernameVariable: 'USER')]) {
        sh 'docker build -t nanatwn/demo-app:jma-2.0 .'
        sh 'echo $PASS | docker login -u $USER --password-stdin'
        sh 'docker push nanatwn/demo-app:jma-2.0'
    }
}

def deployApp() {
    echo 'deploying the application...'
}

return this
````

### File: `src/main/java/com/example/Application.java`

````java
package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import jakarta.annotation.PostConstruct;

@SpringBootApplication
public class Application {

    public static void main(String[] args)
    {
        SpringApplication.run(Application.class, args);
    }

    @PostConstruct
    public void init()
    {
        Logger log = LoggerFactory.getLogger(Application.class);
        log.info("Java app started");
    }

    public String getStatus() {
        return "OK";
    }
}
````

### File: `src/main/resources/static/index.html`

````html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MyApp</title>
</head>
<body>
<h1>Welcome to Java Maven Application</h1>
<!-- add image here  <img src="" width="" /> -->
</body>
</html>
````

### File: `README.md`

````markdown
# Ansible Integration in Jenkins

DevOps capstone integrating Jenkins with a dedicated Ansible control server
to configure and deploy a containerized Java application to two AWS EC2 nodes.

## Status

Starting application imported; independent repository setup in progress.
Infrastructure has not been provisioned and deployment is not yet verified.

## Attribution

Starting code and training material: TechWorld with Nana.
Independent DevOps implementation and documentation: Gafari Oladele Salaudeen.

See [source provenance](docs/SOURCE_PROVENANCE.md) for the upstream repository,
starting branch, baseline commit and attribution details.
````

### File: `docs/SOURCE_PROVENANCE.md`

````markdown
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
````
