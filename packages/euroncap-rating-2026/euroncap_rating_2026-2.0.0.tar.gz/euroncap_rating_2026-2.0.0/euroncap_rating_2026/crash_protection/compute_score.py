# Copyright 2025, Euro NCAP IVZW
# Created by IVEX NV (https://ivex.ai)
#
# Licensed under the Apache License 2.0.
# See http://www.apache.org/licenses/LICENSE-2.0 for details.

import pandas as pd
import logging

from euroncap_rating_2026.crash_protection import vru_processing
from euroncap_rating_2026.crash_protection import data_loader
from euroncap_rating_2026.common import with_footer, hard_copy_sheet
from euroncap_rating_2026 import config
import sys
from pandas.api.types import is_string_dtype
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
from datetime import datetime
import shutil
from importlib.resources import files
from euroncap_rating_2026.crash_protection.report_writer import write_report

import click


logger = logging.getLogger(__name__)
settings = config.Settings()


# Copy specific sheets to the output file
COMPUTE_SHEETS_TO_COPY = [
    "Test Scores",
    "Input parameters",
    "CP - Dummy Scores",
    "CP - Body Region Scores",
    "CP - VRU Prediction",
]


def get_current_loadcase_id(df, index):
    current_loadcase_id = df.loc[index, "Loadcase"]
    if not pd.isna(df.iloc[index]["Seat position"]):
        current_loadcase_id += f"_{df.iloc[index]['Seat position']}"
    if not pd.isna(df.iloc[index]["Dummy"]):
        current_loadcase_id += f"_{df.iloc[index]['Dummy']}"

    # Then process the remaining rows
    for i in range(index + 1, len(df)):
        next_row = df.iloc[i]
        if not pd.isna(next_row["Loadcase"]):
            break
        if not pd.isna(next_row["Seat position"]):
            current_loadcase_id += f"_{next_row['Seat position']}"
        if not pd.isna(next_row["Dummy"]):
            current_loadcase_id += f"_{next_row['Dummy']}"
    return current_loadcase_id


def update_loadcase(df, loadcase):
    last_load_case = None
    last_seat_name = None
    last_dummy_name = None
    last_body_region = None
    last_test_point = None

    if len(loadcase.raw_seats) > 0:
        logger.debug(
            f"Processing loadcase: {loadcase.name} with {len(loadcase.raw_seats)} raw seats"
        )
        logger.debug(f"raw_seats: {[s.name for s in loadcase.raw_seats]}")
    # Ensure the DataFrame has the "Score" and "Capping?" columns
    if "Score" not in df.columns:
        df["Score"] = ""
    if "Capping?" not in df.columns:
        df["Capping?"] = ""

    for column in ["Colour", "Capping?", "Prediction.Check"]:
        if column in df.columns and not is_string_dtype(df[column]):
            df[column] = df[column].astype(str)

    for index, row in df.iterrows():
        if not pd.isna(row["Loadcase"]):
            last_load_case = row["Loadcase"]
            current_loadcase_id = get_current_loadcase_id(df, index)
        if not pd.isna(row["Seat position"]):
            last_seat_name = row["Seat position"]
        if not pd.isna(row["Dummy"]):
            last_dummy_name = row["Dummy"]
        if not pd.isna(row["Body Region"]):
            last_body_region = row["Body Region"]
        if "Test Point" in df.columns and not pd.isna(row["Test Point"]):
            last_test_point = row["Test Point"]
        if (
            not (
                "Static-Front" in current_loadcase_id and "Static-Front" in loadcase.id
            )
            and current_loadcase_id != loadcase.id
        ):
            continue

        criteria = row["Criteria"]
        # Use loadcase.raw_seats if available, otherwise use loadcase.seats
        seat_list = (
            loadcase.raw_seats
            if hasattr(loadcase, "raw_seats") and len(loadcase.raw_seats) > 0
            else loadcase.seats
        )
        logger.debug(f"seat_list: {[f'{s.name} ({s.dummy.name})' for s in seat_list]}")
        seat = next(
            (
                s
                for s in seat_list
                if s.name == last_seat_name and s.dummy.name == last_dummy_name
            ),
            None,
        )
        if seat is None:
            logger.debug(
                f"Seat {last_seat_name} with dummy {last_dummy_name} not found in loadcase {loadcase.name}"
            )
            return

        body_region = next(
            (br for br in seat.dummy.body_region_list if br.name == last_body_region),
            None,
        )
        if body_region is None:
            logger.debug(
                f"Body region {last_body_region} not found in dummy {seat.dummy.name}"
            )

        if "Test Point" in df.columns:
            # Try to find criteria_obj in the current body_region first
            criteria_obj = next(
                (
                    c
                    for c in body_region._criteria
                    if c.name == criteria and c.test_point == last_test_point
                ),
                None,
            )
            # If not found, search all seats, dummies, body regions, and criteria
            if criteria_obj is None:
                for seat_search in seat_list:
                    for body_region_search in seat_search.dummy.body_region_list:
                        for c in body_region_search._criteria:
                            if c.name == criteria and c.test_point == last_test_point:
                                criteria_obj = c
                                break
                        if criteria_obj is not None:
                            break
                    if criteria_obj is not None:
                        break
        else:
            criteria_obj = next(
                (c for c in body_region._criteria if c.name == criteria),
                None,
            )
        logger.debug(f"Loadcase: {loadcase.id}, Criteria object: {criteria_obj}")
        if criteria_obj:
            df.loc[index, "HPL"] = criteria_obj.hpl
            df.loc[index, "LPL"] = criteria_obj.lpl
            df.loc[index, "Colour"] = criteria_obj.color
            df.loc[index, "Score"] = criteria_obj.score
            df.loc[index, "Capping?"] = "YES" if criteria_obj.capping else ""
            if criteria_obj.prediction_result and "Prediction.Check" in df.columns:
                df.loc[index, "Prediction.Check"] = "".join(
                    word.capitalize() for word in criteria_obj.prediction_result.split()
                )
            logger.debug(
                f"Updated row - Loadcase: {current_loadcase_id}, Seat: {last_seat_name}, Dummy: {last_dummy_name}, Body Region: {last_body_region}, Criteria: {criteria}, Colour: {criteria_obj.color}, Score: {criteria_obj.score}, Capping: {criteria_obj.capping}, Prediction: {criteria_obj.prediction_result}"
            )
    return df


