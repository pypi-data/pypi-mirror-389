# Copyright 2025, Euro NCAP IVZW
# Created by IVEX NV (https://ivex.ai)
#
# Licensed under the Apache License 2.0.
# See http://www.apache.org/licenses/LICENSE-2.0 for details.

import pandas as pd
import logging

from euroncap_rating_2026.common import with_footer
from euroncap_rating_2026 import config
import os
import shutil
from importlib.resources import files
import click

logger = logging.getLogger(__name__)
settings = config.Settings()


@click.command()
@with_footer
def generate_template():
    """
    Generate a template file for crash avoidance.
    This function copies the `ca_template.xlsx` file from the predefined
    data directory to the current working directory. The template file
    serves as a starting point for crash avoidance analysis.
    Outputs:
        - A file named `ca_template.xlsx` in the current working directory.
    """
    print(f"[Crash Avoidance] Generating template for crash avoidance...")
    template_path = str(files("data").joinpath("ca_template.xlsx"))
    dest_path = os.path.join(os.getcwd(), "ca_template.xlsx")
    shutil.copyfile(template_path, dest_path)
    print(f"Template generated at {dest_path}")
