"""Validate a real generated RO-Crate for the e2e workflow.

Usage: python validate_crate.py <ro-crate-metadata.json> <expected-strategy> <expected-framework-slug>
Exits non-zero (failing the CI job) if the crate is missing or incomplete, or if
rocrate-validator reports it is not valid RO-Crate 1.2 or Process Run Crate.
Needs rocrate-validator installed (see realapps.yml).
"""

import json
import sys
from pathlib import Path

from rocrate_validator import models, services


def validate(crate_dir, profile, **settings):
    """Validate at REQUIRED level, offline; return the failures as readable lines."""
    result = services.validate(services.ValidationSettings(
        rocrate_uri=str(crate_dir),
        profile_identifier=profile,
        requirement_severity=models.Severity.REQUIRED,
        offline=True,
        extra_checks=True,
        **settings,
    ))
    issues = [f"{i.check.identifier}: {i.message}" for i in result.get_issues()]
    issues += [f"{e.identifier} (extra): {e.message}" for e in result.extra_checks]
    return issues


def main():
    if len(sys.argv) != 4:
        sys.exit(f"usage: {sys.argv[0]} <metadata.json> <strategy> <framework-slug>")
    path, expected_strategy, expected_fw = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        graph = json.loads(open(path).read())["@graph"]
    except FileNotFoundError:
        sys.exit(f"FAIL: crate not found at {path} (did the run produce one?)")
    g = {e["@id"]: e for e in graph}

    crate_dir = Path(path).parent
    ro_crate_issues = validate(crate_dir, "ro-crate-1.2")
    # Process Run Crate 0.5 inherits RO-Crate 1.1 checks that clash with a 1.2
    # crate; the RO-Crate 1.2 check above already covers the base rules.
    process_run_issues = validate(crate_dir, "process-run-crate-0.5",
                                  disable_inherited_profiles_issue_reporting=True)

    checks = {
        "root mentions the run (#1)": g["./"].get("mentions") == [{"@id": "#fl-run"}],
        "run completed": g.get("#fl-run", {}).get("actionStatus", {}).get("@id", "").endswith("CompletedActionStatus"),
        f"strategy is {expected_strategy} (#2)": g.get("#fl-strategy", {}).get("name") == expected_strategy,
        f"framework #framework-{expected_fw} captured (#4)": f"#framework-{expected_fw}" in g,
        "at least one metric (#3)": any(k.startswith("#metric") for k in g),
        "endTime set (record_result ran)": bool(g.get("#fl-run", {}).get("endTime")),
        "license + author + agent (#5)": all([
            g["./"].get("license"), g["./"].get("author"), g.get("#fl-run", {}).get("agent"),
        ]),
        "valid RO-Crate 1.2 (rocrate-validator)": not ro_crate_issues,
        "satisfies Process Run Crate (rocrate-validator)": not process_run_issues,
    }

    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    for issue in ro_crate_issues + process_run_issues:
        print(f"      {issue}")
    if failed:
        sys.exit(f"FAIL: {len(failed)} check(s) failed: {failed}")
    print(f"OK: valid end-to-end crate ({expected_strategy} / {expected_fw}).")


if __name__ == "__main__":
    main()
