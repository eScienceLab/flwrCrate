"""Validate RO-Crates with rocrate-validator.
Shared by the test suite and the end-to-end check, and meant for validating
crates after a run.
"""

from io import StringIO

from rocrate_validator import models, services
from rocrate_validator.utils.io_helpers.output.console import Console
from rocrate_validator.utils.io_helpers.output.text import TextOutputFormatter


def validate(crate_dir, profile, **settings):
    """Validate a crate folder against one profile: REQUIRED level, offline, extra checks on."""
    return services.validate(services.ValidationSettings(
        rocrate_uri=str(crate_dir),
        profile_identifier=profile,
        requirement_severity=models.Severity.REQUIRED,
        offline=True,
        extra_checks=True,
        **settings,
    ))


def report(result):
    """The validator's full text report, which names the entity behind each issue."""
    out = StringIO()
    console = Console(file=out, width=120)
    console.register_formatter(TextOutputFormatter())
    console.print(result)
    return out.getvalue()
