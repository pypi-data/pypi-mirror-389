import sys
import pandas as pd
import numpy as np
import logging
from dataclasses import dataclass, field
from enum import Enum
import os
import warnings

try:
    import matplotlib.pyplot as plt

    HAS_MPL = True
except ImportError:
    HAS_MPL = False

from euroncap_rating_2026.crash_avoidance.data_model import (
    MATRIX_INDICES,
    EXTENDED_RANGE_CELLS,
)
from euroncap_rating_2026.crash_avoidance.robustness_layer import (
    RobustnessLayer,
    AssessmentCriteria,
)
from euroncap_rating_2026.crash_avoidance.test_info import (
    StageSubelementKey,
    VehicleResponse,
    DoorSelected,
)

logger = logging.getLogger(__name__)
COLOR_THRESHOLD_TOLERANCE = 2.0  # km/h tolerance


class PredictionColor(str, Enum):
    BLUE = "blue"
    BROWN = "brown"
    GREEN = "green"
    GREY = "grey"
    ORANGE = "orange"
    RED = "red"
    YELLOW = "yellow"


PREDICTION_COLOR_MAP = {
    PredictionColor.BLUE: (0 / 255, 102 / 255, 204 / 255),
    PredictionColor.BROWN: (150 / 255, 75 / 255, 0 / 255),
    PredictionColor.GREEN: (0 / 255, 153 / 255, 51 / 255),
    PredictionColor.GREY: (128 / 255, 128 / 255, 128 / 255),
    PredictionColor.ORANGE: (255 / 255, 153 / 255, 51 / 255),
    PredictionColor.RED: (255 / 255, 51 / 255, 51 / 255),
    PredictionColor.YELLOW: (255 / 255, 221 / 255, 51 / 255),
}


def plot_matrix(matrix, extended_range_cells, name="matrix"):
    unique_colors = sorted(PREDICTION_COLOR_MAP.keys())
    # Prepare the matrix for plotting
    # Log the length of legforms_string_matrix
    n_rows = len(matrix)
    n_cols = len(matrix[0]) if n_rows > 0 else 0

    fig, ax = plt.subplots(figsize=(n_cols, n_rows))

    # Draw colored cells
    for i in range(n_rows):
        for j in range(n_cols):
            color = matrix[i][j].lower()
            rect = plt.Rectangle(
                (j, n_rows - 1 - i),
                1,
                1,
                facecolor=PREDICTION_COLOR_MAP.get(color, "white"),
                edgecolor="black",
            )
            ax.add_patch(rect)

    # Highlight selected cells with an X
    for row, col in extended_range_cells:
        rect = plt.Rectangle(
            (col, n_rows - 1 - row),
            1,
            1,
            fill=False,
            edgecolor="black",
            linewidth=3,
            linestyle="--",
        )
        ax.add_patch(rect)

    # Set axis limits and labels
    ax.set_xlim(0, n_cols)
    ax.set_ylim(0, n_rows)
    ax.set_xticks(range(n_cols))
    ax.set_yticks(range(n_rows))
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    ax.set_title(f"{name} with Selected Cells")

    # Create a legend for colors
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=PREDICTION_COLOR_MAP[color])
        for color in unique_colors
        if color not in ["grey", "blue"]
    ]
    labels = [
        color.capitalize() for color in unique_colors if color not in ["grey", "blue"]
    ]
    if "grey" in unique_colors:
        handles.append(plt.Rectangle((0, 0), 1, 1, color=PREDICTION_COLOR_MAP["grey"]))
        labels.append("Grey")

    ax.legend(handles, labels, bbox_to_anchor=(1.05, 1), loc="upper left")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            plt.tight_layout()
    except Exception as e:
        logger.warning(f"tight_layout() failed: {e}")

    # Save to /output directory
    output_dir = "matrices"
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, f"{name}_matrix.png"))
    plt.close()


class TestRange(Enum):
    STANDARD = "Standard"
    EXTENDED = "Extended"
    UNKNOWN = "Unknown"


class PredictionSource(Enum):
    VTA = "VTA"
    SELF_CLAIMED = "Self Claimed"
    UNKNOWN = "Unknown"


