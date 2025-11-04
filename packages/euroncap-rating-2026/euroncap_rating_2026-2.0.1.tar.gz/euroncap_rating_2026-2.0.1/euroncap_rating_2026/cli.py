import click

from euroncap_rating_2026.crash_avoidance import crash_avoidance_cli
from euroncap_rating_2026.crash_protection import crash_protection_cli
from euroncap_rating_2026.version import VERSION
from euroncap_rating_2026.config import logging_config
import logging
from functools import wraps
import os
import sys


@click.group(
    help="Euro NCAP Rating Calculator 2026 application to compute NCAP scores.",
    context_settings=dict(
        help_option_names=["-h", "--help"],
    ),
)
def cli():
    """Main CLI entry point."""
    pass


logger = logging.getLogger(__name__)
logging_config()
cli.add_command(crash_protection_cli)
cli.add_command(crash_avoidance_cli)

if __name__ == "__main__":
    cli()
