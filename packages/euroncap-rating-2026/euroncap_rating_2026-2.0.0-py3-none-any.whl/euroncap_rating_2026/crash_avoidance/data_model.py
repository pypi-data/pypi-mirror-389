STAGE_SUBELEMENTS = [
    {
        "Stage ": "Crash Avoidance",
        "Stage element": "Frontal Collisions",
        "Stage subelement": "Car & PTW",
    },
    {
        "Stage ": "Crash Avoidance",
        "Stage element": "Frontal Collisions",
        "Stage subelement": "Pedestrian & Cyclist",
    },
    {
        "Stage ": "Crash Avoidance",
        "Stage element": "Lane Departure Collisions",
        "Stage subelement": "Single Vehicle",
    },
    {
        "Stage ": "Crash Avoidance",
        "Stage element": "Lane Departure Collisions",
        "Stage subelement": "Car & PTW",
    },
    {
        "Stage ": "Crash Avoidance",
        "Stage element": "Low Speed Collisions",
        "Stage subelement": "Car & PTW",
    },
    {
        "Stage ": "Crash Avoidance",
        "Stage element": "Low Speed Collisions",
        "Stage subelement": "Pedestrian & Cyclist",
    },
]

MATRIX_INDICES = {
    "CCRs": {"start_row": 1, "n_rows": 8, "start_col": 3, "n_cols": 7},
    "CCRm": {"start_row": 12, "n_rows": 11, "start_col": 3, "n_cols": 7},
    "CCRb": {"start_row": 26, "n_rows": 11, "start_col": 3, "n_cols": 7},
    "CCFhos": {"start_row": 40, "n_rows": 8, "start_col": 4, "n_cols": 4},
    "CCFhol": {"start_row": 51, "n_rows": 8, "start_col": 4, "n_cols": 4},
    "CCFtap": {"start_row": 62, "n_rows": 4, "start_col": 4, "n_cols": 6},
    "CCCscp": {"start_row": 69, "n_rows": 7, "start_col": 3, "n_cols": 7},
    "CMRs": {"start_row": 79, "n_rows": 8, "start_col": 4, "n_cols": 5},
    "CMRb": {"start_row": 90, "n_rows": 11, "start_col": 4, "n_cols": 5},
    "CMFtap": {"start_row": 104, "n_rows": 4, "start_col": 4, "n_cols": 6},
    "CMCscp": {"start_row": 111, "n_rows": 9, "start_col": 3, "n_cols": 7},
    "CPLA_day": {"start_row": 1, "n_rows": 10, "start_col": 4, "n_cols": 7},
    "CPLA_night": {"start_row": 14, "n_rows": 10, "start_col": 4, "n_cols": 7},
    "CBLA": {"start_row": 27, "n_rows": 10, "start_col": 4, "n_cols": 7},
    "CPTAfs && CPTAns": {"start_row": 40, "n_rows": 5, "start_col": 4, "n_cols": 7},
    "CPTAfo && CPTAno": {"start_row": 48, "n_rows": 5, "start_col": 4, "n_cols": 7},
    "CBTAfs && CBTAns": {"start_row": 56, "n_rows": 5, "start_col": 4, "n_cols": 7},
    "CBTAfo && CBTAno": {"start_row": 64, "n_rows": 5, "start_col": 4, "n_cols": 7},
    "CPNA_day": {"start_row": 72, "n_rows": 6, "start_col": 4, "n_cols": 7},
    "CPNA_night": {"start_row": 81, "n_rows": 6, "start_col": 4, "n_cols": 7},
    "CPFA_day": {"start_row": 90, "n_rows": 6, "start_col": 4, "n_cols": 7},
    "CPFA_night": {"start_row": 99, "n_rows": 6, "start_col": 4, "n_cols": 7},
    "CPNCO_day": {"start_row": 108, "n_rows": 6, "start_col": 4, "n_cols": 7},
    "CPNCO_night": {"start_row": 117, "n_rows": 6, "start_col": 4, "n_cols": 7},
    "CBNA": {"start_row": 126, "n_rows": 6, "start_col": 4, "n_cols": 7},
    "CBNAO": {"start_row": 135, "n_rows": 6, "start_col": 4, "n_cols": 7},
    "CBFA": {"start_row": 144, "n_rows": 6, "start_col": 4, "n_cols": 7},
    "ELK-RE": {"start_row": 1, "n_rows": 6, "start_col": 1, "n_cols": 6},
    "C2C ELK-ON": {"start_row": 1, "n_rows": 6, "start_col": 3, "n_cols": 4},
    "C2C ELK-OVU": {"start_row": 10, "n_rows": 9, "start_col": 2, "n_cols": 6},
    "C2C ELK-OVI": {"start_row": 22, "n_rows": 5, "start_col": 4, "n_cols": 5},
    "C2M ELK-ON": {"start_row": 30, "n_rows": 6, "start_col": 3, "n_cols": 4},
    "C2M ELK-OVU": {"start_row": 39, "n_rows": 9, "start_col": 2, "n_cols": 6},
    "C2M ELK-OVI": {"start_row": 51, "n_rows": 5, "start_col": 4, "n_cols": 5},
    "CCCscp - SfS": {"start_row": 1, "n_rows": 1, "start_col": 1, "n_cols": 5},
    "CMCscp - SfS": {"start_row": 5, "n_rows": 1, "start_col": 1, "n_cols": 7},
    "CCFtap - SfS": {"start_row": 9, "n_rows": 1, "start_col": 1, "n_cols": 3},
    "CMFtap - SfS": {"start_row": 13, "n_rows": 1, "start_col": 1, "n_cols": 4},
    "CBNAO - SfS": {"start_row": 1, "n_rows": 2, "start_col": 1, "n_cols": 3},
    "CPMRCm": {"start_row": 6, "n_rows": 3, "start_col": 1, "n_cols": 2},
    "CPMRCs": {"start_row": 12, "n_rows": 2, "start_col": 1, "n_cols": 3},
    "CPMFC": {"start_row": 17, "n_rows": 2, "start_col": 1, "n_cols": 3},
    "CBDA": {"start_row": 22, "n_rows": 4, "start_col": 1, "n_cols": 3},
}

