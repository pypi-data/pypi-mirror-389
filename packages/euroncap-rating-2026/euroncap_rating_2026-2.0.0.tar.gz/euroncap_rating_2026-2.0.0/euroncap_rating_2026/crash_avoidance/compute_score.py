# Copyright 2025, Euro NCAP IVZW
# Created by IVEX NV (https://ivex.ai)
#
# Licensed under the Apache License 2.0.
# See http://www.apache.org/licenses/LICENSE-2.0 for details.

import pandas as pd
import logging

from euroncap_rating_2026.common import with_footer, hard_copy_sheet
from euroncap_rating_2026 import config
from euroncap_rating_2026 import common
from euroncap_rating_2026.crash_avoidance.test_info import (
    compute_stage_score,
    get_stage_subelement_key,
)
from euroncap_rating_2026.crash_avoidance.data_model import (
    STAGE_SUBELEMENTS,
    STAGE_SUBELEMENT_TO_CATEGORIES,
)
from euroncap_rating_2026.crash_avoidance import report_writer

import sys
import os
from datetime import datetime

import click


logger = logging.getLogger(__name__)
settings = config.Settings()


# Copy specific sheets to the output file

COMPUTE_SHEETS_TO_COPY = [
    "Input parameters",
    "FC - Car & PTW Prediction",
    "FC - Car & PTW Robustness",
    "FC - Car & PTW Verification",
    "FC - Ped & Cyc Prediction",
    "FC - Ped & Cyc Robustness",
    "FC - Ped & Cyc Verification",
    "LDC - Single Veh Prediction",
    "LDC - Single Veh Verification",
    "LDC - Car & PTW Prediction",
    "LDC - Car & PTW Verification",
    "LDC - Robustness",
    "LSC - Car & PTW Prediction",
    "LSC - Ped & Cyc Prediction",
    "LSC - Car & PTW Verification",
    "LSC - Ped & Cyc Verification",
]


def get_output_file_path(output_path: str) -> str:
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = os.path.join(output_path, f"ca_{current_datetime}_report.xlsx")
    return output_file


