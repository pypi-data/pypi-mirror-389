# Copyright 2025, Euro NCAP IVZW
# Created by IVEX NV (https://ivex.ai)
#
# Licensed under the Apache License 2.0.
# See http://www.apache.org/licenses/LICENSE-2.0 for details.

import pandas as pd
import logging
import os

from euroncap_rating_2026.crash_protection import vru_processing
from euroncap_rating_2026.crash_protection import data_loader
from euroncap_rating_2026.common import with_footer
from euroncap_rating_2026 import config
from euroncap_rating_2026.crash_protection.report_writer import write_report

import click

logger = logging.getLogger(__name__)
settings = config.Settings()

PREPROCESS_SHEETS_TO_COPY = [
    "Test Scores",
    "Input parameters",
    "CP - Dummy Scores",
    "CP - Body Region Scores",
    "CP - Frontal Offset",
    "CP - Frontal FW",
    "CP - Frontal Sled & VT",
    "CP - Side MDB",
    "CP - Side Pole",
    "CP - Side Farside",
    "CP - Rear Whiplash",
    "CP - VRU Prediction",
]


def get_vru_cell_coords(vru_test_points, vru_df):
    vru_x_cell_coords = []
    # Add VRU sheet from score_df_dict to the output file
    # Write an "x" at the cells specified by vru_test_points
    logger.info(f"vru_test_points: {vru_test_points}")
    for vru_test_point in vru_test_points:
        row_index = vru_test_point.row
        col_index = vru_test_point.col
        row_1 = vru_df.iloc[1]
        col_3 = vru_df.iloc[:, 3]

        # Find the column index in row_1 where the value equals col_index
        row_1_index = None
        for idx, value in enumerate(row_1):
            if value == col_index:
                row_1_index = idx
                break

        # Find the row index in col_3 where the value equals row_index
        col_3_index = None
        if isinstance(vru_test_point, vru_processing.VruTestPoint):
            for idx, value in enumerate(col_3):
                if value == row_index:
                    col_3_index = idx
                    break
        elif isinstance(vru_test_point, vru_processing.LegformTestPoint):
            col_3_index = (
                vru_test_point.row + vru_processing.LEGFORMS_START_ROW_INDEX + 2
            )

        if row_1_index is not None and col_3_index is not None:
            logger.info(
                f"Saving 'x'row {col_3_index} x {row_1_index} for {vru_test_point}"
            )
            vru_x_cell_coords.append((col_3_index, row_1_index))
    logger.info(f"vru_x_cell_coords: {vru_x_cell_coords}")
    return vru_x_cell_coords


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
    """Preprocess VRU test points and generate loadcases from input Excel file."""
    print(
        f"[Crash Protection] Preprocessing VRU test points and generating loadcases..."
    )

    output_file = os.path.join(output_path, "cp_preprocessed_template.xlsx")

    vru_test_data = data_loader.generate_vru_test_points(input_file)
    data_loader.generate_vru_loadcases(vru_test_data)
    vru_test_data.populate_loadcase_dict()

    vru_test_points = vru_test_data.get_vru_test_points()
    vru_x_cell_coords = get_vru_cell_coords(
        vru_test_points, vru_test_data.prediction_df
    )

    vru_processing.pretty_print_loadcases(vru_test_data.headform_loadcases)
    vru_processing.pretty_print_loadcases(vru_test_data.legform_loadcases)

    vru_test_data.generate_vru_df()

    for i, sheet in enumerate(PREPROCESS_SHEETS_TO_COPY):
        try:
            if i == 0:
                mode = "w"
            else:
                mode = "a"
            df = pd.read_excel(input_file, sheet_name=sheet, header=0)
            with pd.ExcelWriter(output_file, engine="openpyxl", mode=mode) as writer:
                df.to_excel(writer, sheet_name=sheet, index=False)
        except Exception as e:
            logger.error(f"Failed to copy sheet {sheet}: {e}")

    for sheet_name in vru_test_data.df_dict:
        df = vru_test_data.df_dict[sheet_name]

        # Save the updated DataFrame back to the output file
        writer = pd.ExcelWriter(
            output_file, engine="openpyxl", mode="a", if_sheet_exists="replace"
        )
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        writer.close()

    write_report(
        vru_test_data.df_dict,
        vru_x_cell_coords,
        output_file,
        format_vru_prediction=True,
    )

    print(" " * 40)
    print(f"Preprocessed template available at {output_file}")
    logger.info(f"Preprocessed template available at {output_file}")