@dataclass
class TestPoint:
    """
    Represents a VRU test point with its coordinates and color.
    """

    row: int
    col: int
    color: PredictionColor = None
    test_range: TestRange = TestRange.UNKNOWN
    attributes: dict = field(default_factory=dict)
    robustness_layer: RobustnessLayer = None

    @property
    def predicted_score(self) -> float:
        if self.test_range == TestRange.STANDARD:
            if self.color == PredictionColor.GREEN:
                return 1.0
            elif self.color == PredictionColor.YELLOW:
                return 0.75
            elif self.color == PredictionColor.ORANGE:
                return 0.5
            elif self.color == PredictionColor.BROWN:
                return 0.25
            elif self.color == PredictionColor.RED:
                return 0.0
            else:
                return 0.0
        else:
            if self.color == PredictionColor.RED:
                return 0.0
            else:
                return 1.0


class PredictionResult(str, Enum):
    UNKNOWN = "Unknown"
    CORRECT = "Correct"
    INCORRECT = "Incorrect"
    IN_TOLERANCE = "In Tolerance"


def check_thresholds(thresholds, oem_predicted_color, value, tolerance):
    color_list = [color for color, _ in thresholds]
    if oem_predicted_color in color_list:
        idx = color_list.index(oem_predicted_color)
        prev_idx = max(idx - 1, 0)
        prev_color, prev_threshold = thresholds[prev_idx]
        curr_color, curr_threshold = thresholds[idx]

        if prev_idx != idx and prev_threshold - tolerance <= value <= prev_threshold:
            return PredictionResult.IN_TOLERANCE, oem_predicted_color
        if curr_threshold < value <= curr_threshold + tolerance:
            return PredictionResult.IN_TOLERANCE, oem_predicted_color

        if prev_threshold <= value <= curr_threshold:
            return PredictionResult.CORRECT, oem_predicted_color

        return PredictionResult.INCORRECT, oem_predicted_color
    else:
        return PredictionResult.INCORRECT, PredictionColor.GREY


AEB_ONLY_ROW = [4, 5]
FCW_AEB_ROW = [6, 7]


