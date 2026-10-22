"""
Checks that the crates flwrCrate writes are valid RO-Crate 1.2 and satisfy the
Process Run Crate profile. Validation runs offline and reads only
rocrate-validator's cache, so fill it once before running the tests:
rocrate-validator cache warm -p ro-crate-1.2 -p process-run-crate-0.5
"""

from rocrate_validator import models, services

from flwrcrate.crate_builder import build_crate
from tests.test_crate_builder import _minimal_capture

AUTHOR = {"name": "john", "orcid": "https://orcid.org/0000-0000-0000-0001"}
LICENSE = "http://spdx.org/licenses/MIT"


def _validate(crate_dir, profile, **settings):
    return services.validate(services.ValidationSettings(
        rocrate_uri=str(crate_dir),
        profile_identifier=profile,
        requirement_severity=models.Severity.REQUIRED,
        offline=True,
        extra_checks=True,
        **settings,
    ))


def _issues(result):
    """Readable list of failures and extra-check findings, shown if an assertion fails."""
    lines = [f"{i.check.identifier}: {i.message}" for i in result.get_issues()]
    lines += [f"{e.identifier} (extra): {e.message}" for e in result.extra_checks]
    return "\n".join(lines)


def test_crate_is_valid_ro_crate_1_2(tmp_path):
    crate_dir = build_crate(_minimal_capture(), crate_dir=tmp_path / "ro-crate",
                            author=AUTHOR, license=LICENSE)
    result = _validate(crate_dir, "ro-crate-1.2")
    assert result.passed(), _issues(result)
    assert not result.extra_checks, _issues(result)


def test_crate_satisfies_process_run_crate(tmp_path):
    crate_dir = build_crate(_minimal_capture(), crate_dir=tmp_path / "ro-crate",
                            author=AUTHOR, license=LICENSE)
    # The validator only has a Process Run Crate 0.5 profile, which inherits
    # RO-Crate 1.1 checks that clash with a 1.2 crate. The test above already
    # covers the base RO-Crate rules, so only report the profile's own checks.
    result = _validate(crate_dir, "process-run-crate-0.5",
                       disable_inherited_profiles_issue_reporting=True)
    assert result.passed(), _issues(result)
    assert not result.extra_checks, _issues(result)


def test_missing_license_is_reported(tmp_path):
    crate_dir = build_crate(_minimal_capture(), crate_dir=tmp_path / "ro-crate",
                            author=AUTHOR)
    result = _validate(crate_dir, "ro-crate-1.2")
    assert not result.passed()
    assert any(i.violatingProperty == "http://schema.org/license"
               for i in result.get_issues()), _issues(result)