TOTAL_SCORES = {
    "CCRs": {"Standard": 1.2, "Extended": 0.15, "Robustness": 0.15},
    "CCRm": {"Standard": 2.4, "Extended": 0.3, "Robustness": 0.3},
    "CCRb": {"Standard": 1.6, "Extended": 0.2, "Robustness": 0.2},
    "CCFhos": {"Standard": 2.0, "Extended": 0.25, "Robustness": 0.25},
    "CCFhol": {"Standard": 2.0, "Extended": 0.25, "Robustness": 0.25},
    "CCFtap": {"Standard": 4.0, "Extended": 0.5, "Robustness": 0.5},
    "CCCscp": {"Standard": 6.0, "Extended": 0.75, "Robustness": 0.75},
    "CMRs": {"Standard": 1.2, "Extended": 0.15, "Robustness": 0.15},
    "CMRb": {"Standard": 1.6, "Extended": 0.2, "Robustness": 0.2},
    "CMFtap": {"Standard": 4.0, "Extended": 0.5, "Robustness": 0.5},
    "CMCscp": {"Standard": 6.0, "Extended": 0.75, "Robustness": 0.75},
    "CPLA_day": {"Standard": 1.0, "Extended": 0.125, "Robustness": 0.25},
    "CPLA_night": {"Standard": 1.0, "Extended": 0.125, "Robustness": None},
    "CBLA": {"Standard": 2.0, "Extended": 0.25, "Robustness": 0.25},
    "CPTAfs && CPTAns": {"Standard": 1.0, "Extended": 0.125, "Robustness": 0.125},
    "CPTAfo && CPTAno": {"Standard": 1.0, "Extended": 0.125, "Robustness": 0.125},
    "CBTAfs && CBTAns": {"Standard": 1.0, "Extended": 0.125, "Robustness": 0.125},
    "CBTAfo && CBTAno": {"Standard": 1.0, "Extended": 0.125, "Robustness": 0.125},
    "CPNA_day": {"Standard": 0.5, "Extended": 0.0625, "Robustness": 0.125},
    "CPNA_night": {"Standard": 0.5, "Extended": 0.0625, "Robustness": None},
    "CPFA_day": {"Standard": 0.5, "Extended": 0.0625, "Robustness": 0.125},
    "CPFA_night": {"Standard": 0.5, "Extended": 0.0625, "Robustness": None},
    "CPNCO_day": {"Standard": 1.0, "Extended": 0.125, "Robustness": 0.25},
    "CPNCO_night": {"Standard": 1.0, "Extended": 0.125, "Robustness": None},
    "CBNA": {"Standard": 1.0, "Extended": 0.125, "Robustness": 0.125},
    "CBFA": {"Standard": 1.0, "Extended": 0.125, "Robustness": 0.125},
    "CBNAO": {"Standard": 2.0, "Extended": 0.25, "Robustness": 0.25},
    "ELK-RE": {"Standard": 4.0, "Extended": 0.5, "Robustness": 0.5},
    "C2C ELK-ON": {"Standard": 2.0, "Extended": 0.25, "Robustness": 0.25},
    "C2C ELK-OVU": {"Standard": 1.0, "Extended": 0.125, "Robustness": 0.125},
    "C2C ELK-OVI": {"Standard": 1.0, "Extended": 0.125, "Robustness": 0.125},
    "C2M ELK-ON": {"Standard": 2.0, "Extended": 0.25, "Robustness": 0.25},
    "C2M ELK-OVU": {"Standard": 1.0, "Extended": 0.125, "Robustness": 0.125},
    "C2M ELK-OVI": {"Standard": 1.0, "Extended": 0.125, "Robustness": 0.125},
    "CCCscp - SfS": {"Standard": 3.0},
    "CMCscp - SfS": {"Standard": 3.0},
    "CCFtap - SfS": {"Standard": 1.0},
    "CMFtap - SfS": {"Standard": 3.0},
    "CBNAO - SfS": {"Standard": 3.0},
    "CPMRCm": {"Standard": 1.5},
    "CPMRCs": {"Standard": 1.5},
    "CPMFC": {"Standard": 2.0},
    "CBDA": {"Standard": 2.0},
}