@dataclass
class ComputedTestPoint:
    """
    Represents a computed test point with its attributes.
    """

    test_point: TestPoint
    test_name: str = None
    value: float = None
    prediction_result: PredictionResult = PredictionResult.UNKNOWN
    assessment_criteria: AssessmentCriteria = None

    @property
    def computed_color(self) -> float:
        if self.value is None:
            self.prediction_result = PredictionResult.UNKNOWN
            logger.debug("Value is None, returning grey color.")
            return PredictionColor.GREY

        vut_speed_str = self.test_point.attributes.get("VUT speed")
        if vut_speed_str and vut_speed_str.strip().lower() == "sfs":
            vut_speed = 0.0
        else:
            vut_speed = (
                float(vut_speed_str.replace(" km/h", "")) if vut_speed_str else 0.0
            )
        tolerance = COLOR_THRESHOLD_TOLERANCE
        oem_predicted_color = self.test_point.color

        # Lookup tables for thresholds and tolerances
        mitigation_or_avoidance_thresholds = {
            10.0: [
                (PredictionColor.GREEN, 0.0),
                (PredictionColor.RED, float("inf")),
            ],
            20.0: [
                (PredictionColor.GREEN, 0.0),
                (PredictionColor.RED, float("inf")),
            ],
            30.0: [
                (PredictionColor.GREEN, 0.0),
                (PredictionColor.BROWN, 10.0),
                (PredictionColor.RED, float("inf")),
            ],
            40.0: [
                (PredictionColor.GREEN, 0.0),
                (PredictionColor.ORANGE, 10.0),
                (PredictionColor.BROWN, 20.0),
                (PredictionColor.RED, float("inf")),
            ],
            50.0: [
                (PredictionColor.GREEN, 0.0),
                (PredictionColor.YELLOW, 10.0),
                (PredictionColor.ORANGE, 20.0),
                (PredictionColor.BROWN, 30.0),
                (PredictionColor.RED, float("inf")),
            ],
        }

        mitigation_scenarios_thresholds = [
            (PredictionColor.RED, 10.0),
            (PredictionColor.ORANGE, 20.0),
            (PredictionColor.GREEN, 30.0),
            (PredictionColor.RED, float("inf")),
        ]
        avoidance_thresholds = [
            (PredictionColor.GREEN, 0.0),
            (PredictionColor.RED, float("inf")),
        ]
        warning_thresholds = [
            (PredictionColor.RED, 1.7),
            (PredictionColor.GREEN, float("inf")),
        ]
        road_edge_thresholds = [
            (PredictionColor.RED, -0.1),
            (PredictionColor.GREEN, float("inf")),
        ]
        elk_target_thresholds = [
            (PredictionColor.GREEN, 0.0),
            (PredictionColor.RED, float("inf")),
        ]

        avoidance_scenarios = [
            "CBTAfs && CBTAns",
            "CBTAfo && CBTAno",
            "CPTAfs && CPTAns",
            "CPTAfo && CPTAno",
            "CCFtap",
            "CMFtap",
            "CCCscp",
            "CMCscp",
        ]
        mitigation_scenarios = ["CCFhos", "CCFhol"]
        mitigation_or_avoidance_scenarios = [
            "CCRs",
            "CCRm",
            "CCRb",
            "CMRs",
            "CMRb",
            "CPNA_day",
            "CPNA_night",
            "CPFA_day",
            "CPFA_night",
            "CPNCO_day",
            "CPNCO_night",
            "CBNA",
            "CBFA",
            "CBNAO",
        ]
        warning_scenarios = (
            []
        )  # Special cases for "CPLA_day(FCW)", "CPLA_night(FCW)", "CBLA(≥50 km/h)" are handled below
        road_edge_scenarios = ["ELK-RE"]
        elk_target_scenarios = [
            "C2C ELK-ON",
            "C2C ELK-OVI",
            "C2C ELK-OVU",
            "C2M ELK-ON",
            "C2M ELK-OV",
            "C2M ELK-OVI",
            "C2M ELK-OVU",
        ]

        is_mitigation_or_avoidance = self.test_name in mitigation_or_avoidance_scenarios
        is_mitigation = self.test_name in mitigation_scenarios
        is_avoidance = self.test_name in avoidance_scenarios
        is_warning = self.test_name in warning_scenarios
        is_road_edge = self.test_name in road_edge_scenarios
        is_elk_target = self.test_name in elk_target_scenarios

        logger.debug(
            f"is_mitigation_or_avoidance: {is_mitigation_or_avoidance}, "
            f"is_mitigation: {is_mitigation}, "
            f"is_avoidance: {is_avoidance}, "
            f"is_warning: {is_warning}, "
            f"is_road_edge: {is_road_edge}, "
            f"is_elk_target: {is_elk_target}"
        )
        logger.debug(f"VUT speed: {vut_speed} km/h")

        if "CPLA" in self.test_name or "CBLA" in self.test_name:
            if self.test_point.attributes.get("Function") == "FCW":
                logger.debug(
                    f"Test point row {self.test_point.row} indicates FCW function. Setting is_warning to True."
                )
                is_warning = True
            # Special case for CPLA scenarios
            elif self.test_point.attributes.get("Function") == "AEB":
                # If it is an original AEB the mitigation_or_avoidance (row 6-7 in template)
                is_mitigation_or_avoidance = True
                if self.test_point.row in AEB_ONLY_ROW:
                    logger.debug(
                        f"Test point row {self.test_point.row} indicates original AEB. Setting is_mitigation_or_avoidance to True."
                    )
                # If it is a former FCW then declared as AEB, the is_avoidance (row 8-9 in template)
                elif self.test_point.row in FCW_AEB_ROW:
                    # Set is_avoidance to True
                    logger.debug(
                        f"Test point row {self.test_point.row} indicates FCW declared as AEB. Setting is_avoidance to True."
                    )
                    is_avoidance = True

        # Mitigation or avoidance scenarios
        if is_mitigation_or_avoidance:
            logger.debug(
                f"Test name '{self.test_name}' is in mitigation or avoidance scenarios."
            )
            speed = 50.0 if vut_speed >= 50.0 else vut_speed
            thresholds_at_speed = mitigation_or_avoidance_thresholds.get(speed, [])
            # Find the index of the OEM predicted color in the thresholds list
            logger.debug(f"Speed: {speed}")
            logger.debug(f"Thresholds: {thresholds_at_speed}")
            logger.debug(f"OEM predicted color: {oem_predicted_color}")

            self.prediction_result, predicted_color = check_thresholds(
                thresholds_at_speed, oem_predicted_color, self.value, tolerance
            )
            return predicted_color

        # Mitigation scenarios
        elif is_mitigation:
            logger.debug(f"Test name '{self.test_name}' is in mitigation scenarios.")
            # Use similar logic as mitigation_or_avoidance_scenarios
            speed = 30.0 if vut_speed == 30.0 else 35.0

            self.prediction_result, predicted_color = check_thresholds(
                mitigation_scenarios_thresholds,
                oem_predicted_color,
                self.value,
                tolerance,
            )
            return predicted_color

        # Avoidance scenarios
        elif is_avoidance:
            logger.debug(f"Test name '{self.test_name}' is in avoidance scenarios.")
            self.prediction_result, predicted_color = check_thresholds(
                avoidance_thresholds, oem_predicted_color, self.value, tolerance
            )
            return predicted_color

        # Warning scenarios
        elif is_warning:
            logger.debug(f"Test name '{self.test_name}' is in warning scenarios.")
            self.prediction_result, predicted_color = check_thresholds(
                warning_thresholds, oem_predicted_color, self.value, tolerance
            )
            return predicted_color
        elif is_road_edge:
            logger.debug(f"Test name '{self.test_name}' is in road edge scenarios.")

            self.prediction_result, predicted_color = check_thresholds(
                road_edge_thresholds, oem_predicted_color, self.value, tolerance
            )
            return predicted_color
        elif is_elk_target:
            logger.debug(f"Test name '{self.test_name}' is in ELK target scenarios.")
            self.prediction_result, predicted_color = check_thresholds(
                elk_target_thresholds, oem_predicted_color, self.value, tolerance
            )
            return predicted_color

        # Unknown category
        else:
            self.prediction_result = PredictionResult.UNKNOWN
            logger.debug(
                f"Test name '{self.test_name}' not recognized for computed color logic."
            )
            return PredictionColor.GREY

    @computed_color.setter
    def computed_color(self, value):
        self._computed_color = value

    def get_lsc_computed_color(self, vehicle_response, doors):
        lsc_avoidance_scenarios = [
            "CCCscp - SfS",
            "CMCscp - SfS",
            "CCFtap - SfS",
            "CMFtap - SfS",
            "CBNAO - SfS",
            "CPMRCm",
            "CPMRCs",
        ]
        lsc_mitigation_scenarios = ["CPMFC"]
        lsc_dooring_scenarios = ["CBDA"]

        is_avoidance = self.test_name in lsc_avoidance_scenarios
        is_mitigation = self.test_name in lsc_mitigation_scenarios
        is_dooring = self.test_name in lsc_dooring_scenarios
        logger.debug(
            f"is_avoidance: {is_avoidance}, is_mitigation: {is_mitigation}, is_dooring: {is_dooring}"
        )

        if is_avoidance or is_mitigation:
            if self.value <= 0.0:
                logger.debug(
                    f"Test name '{self.test_name}' is in avoidance or mitigation scenario with value <= 0.0."
                )
                logger.debug(f"Returning GREEN color.")

                self.prediction_result = PredictionResult.CORRECT
                return PredictionColor.GREEN
            else:
                logger.debug(
                    f"Test name '{self.test_name}' is in avoidance or mitigation scenario with value > 0.0."
                )
                logger.debug(f"Returning RED color.")
                self.prediction_result = PredictionResult.INCORRECT
                return PredictionColor.RED

        elif is_dooring:
            # LSC dooring thresholds logic
            # Vehicle response | Criteria | Doors | Colour Band
            # Information: TTC ≥ 2.30s, Driver's only -> Brown; TTC < 2.30s -> Red
            # Warning: TTC ≥ 1.70s, Driver's only -> Orange; All -> Yellow; TTC < 1.70s, Driver's only or All -> Red
            # Retention: Start @ TTC ≥ 1.70s AND End @ TTC ≤ -0.40s, Driver's only -> Yellow; All -> Green
            # Start @ TTC < 1.70s OR End @ TTC > -0.40s, Driver's only or All -> Red

            # vehicle_response: "Information", "Warning", "Retention"
            # doors: "Driver's only" or "All"
            ttc = self.value  # TTC value
            logger.debug(
                f"LSC Door scenario: value={ttc}, vehicle_response={vehicle_response}, doors={doors}"
            )
            logger.debug(
                f"vehicle_response==VehicleResponse.INFORMATION: {vehicle_response==VehicleResponse.INFORMATION}"
            )
            logger.debug(
                f"doors==DoorSelected.DRIVERS_ONLY: {doors==DoorSelected.DRIVERS_ONLY}"
            )
            if vehicle_response == VehicleResponse.INFORMATION:
                if doors == DoorSelected.DRIVERS_ONLY:
                    if ttc >= 2.30:
                        logger.debug(f"Returning BROWN color.")
                        return PredictionColor.BROWN
                    else:
                        logger.debug(f"Returning RED color.")
                        return PredictionColor.RED
                else:
                    logger.debug(f"Returning RED color.")
                    return PredictionColor.RED

            elif vehicle_response == VehicleResponse.WARNING:
                if ttc >= 1.70:
                    if doors == DoorSelected.DRIVERS_ONLY:
                        return PredictionColor.ORANGE
                    else:
                        return PredictionColor.YELLOW
                else:
                    return PredictionColor.RED

            elif vehicle_response == VehicleResponse.RETENTION:
                # @TODO: Confirm with Euro NCAP if the logic below is correct
                # if ttc_start >= 1.70 and ttc_end <= -0.40:
                if ttc <= -0.40:
                    if doors == DoorSelected.DRIVERS_ONLY:
                        return PredictionColor.YELLOW
                    else:
                        return PredictionColor.GREEN
                else:
                    return PredictionColor.RED


