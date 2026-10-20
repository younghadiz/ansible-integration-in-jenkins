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
