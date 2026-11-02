"""
Checks that the crates flwrCrate writes are valid RO-Crate 1.2 and satisfy the
Process Run Crate profile. Validation runs offline and reads only
rocrate-validator's cache, so fill it once before running the tests:
rocrate-validator cache warm -p ro-crate-1.2 -p process-run-crate-0.5
"""

from flwrcrate.crate_builder import build_crate
from flwrcrate.validation import report, validate
from tests.test_crate_builder import _minimal_capture

AUTHOR = {"name": "john", "orcid": "https://orcid.org/0000-0000-0000-0001"}
LICENSE = "http://spdx.org/licenses/MIT"


def test_crate_is_valid_ro_crate_1_2(tmp_path):
    crate_dir = build_crate(_minimal_capture(), crate_dir=tmp_path / "ro-crate",
                            author=AUTHOR, license=LICENSE)
    result = validate(crate_dir, "ro-crate-1.2")
    assert result.passed(), report(result)
    assert not result.extra_checks, report(result)


def test_crate_satisfies_process_run_crate(tmp_path):
    crate_dir = build_crate(_minimal_capture(), crate_dir=tmp_path / "ro-crate",
                            author=AUTHOR, license=LICENSE)
    # The validator only has a Process Run Crate 0.5 profile, which inherits
    # RO-Crate 1.1 checks that clash with a 1.2 crate. The test above already
    # covers the base RO-Crate rules, so only report the profile's own checks.
    result = validate(crate_dir, "process-run-crate-0.5",
                      disable_inherited_profiles_issue_reporting=True)
    assert result.passed(), report(result)
    assert not result.extra_checks, report(result)


def test_missing_license_is_reported(tmp_path):
    crate_dir = build_crate(_minimal_capture(), crate_dir=tmp_path / "ro-crate",
                            author=AUTHOR)
    result = validate(crate_dir, "ro-crate-1.2")
    assert not result.passed()
    assert any(i.violatingProperty == "http://schema.org/license"
               for i in result.get_issues()), report(result)
    assert "ro-crate-1.2_13.3" in report(result)