STANDARD_RANGE_VERIFICATION_TEST_NUM = {
    "CCRs": 3,
    "CCRm": 3,
    "CCRb": 3,
    "CCFhos": 4,
    "CCFhol": 4,
    "CCFtap": 3,
    "CCCscp": 5,
    "CMRs": 3,
    "CMRb": 3,
    "CMFtap": 3,
    "CMCscp": 5,
    "CPLA_day": 3,
    "CPLA_night": 3,
    "CBLA": 3,
    "CPTAfs && CPTAns": 3,
    "CPTAfo && CPTAno": 3,
    "CBTAfs && CBTAns": 3,
    "CBTAfo && CBTAno": 3,
    "CPNA_day": 3,
    "CPNA_night": 3,
    "CPFA_day": 3,
    "CPFA_night": 3,
    "CPNCO_day": 3,
    "CPNCO_night": 3,
    "CBNA": 3,
    "CBFA": 3,
    "CBNAO": 3,
    "ELK-RE": 3,
    "C2C ELK-ON": 3,
    "C2C ELK-OVU": 3,
    "C2C ELK-OVI": 3,
    "C2M ELK-ON": 3,
    "C2M ELK-OVU": 3,
    "C2M ELK-OVI": 3,
}

EXTENDED_RANGE_CELLS = {
    "CCRs": [
        *((i, 0) for i in range(8)),  # first col
        *((i, 6) for i in range(8)),  # last col
    ],
    "CCRm": [
        *((i, 0) for i in range(11)),  # first col
        *((i, 6) for i in range(11)),  # last col
    ],
    "CCRb": [
        *((i, 0) for i in range(11)),  # first col
        *((i, 6) for i in range(11)),  # last col
        *(
            (row, col) for row in range(6, 11) for col in range(7)
        ),  # last 5 rows, all cols
    ],
    "CCFhos": [
        *((i, 0) for i in range(8)),  # first col
        *(
            (row, col) for row in range(6, 8) for col in range(4)
        ),  # last 2 rows, all cols
    ],
    "CCFhol": [
        *((i, 0) for i in range(8)),  # first col
        *(
            (row, col) for row in range(6, 8) for col in range(4)
        ),  # last 2 rows, all cols
    ],
    "CCFtap": [
        *((i, 5) for i in range(4)),  # last col
        *((3, j) for j in range(6)),  # last row
    ],
    "CCCscp": [
        (0, 5),
        (0, 6),
        (1, 5),
        (1, 6),
        (5, 0),
        (6, 0),
        (5, 1),
        (6, 1),
    ],
    "CMRs": [
        *((i, 0) for i in range(8)),  # first col
        *((i, 4) for i in range(8)),  # last col
    ],
    "CMRb": [
        *((i, 0) for i in range(11)),  # first col
        *((i, 4) for i in range(11)),  # last col
        *(
            (row, col) for row in range(6, 11) for col in range(4)
        ),  # last 5 rows, all cols
    ],
    "CMFtap": [
        *((i, 5) for i in range(4)),  # last col
        *((3, j) for j in range(6)),  # last row
    ],
    "CMCscp": [
        (0, 5),
        (0, 6),
        (1, 5),
        (1, 6),
        (5, 0),
        (6, 0),
        (5, 1),
        (6, 1),
    ],
    "CPLA_day": [
        *(
            (row, col) for row in range(6) for col in [0, 2, 3]
        ),  # first 6 rows, cols 0,2,3
        *(
            (row, col) for row in range(6, 10) for col in [0, 1, 3]
        ),  # next 4 rows, cols 0,1,3
    ],
    "CPLA_night": [
        *(
            (row, col) for row in range(6) for col in [0, 2, 3]
        ),  # first 6 rows, cols 0,2,3
        *(
            (row, col) for row in range(6, 10) for col in [0, 1, 3]
        ),  # next 4 rows, cols 0,1,3
    ],
    "CBLA": [
        *(
            (row, col) for row in range(6) for col in [0, 2, 3]
        ),  # first 6 rows, cols 0,2,3
        *(
            (row, col) for row in range(6, 10) for col in [0, 1, 3]
        ),  # next 4 rows, cols 0,1,3
    ],
    "CPTAfs && CPTAns": [
        *(
            (row, col) for row in range(5) for col in [0, 1, 3, 4]
        ),  # next 4 rows, cols 0,1,3,4
        (3, 2),  # last row-1, col 2
    ],
    "CPTAfo && CPTAno": [
        *(
            (row, col) for row in range(5) for col in [0, 1, 3, 4]
        ),  # next 4 rows, cols 0,1,3,4
        (3, 2),  # last row-1, col 2
    ],
    "CBTAfs && CBTAns": [
        (0, 2),
        (1, 2),
        (2, 2),
        (3, 2),
        (4, 2),
    ],
    "CBTAfo && CBTAno": [
        *(
            (row, col) for row in range(4) for col in [0, 1, 3, 4]
        ),  # next 4 rows, cols 0,1,3,4
        (3, 2),  # last row-1, col 2
        (4, 1),
        (4, 3),
    ],
    "CPNA_day": [
        *((row, col) for row in range(6) for col in [0, 4]),
    ],
    "CPNA_night": [
        *((row, col) for row in range(6) for col in [0, 4]),
    ],
    "CPFA_day": [
        *((row, col) for row in range(6) for col in [0, 1, 3, 4]),
    ],
    "CPFA_night": [
        *((row, col) for row in range(6) for col in [0, 1, 3, 4]),
    ],
    "CPNCO_day": [
        *((row, col) for row in range(6) for col in [0, 2]),
    ],
    "CPNCO_night": [
        *((row, col) for row in range(6) for col in [0, 2]),
    ],
    "CBNA": [
        *((row, col) for row in range(6) for col in [0, 3, 4]),
    ],
    "CBNAO": [
        *((row, col) for row in range(6) for col in [0, 3, 4]),
    ],
    "CBFA": [
        *((row, col) for row in range(6) for col in [0, 1, 4]),
    ],
    "ELK-RE": [
        *((row, col) for row in range(6) for col in [5]),
        *((row, col) for row in [0, 1, 5] for col in range(6)),
    ],
    "C2C ELK-ON": [
        *((row, col) for row in [0, 1, 3, 4, 5] for col in range(4)),
    ],
    "C2C ELK-OVU": [
        *((row, col) for row in range(9) for col in [0, 5]),
        *((row, col) for row in [0, 1, 3, 4, 5, 6, 7, 8] for col in range(6)),
    ],
    "C2C ELK-OVI": [
        *((row, col) for row in range(5) for col in [0, 4]),
        *((row, col) for row in [0, 1, 3, 4] for col in range(5)),
    ],
    "C2M ELK-ON": [
        *((row, col) for row in [0, 1, 3, 4, 5] for col in range(4)),
    ],
    "C2M ELK-OVU": [
        *((row, col) for row in range(9) for col in [0, 5]),
        *((row, col) for row in [3, 4, 5, 6, 7, 8] for col in range(6)),
    ],
    "C2M ELK-OVI": [
        *((row, col) for row in range(5) for col in [0, 4]),
        *((row, col) for row in [3, 4] for col in range(5)),
    ],
}

