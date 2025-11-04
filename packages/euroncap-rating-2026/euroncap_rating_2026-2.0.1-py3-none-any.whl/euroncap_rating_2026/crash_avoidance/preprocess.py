# Copyright 2025, Euro NCAP IVZW
# Created by IVEX NV (https://ivex.ai)
#
# Licensed under the Apache License 2.0.
# See http://www.apache.org/licenses/LICENSE-2.0 for details.

import pandas as pd
import logging
import os

from euroncap_rating_2026.crash_avoidance import matrix_processing
from euroncap_rating_2026.common import with_footer, hard_copy_sheet
from euroncap_rating_2026 import config

from euroncap_rating_2026 import common
import click

from euroncap_rating_2026.crash_avoidance.test_info import (
    preprocess_stage_subelement,
    get_sheet_prefix,
)
from euroncap_rating_2026.crash_avoidance.data_model import (
    STAGE_SUBELEMENTS,
)
from euroncap_rating_2026.crash_avoidance import report_writer
from euroncap_rating_2026.crash_protection.compute_score import COMPUTE_SHEETS_TO_COPY

logger = logging.getLogger(__name__)
settings = config.Settings()

PREPROCESS_SHEETS_TO_COPY = [
    "Input parameters",
    "Test Scores",
    "Scenario Scores",
    "Category Scores",
    "FC - Car & PTW Prediction",
    "FC - Car & PTW Robustness",
    "FC - Ped & Cyc Prediction",
    "FC - Ped & Cyc Robustness",
    "LDC - Single Veh Prediction",
    "LDC - Car & PTW Prediction",
    "LDC - Robustness",
    "LSC - Car & PTW Prediction",
    "LSC - Ped & Cyc Prediction",
]


@click.command()
@with_footer
@click.option(
    "--input_file",
    "-i",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Path to the input Excel file containing NCAP test measurements.",
)
@click.option(
    "--output_path",
    "-o",
    type=click.Path(file_okay=False, writable=True),
    default=os.getcwd(),
    show_default=True,
    help="Path to the output directory where the report will be saved.",
)
def preprocess(input_file, output_path):
    """Select test points and generate loadcases from input Excel file."""
    print(f"[Crash Avoidance] Preprocessing test points and generating loadcases...")

    output_file = os.path.join(output_path, "ca_preprocessed_template.xlsx")

    dfs = common.read_excel_file_to_dfs(input_file)
    logger.debug(f"Loaded sheets: {list(dfs.keys())}")

    verification_test_dfs = {}

    stage_subelements = []
    for stage_info in STAGE_SUBELEMENTS:
        current_stage_info = stage_info
        current_stage_element = current_stage_info["Stage element"]
        current_stage_subelement = current_stage_info["Stage subelement"]

        stage_subelement = preprocess_stage_subelement(
            dfs, current_stage_element, current_stage_subelement
        )
        sheet_prefix = get_sheet_prefix(current_stage_element, current_stage_subelement)
        verification_test_dfs[f"{sheet_prefix} Verification"] = (
            stage_subelement.test_points_df
        )
        stage_subelements.append(stage_subelement)

    for i, sheet in enumerate(PREPROCESS_SHEETS_TO_COPY):
        try:
            mode = "w" if i == 0 else "a"
            df = pd.read_excel(input_file, sheet_name=sheet, header=0)
            with pd.ExcelWriter(output_file, engine="openpyxl", mode=mode) as writer:
                df.to_excel(writer, sheet_name=sheet, index=False)
        except Exception as e:
            logger.error(f"Failed to copy sheet {sheet}: {e}")
    for i, sheet in enumerate(PREPROCESS_SHEETS_TO_COPY):
        hard_copy_sheet(input_file, sheet, output_file)

    merged_selected_points_dict = {}
    for subelement in stage_subelements:
        merged_selected_points_dict.update(subelement.selected_points_dict)
    report_writer.write_report(
        verification_test_dfs,
        selected_points_dict=merged_selected_points_dict,
        output_file=output_file,
        format_prediction_cells=True,
    )
