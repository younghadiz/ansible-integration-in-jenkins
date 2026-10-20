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