def update_dummy_scores(df, loadcase):

    last_load_case = None
    last_seat_name = None
    last_dummy_name = None

    for column in ["Capping?"]:
        if column in df.columns and not is_string_dtype(df[column]):
            df[column] = df[column].astype(str)

    for index, row in df.iterrows():
        if not pd.isna(row["Loadcase"]):
            last_load_case = row["Loadcase"]
            current_loadcase_id = get_current_loadcase_id(df, index)
        if not pd.isna(row["Seat position"]):
            last_seat_name = row["Seat position"]
        if not pd.isna(row["Dummy"]):
            last_dummy_name = row["Dummy"]

        if current_loadcase_id != loadcase.id:
            continue

        seat = next(
            (
                s
                for s in loadcase.seats
                if s.name == last_seat_name and s.dummy.name == last_dummy_name
            ),
            None,
        )
        if seat is None:
            logger.debug(
                f"Seat {last_seat_name} with dummy {last_dummy_name} not found in loadcase {loadcase.name}"
            )
            return

        if seat.dummy.score is not None:
            df.loc[index, "Score"] = seat.dummy.score
        if seat.dummy.max_score is not None:
            df.loc[index, "Max score"] = seat.dummy.max_score
        df.loc[index, "Capping?"] = "Capped" if seat.dummy.capping else ""

        logger.debug(
            f"Updated row - Loadcase: {last_load_case}, Seat: {last_seat_name}, Dummy: {last_dummy_name}, Score: {seat.dummy.score}"
        )

    return df


def update_bodyregion(df, loadcase):

    last_load_case = None
    last_seat_name = None
    last_dummy_name = None
    last_body_region = None

    for index, row in df.iterrows():
        if not pd.isna(row["Loadcase"]):
            last_load_case = row["Loadcase"]
            current_loadcase_id = get_current_loadcase_id(df, index)
        if not pd.isna(row["Seat position"]):
            last_seat_name = row["Seat position"]
        if not pd.isna(row["Dummy"]):
            last_dummy_name = row["Dummy"]
        if not pd.isna(row["Body Region"]):
            last_body_region = row["Body Region"]

        if current_loadcase_id != loadcase.id:
            continue

        seat = next(
            (
                s
                for s in loadcase.seats
                if s.name == last_seat_name and s.dummy.name == last_dummy_name
            ),
            None,
        )
        if seat is None:
            logger.debug(
                f"Seat {last_seat_name} with dummy {last_dummy_name} not found in loadcase {loadcase.name}"
            )
            return

        body_region = next(
            (br for br in seat.dummy.body_region_list if br.name == last_body_region),
            None,
        )
        if body_region is None:
            logger.debug(
                f"Body region {last_body_region} not found in dummy {seat.dummy.name}"
            )
            return

        df.loc[index, "Body regionscore"] = body_region.bodyregion_score
        df.loc[index, "Score"] = body_region.score
        df.loc[index, "Modifiers"] = sum(
            measurement.modifier
            for measurement in body_region._measurement
            if measurement.modifier is not None
        )
        if body_region.max_score is not None:
            df.loc[index, "Max Score"] = body_region.max_score
        logger.debug(
            f"Updated row - Loadcase: {last_load_case}, Seat: {last_seat_name}, Dummy: {last_dummy_name}, Body Region: {last_body_region}, Score: {body_region.score}"
        )
    return df


def update_stage_scores(df, final_scores):

    last_stage_subelement = None

    for index, row in df.iterrows():

        if not pd.isna(row["Stage Subelement"]):
            last_stage_subelement = row["Stage Subelement"]

        for key in final_scores:
            if key == last_stage_subelement:
                df.loc[index, "Score"] = final_scores[key]

    return df