STAGE_SUBELEMENT_TO_LOADCASES = {
    "FC": {
        "Car & PTW": [
            "CCRs",
            "CCRm",
            "CCRb",
            "CCFhos",
            "CCFhol",
            "CCFtap",
            "CCCscp",
            "CMRs",
            "CMRb",
            "CMFtap",
            "CMCscp",
        ],
        "Ped & Cyc": [
            "CPLA_day",
            "CPLA_night",
            "CBLA",
            "CPTAfs && CPTAns",
            "CPTAfo && CPTAno",
            "CBTAfs && CBTAns",
            "CBTAfo && CBTAno",
            "CPNA_day",
            "CPNA_night",
            "CPFA_day",
            "CPFA_night",
            "CPNCO_day",
            "CPNCO_night",
            "CBNA",
            "CBFA",
            "CBNAO",
        ],
    },
    "LDC": {
        "Single Veh": [
            "Driveability",
            "Driver State Link",
            "ELK-RE",
        ],
        "Car & PTW": [
            "C2C ELK-ON",
            "C2C ELK-OVU",
            "C2C ELK-OVI",
            "C2M ELK-ON",
            "C2M ELK-OVU",
            "C2M ELK-OVI",
        ],
    },
    "LSC": {
        "Ped & Cyc": ["CBNAO - SfS", "CPMRCm", "CPMRCs", "CPMFC", "CBDA"],
        "Car & PTW": [
            "CCCscp - SfS",
            "CMCscp - SfS",
            "CCFtap - SfS",
            "CMFtap - SfS",
        ],
    },
}

