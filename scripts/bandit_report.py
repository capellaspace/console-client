#!/usr/bin/env python3
"""Format bandit JSON output as a compact table. Exits non-zero if medium+ issues found."""
import json
import sys

data = json.load(sys.stdin)
issues = data.get("results", [])

if not issues:
    print("bandit: no issues found")
    sys.exit(0)

print(f"{'ID':<8} {'SEV':<6} {'CONF':<6} {'LOCATION':<50} {'TEST'}")
print("-" * 90)
for i in sorted(issues, key=lambda x: x["issue_severity"], reverse=True):
    loc = i["filename"].replace("capella_console_client/", "") + ":" + str(i["line_number"])
    print(f"{i['test_id']:<8} {i['issue_severity'][:3]:<6} {i['issue_confidence'][:3]:<6} {loc:<50} {i['test_name']}")

medium_plus = [i for i in issues if i["issue_severity"] in ("MEDIUM", "HIGH")]
if medium_plus:
    print(f"\nbandit: {len(medium_plus)} medium/high severity issue(s) found")
    sys.exit(1)