def check_extended_range(row, col, test_name):
    """
    Check if the given row and column indices correspond to an extended range cell
    for the specified test name. Returns CellType.
    """
    extended_range_cells = EXTENDED_RANGE_CELLS.get(test_name, [])
    if (row, col) in extended_range_cells:
        return TestRange.EXTENDED
    else:
        return TestRange.STANDARD


def get_test_matrix(prediction_df, test_name, stage_subelement_key):
    """
    Process the VRU predictions DataFrame to extract headforms  matrices,
    compute color percentages, and randomly select samples based on color distribution.

    Args:
        prediction_df (pd.DataFrame): DataFrame containing VRU predictions.

    Returns:
        None
    """

    # Ensure the DataFrame is not empty
    if prediction_df.empty:
        logger.error("The input DataFrame is empty.")
        return

    test_matrix = None
    matrix_indices = MATRIX_INDICES.get(test_name, None)

    if not matrix_indices:
        logger.error(f"Test name '{test_name}' not found in MATRIX_INDICES.")
        return

    start_row = matrix_indices["start_row"]
    n_rows = matrix_indices["n_rows"]
    start_col = matrix_indices["start_col"]
    n_cols = matrix_indices["n_cols"]

    test_matrix = prediction_df.iloc[
        start_row : start_row + n_rows,
        start_col : start_col + n_cols,
    ].reset_index(drop=True)

    test_matrix = test_matrix.iloc[:, :].astype(str).values.tolist()

    test_points = []

    test_start_col = matrix_indices["start_col"]
    test_start_row = matrix_indices["start_row"]
    # Convert all values in test_matrix to PredictionColor enum
    for i in range(len(test_matrix)):
        for j in range(len(test_matrix[0])):
            color_str = test_matrix[i][j].lower()
            enum_val = next(
                (k for k in PredictionColor if k.value.lower() == color_str),
                PredictionColor.GREY,
            )
            test_matrix[i][j] = enum_val
            if stage_subelement_key == StageSubelementKey.LSC:
                test_range = TestRange.STANDARD
            else:
                test_range = check_extended_range(i, j, test_name)
            attributes = {}
            # Add start_col -1, -2, -3 if available
            for offset in range(1, 5):
                col_idx = test_start_col - offset
                if col_idx >= 0:
                    if col_idx == 0:
                        if test_name == "CBNAO - SfS":
                            col_name = "d"
                        elif test_name in ["CBDA", "CPMRCm"]:
                            col_name = "Gap"
                        elif test_name in ["CPMFC"]:
                            col_name = "Distance"
                        else:
                            col_name = "VUT speed"
                    else:
                        col_name = str(prediction_df.columns[col_idx])
                    col_value = prediction_df.iloc[test_start_row + i, col_idx]
                    if col_value is not None and not pd.isna(col_value):
                        attributes[col_name] = col_value.strip()

            # Add row at index start_row -2 for the name and start_row -1 for the value
            if test_start_row == 1:
                row_name = str(prediction_df.columns[test_start_col])
            else:
                row_name = str(prediction_df.iloc[test_start_row - 2, test_start_col])

            if (
                pd.isna(row_name)
                or str(row_name).strip() == "nan"
                or "Unnamed" in str(row_name).strip()
            ):
                if test_start_row == 1:
                    # Search backward from test_start_col for the first non-NaN value in columns array
                    for col_idx in range(test_start_col, -1, -1):
                        potential_row_name = prediction_df.columns[col_idx]
                        if (
                            not pd.isna(potential_row_name)
                            and str(potential_row_name).strip() != "nan"
                            and "Unnamed" not in str(potential_row_name).strip()
                        ):
                            row_name = str(potential_row_name)
                            break
                else:
                    # Search backward from test_start_col for the first non-NaN value in row test_start_row - 2
                    for col_idx in range(test_start_col, -1, -1):
                        potential_row_name = prediction_df.iloc[
                            test_start_row - 2, col_idx
                        ]
                        if (
                            not pd.isna(potential_row_name)
                            and str(potential_row_name).strip() != "nan"
                        ):
                            row_name = str(potential_row_name)
                            break

            row_value = prediction_df.iloc[test_start_row - 1, test_start_col + j]

            if row_value is not None and not pd.isna(row_value):
                attributes[row_name] = row_value

            if "Impact Location" in attributes:
                attributes["Impact Location"] = (
                    str(int(float(attributes["Impact Location"]) * 100)) + "%"
                )
            test_points.append(
                TestPoint(
                    row=i,
                    col=j,
                    color=enum_val,
                    test_range=test_range,
                    attributes=attributes,
                )
            )

    for idx, row in enumerate(test_matrix):
        logger.debug("%d: %s", idx, row)

    # Get all extended range cells for the current test name
    if stage_subelement_key == StageSubelementKey.LSC:
        extended_range_cells = []
    else:
        extended_range_cells = EXTENDED_RANGE_CELLS.get(test_name, [])

    if HAS_MPL:
        logger.debug("Plotting matrix for test: %s", test_name)
        plot_matrix(test_matrix, extended_range_cells, name=test_name)
    return test_points