def get_element_for_row(df, col_name, row_idx):
    """
    Given a DataFrame, column name, and row index, return the value of the column for the interval containing the row.
    Assumes the column is set at the start of an interval and NaN until the next.
    """
    col_elements = df[col_name]
    # Find all indices where col_name is notna and less than or equal to row_idx
    valid_indices = col_elements[col_elements.notna()].index
    prev_indices = valid_indices[valid_indices <= row_idx]
    if prev_indices.empty:
        return None
    last_idx = prev_indices[-1]
    return col_elements.loc[last_idx]


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
def compute_score(input_file, output_path):
    """Compute NCAP scores from an input Excel file."""
    print(f"[Crash Avoidance] Computing NCAP scores from input Excel file...")

    if not input_file:
        logger.error("Input file path is required.")
        sys.exit(1)
    if not input_file.endswith(".xlsx"):
        logger.error("Input file must be an Excel file with .xlsx extension.")
        sys.exit(1)

    print("Loading data from spreadsheet...")

    dfs = common.read_excel_file_to_dfs(input_file)
    logger.debug(f"Loaded sheets: {list(dfs.keys())}")
    print("Computing NCAP scores...")
    loadcase_score_dict = {}

    for stage_info in STAGE_SUBELEMENTS:
        stage_element = stage_info["Stage element"]
        stage_subelement = stage_info["Stage subelement"]
        if stage_subelement == "Pedestrian & Cyclist":
            stage_subelement = "Ped & Cyc"
        if stage_subelement == "Single Vehicle":
            stage_subelement = "Single Veh"
        if stage_element not in loadcase_score_dict:
            loadcase_score_dict[stage_element] = {}
        if stage_subelement not in loadcase_score_dict[stage_element]:
            loadcase_score_dict[stage_element][stage_subelement] = {}

        compute_stage_score(dfs, stage_info, loadcase_score_dict)

    for stage_element, subelements_dict in loadcase_score_dict.items():
        for stage_subelement, loadcases_dict in subelements_dict.items():
            for loadcase_key, loadcase_score in loadcases_dict.items():
                logger.debug(
                    f"Computed scenario score: Stage element={stage_element}, "
                    f"Stage subelement={stage_subelement}, Scenario={loadcase_key}, "
                    f"Scores={loadcase_score}"
                )

    if "Scenario Scores" not in dfs:
        raise ValueError("The input file must contain a 'Scenario Scores' sheet.")
    if "Test Scores" not in dfs:
        raise ValueError("The input file must contain a 'Test Scores' sheet.")

    loadcase_score_df = dfs["Scenario Scores"]
    loadcase_score_df["Score"] = loadcase_score_df["Score"].astype(float)
    for stage_element, subelements_dict in loadcase_score_dict.items():
        for stage_subelement, loadcases_dict in subelements_dict.items():
            for loadcase_key, loadcase_score in loadcases_dict.items():
                row_idx = loadcase_score_df.index[
                    loadcase_score_df["Scenario"] == loadcase_key
                ]
                if row_idx.empty:
                    logger.warning(f"Scenario {loadcase_key} not found in DataFrame.")
                    continue
                start_idx = row_idx[0]
                # Find the next index where "Scenario" is not NaN after start_idx
                next_idxs = loadcase_score_df.index[
                    (loadcase_score_df.index > start_idx)
                    & (loadcase_score_df["Scenario"].notna())
                ]
                end_idx = (
                    next_idxs[0] if not next_idxs.empty else len(loadcase_score_df)
                )
                loadcase_subset_df = loadcase_score_df.iloc[start_idx:end_idx]

                standard_layer_indices = loadcase_subset_df.index[
                    loadcase_subset_df["Layer"] == "Standard"
                ]
                loadcase_score_df.loc[standard_layer_indices, "Score"] = (
                    loadcase_score.standard_score
                )
                extended_layer_indices = loadcase_subset_df.index[
                    loadcase_subset_df["Layer"] == "Extended"
                ]
                loadcase_score_df.loc[extended_layer_indices, "Score"] = (
                    loadcase_score.extended_score
                )
                robustness_layer_indices = loadcase_subset_df.index[
                    loadcase_subset_df["Layer"] == "Robustness"
                ]
                loadcase_score_df.loc[robustness_layer_indices, "Score"] = (
                    loadcase_score.robustness_layer_score
                )

    scenario_score_df = dfs["Category Scores"]
    scenario_score_df["Score"] = scenario_score_df["Score"].astype(float)
    idx = 0
    logger.debug("Printing loadcase_score_dict for debugging:")
    for stage_element, subelements_dict in loadcase_score_dict.items():
        for stage_subelement, loadcases_dict in subelements_dict.items():
            for loadcase_key, loadcase_score in loadcases_dict.items():
                logger.debug(
                    f"Stage element: {stage_element}, Stage subelement: {stage_subelement}, Scenario: {loadcase_key}, Score: {loadcase_score}"
                )
    while idx < len(loadcase_score_df):
        logger.debug(f"IDX: {idx}")
        stage_element = get_element_for_row(loadcase_score_df, "Stage element", idx)
        stage_subelement = get_element_for_row(
            loadcase_score_df, "Stage subelement", idx
        )
        if stage_subelement == "Pedestrian & Cyclist":
            stage_subelement = "Ped & Cyc"
        if stage_subelement == "Single Vehicle":
            stage_subelement = "Single Veh"
        category_name = get_element_for_row(loadcase_score_df, "Category", idx)
        start_idx = idx
        # Find the next index where "Category" is notna after start_idx
        next_idxs = loadcase_score_df.index[
            (loadcase_score_df.index > start_idx)
            & (loadcase_score_df["Category"].notna())
        ]
        end_idx = next_idxs[0] if not next_idxs.empty else len(loadcase_score_df)
        subset_df = loadcase_score_df.iloc[start_idx:end_idx]
        idx += len(subset_df)
        logger.debug(f"IDX: {idx} after adding subset length {len(subset_df)}")
        score_sum = subset_df["Score"].sum()
        logger.debug(
            f"Computed score for {category_name} [{stage_element} - {stage_subelement}]: {score_sum} from rows {start_idx} to {end_idx}"
        )
        logger.debug(f"scenario_score_df:\n{scenario_score_df}")
        for scenario_idx in scenario_score_df.index:
            logger.debug(
                f"Processing {category_name} for {stage_element} - {stage_subelement}"
            )
            elem = get_element_for_row(scenario_score_df, "Stage element", scenario_idx)
            subelem = get_element_for_row(
                scenario_score_df, "Stage subelement", scenario_idx
            )

            if subelem == "Pedestrian & Cyclist":
                subelem = "Ped & Cyc"
            if subelem == "Single Vehicle":
                subelem = "Single Veh"
            category = get_element_for_row(scenario_score_df, "Category", scenario_idx)
            logger.debug(f"elem={elem}, subelem={subelem}, category={category}")
            logger.debug(
                f"stage_element={stage_element}, stage_subelement={stage_subelement}, category_name={category_name}"
            )
            logger.debug(f"score_sum={score_sum}")
            if (
                elem == stage_element
                and subelem == stage_subelement
                and category == category_name
            ):
                logger.debug(
                    f"Updating score for {category_name} in {stage_element} - {stage_subelement} with value {score_sum}"
                )
                scenario_score_df.loc[scenario_idx, "Score"] = score_sum
                break

    total_score_df = dfs["Test Scores"]
    total_score_df["Score"] = total_score_df["Score"].astype(float)
    for idx in total_score_df.index:
        stage_element = get_element_for_row(total_score_df, "Stage element", idx)
        stage_subelement = get_element_for_row(total_score_df, "Stage subelement", idx)

        if stage_subelement == "Pedestrian & Cyclist":
            stage_subelement = "Ped & Cyc"
        if stage_subelement == "Single Vehicle":
            stage_subelement = "Single Veh"
        scenario_scores = 0
        stage_subelement_key = get_stage_subelement_key(stage_element).value
        logger.debug(
            f"stage_subelement_key: {stage_subelement_key}, categories: {STAGE_SUBELEMENT_TO_CATEGORIES[stage_subelement_key]}"
        )
        processed_categories = set()
        for category_name in STAGE_SUBELEMENT_TO_CATEGORIES[stage_subelement_key]:
            for idx2 in scenario_score_df.index:
                elem = get_element_for_row(scenario_score_df, "Stage element", idx2)
                subelem = get_element_for_row(
                    scenario_score_df, "Stage subelement", idx2
                )

                if subelem == "Pedestrian & Cyclist":
                    subelem = "Ped & Cyc"
                if subelem == "Single Vehicle":
                    subelem = "Single Veh"

                category = get_element_for_row(scenario_score_df, "Category", idx2)
                logger.debug(f"elem={elem}, subelem={subelem}, category={category}")
                logger.debug(
                    f"stage_element={stage_element}, stage_subelement={stage_subelement}, category_name={category_name}"
                )
                if (
                    elem == stage_element
                    and subelem == stage_subelement
                    and category == category_name
                ):
                    score = scenario_score_df.loc[idx2, "Score"]
                    if pd.notna(score) and category_name not in processed_categories:
                        scenario_scores += score
                        processed_categories.add(category_name)
        logger.debug(
            f"Updating total score for {stage_element} - {stage_subelement} with category scores {scenario_scores}"
        )
        total_score_df.loc[idx, "Score"] = scenario_scores

    output_file = get_output_file_path(output_path)
    for i, sheet in enumerate(COMPUTE_SHEETS_TO_COPY):
        try:
            mode = "w" if i == 0 else "a"
            df = pd.read_excel(input_file, sheet_name=sheet, header=0)
            with pd.ExcelWriter(output_file, engine="openpyxl", mode=mode) as writer:
                df.to_excel(writer, sheet_name=sheet, index=False)
        except Exception as e:
            logger.error(f"Failed to copy sheet {sheet}: {e}")
    for i, sheet in enumerate(COMPUTE_SHEETS_TO_COPY):
        hard_copy_sheet(
            input_file,
            sheet,
            output_file,
        )

    with pd.ExcelWriter(output_file, engine="openpyxl", mode="a") as writer:
        loadcase_score_df.to_excel(writer, sheet_name="Scenario Scores", index=False)
        scenario_score_df.to_excel(writer, sheet_name="Category Scores", index=False)
        total_score_df.to_excel(writer, sheet_name="Test Scores", index=False)

    report_writer.write_report(
        {},
        [],
        output_file=output_file,
        format_prediction_cells=False,
    )

    print(f"Log available at {os.path.join(output_path, 'euroncap_rating_2026.log')}")
    print(" " * 40)
    print(f"Final report available at {output_file}")
    logger.info(f"Final report available at {output_file}")
