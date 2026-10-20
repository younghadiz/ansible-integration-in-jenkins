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