def get_prediction_methods(input_parameters_df, test_name):
    # Find the row where "Scenario" equals test_name
    logger.info(f"Test name: {test_name}")
    start_idx = input_parameters_df.index[input_parameters_df["Scenario"] == test_name]
    if len(start_idx) == 0:
        logger.error(
            f"Test name '{test_name}' not found in input_parameters_df['Scenario']."
        )
        return None, None
    start_idx = start_idx[0]

    # Find the next row where "Scenario" is not NaN after start_idx
    next_indices = input_parameters_df.index[
        (input_parameters_df.index > start_idx)
        & (input_parameters_df["Scenario"].notna())
    ]
    end_idx = next_indices[0] if len(next_indices) > 0 else len(input_parameters_df)

    # Get the relevant rows for this test_name
    input_params_rows = input_parameters_df.iloc[start_idx:end_idx]
    input_params_dict = dict(
        zip(
            input_params_rows["Input parameter"].astype(str),
            input_params_rows["Value"],
        )
    )
    logger.info(f"Input parameters for test '{test_name}': {input_params_dict}")

    standard_pred_value = input_params_dict["Prediction - Standard"].strip().lower()
    extended_pred_value = input_params_dict["Prediction - Extended"].strip().lower()

    standard_oem_prediction_method = PredictionSource.UNKNOWN
    if standard_pred_value == "vta":
        standard_oem_prediction_method = PredictionSource.VTA
    elif standard_pred_value == "self claimed":
        standard_oem_prediction_method = PredictionSource.SELF_CLAIMED

    extended_oem_prediction_method = PredictionSource.UNKNOWN
    if extended_pred_value == "vta":
        extended_oem_prediction_method = PredictionSource.VTA
    elif extended_pred_value == "self claimed":
        extended_oem_prediction_method = PredictionSource.SELF_CLAIMED
    logger.info(f"Standard OEM prediction method: {standard_oem_prediction_method}")
    logger.info(f"Extended OEM prediction method: {extended_oem_prediction_method}")

    if (
        standard_oem_prediction_method == PredictionSource.UNKNOWN
        or extended_oem_prediction_method == PredictionSource.UNKNOWN
    ):
        raise ValueError(
            f"OEM prediction method is 'Unknown' for test '{test_name}'. Please specify both standard and extended OEM prediction methods."
        )

    return (
        standard_oem_prediction_method,
        extended_oem_prediction_method,
    )