def print_score(final_scores, final_max_scores, overall_score, overall_max_score):
    print("-" * 40)
    print("Score:")
    print("-" * 40)
    print(
        f"{'Stage Element':<20}{'Stage Subelement':<20}{'Score':<10}{'Max Score':<10}"
    )
    print("-" * 40)
    score_order = [
        ("Frontal Impact", ["Offset", "FW", "Sled & VT"]),
        ("Side Impact", ["MDB", "Pole", "Farside"]),
        ("Rear Impact", ["Whiplash"]),
        ("VRU Impact", ["Head Impact", "Pelvis & Leg Impact"]),
    ]

    printed_categories = set()
    for category, subcategories in score_order:
        for subcategory in subcategories:
            if subcategory in final_scores:
                logger.info(
                    f"Final score for {subcategory}: {final_scores[subcategory]}/{final_max_scores[subcategory]}"
                )
                category_to_print = (
                    category if category not in printed_categories else ""
                )
                print(
                    f"{category_to_print:<20}{subcategory:<20}{final_scores[subcategory]:<10}{final_max_scores[subcategory]:<10}"
                )
                printed_categories.add(category)
            else:
                logger.warning(f"Score for {subcategory} not found.")
                category_to_print = (
                    category if category not in printed_categories else ""
                )
                print(f"{category_to_print:<20}{subcategory:<20}{'N/A':<10}{'N/A':<10}")
                printed_categories.add(category)

    print("-" * 40)
    print(" " * 40)

    overall_str = "Final score"
    print(f"{overall_str:<20}{overall_score:<10}{overall_max_score:<10}")
    print(" " * 40)


def get_output_file_path(output_path: str) -> str:
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = os.path.join(output_path, f"cp_{current_datetime}_report.xlsx")
    return output_file


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
    print(f"[Crash Protection] Computing NCAP scores from input Excel file...")

    if not input_file:
        logger.error("Input file path is required.")
        sys.exit(1)
    if not input_file.endswith(".xlsx"):
        logger.error("Input file must be an Excel file with .xlsx extension.")
        sys.exit(1)

    print("Loading data from spreadsheet...")
    sheet_dict, test_score_inspection = data_loader.load_data(input_file)
    logger.info(f"Loaded sheet_dict: {sheet_dict.keys()}")

    print("Computing NCAP scores...")
    overall_score, overall_max_score, final_scores, final_max_scores = (
        data_loader.get_score(sheet_dict, test_score_inspection)
    )

    output_file = get_output_file_path(output_path)

    score_df_dict = {}
    vru_x_cell_coords = []

    for i, sheet in enumerate(COMPUTE_SHEETS_TO_COPY):
        if i == 0:
            mode = "w"
        else:
            mode = "a"

        if sheet == "CP - VRU Prediction":
            hard_copy_sheet(input_file, sheet, output_file)
        else:
            df = pd.read_excel(input_file, sheet_name=sheet, header=0)
            score_df_dict[sheet] = df  # Store the DataFrame for later use
            with pd.ExcelWriter(output_file, engine="openpyxl", mode=mode) as writer:
                df.to_excel(writer, sheet_name=sheet, index=False)

    for sheet_name in sheet_dict:
        writer = pd.ExcelWriter(output_file, engine="openpyxl", mode="a")
        df = pd.read_excel(input_file, sheet_name=sheet_name, header=0)
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        writer.close()

        logger.debug(f"score_df_dict keys: {list(score_df_dict.keys())}")
        logger.debug(f"sheet_dict keys: {list(sheet_dict.keys())}")
        for i, loadcase_df in enumerate(sheet_dict[sheet_name]):
            df = update_loadcase(df, loadcase_df)
            logger.debug(f"Processing loadcase_df: {loadcase_df}")
            score_df_dict["CP - Body Region Scores"] = update_bodyregion(
                score_df_dict["CP - Body Region Scores"], loadcase_df
            )
            score_df_dict["CP - Dummy Scores"] = update_dummy_scores(
                score_df_dict["CP - Dummy Scores"], loadcase_df
            )
            logger.debug(f"end: {loadcase_df}")

        # Save the updated DataFrame back to the output file
        writer = pd.ExcelWriter(
            output_file, engine="openpyxl", mode="a", if_sheet_exists="replace"
        )
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        writer.close()

    score_df_dict["Test Scores"] = update_stage_scores(
        score_df_dict["Test Scores"], final_scores
    )
    write_report(
        score_df_dict,
        vru_x_cell_coords,
        output_file,
        format_vru_prediction=False,
    )

    print_score(final_scores, final_max_scores, overall_score, overall_max_score)

    print(f"Log available at {os.path.join(output_path, 'euroncap_rating_2026.log')}")
    print(" " * 40)
    print(f"Final report available at {output_file}")
    logger.info(f"Final report available at {output_file}")