SCORE_FROM_VERIFICATION_TEST_OUTCOME = {
    "Standard": {
        "VTA": {
            5: {5: 100, 4: 80, 3: 60, 2: 40, 1: 20, 0: 0},
            4: {4: 100, 3: 75, 2: 50, 1: 25, 0: 0},
            3: {3: 100, 2: 67, 1: 33, 0: 0},
        },
        "Self Claimed": {
            5: {5: 100, 4: 80, 3: 0, 2: 0, 1: 0, 0: 0},
            4: {4: 100, 3: 75, 2: 0, 1: 0, 0: 0},
            3: {3: 100, 2: 67, 1: 0, 0: 0},
        },
    },
    "Extended": {
        "VTA": {
            2: {2: 100, 1: 50, 0: 0},
        },
        "Self Claimed": {
            2: {2: 100, 1: 0, 0: 0},
        },
    },
}


SUBTEST_TO_TEST_DICT = {
    "CPLA_day": "CPLA",
    "CPLA_night": "CPLA",
    "CPTAfs && CPTAns": "CPTA",
    "CPTAfo && CPTAno": "CPTA",
    "CBTAfs && CBTAns": "CBTA",
    "CBTAfo && CBTAno": "CBTA",
    "CPNA_day": "CPNA",
    "CPNA_night": "CPNA",
    "CPFA_day": "CPFA",
    "CPFA_night": "CPFA",
    "CPNCO_day": "CPNCO",
    "CPNCO_night": "CPNCO",
    "C2C ELK-OVU": "C2C ELK-OV",
    "C2C ELK-OVI": "C2C ELK-OV",
    "C2M ELK-OVU": "C2M ELK-OV",
    "C2M ELK-OVI": "C2M ELK-OV",
}

STAGE_SUBELEMENT_TO_CATEGORIES = {
    "FC": ["Turning", "Crossing", "Longitudinal"],
    "LDC": [
        "Driver Acceptance",
        "Lane Departure",
        "ELK Car-to-car",
        "ELK Car-to-motorcyclist",
    ],
    "LSC": [
        "Turning",
        "Crossing",
        "Crossing",
        "Manoeuvring",
        "Dooring",
    ],
}
