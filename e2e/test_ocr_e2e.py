from dataclasses import asdict
from enum import Enum
import json
import sys
import cv2
import os
import pytest
from pathlib import Path

import yaml

sys.path.append("../src")

from neume_map import neume_map
from neume_compare import (
    calculate_scorecard,
)
from e2e_models import (
    MartyriaElement,
    NoteElement,
    TempoElement,
)
from model import load_onnx_model
from model_metadata import load_metadata
from ocr import PreprocessOptions, process_image, save_analysis
from levenshtein import backtrack_alignment, levenshtein_distance


# If you are tweaking only the interpretation code, set env SKIP_OCR=true
import os

SKIP_OCR = os.getenv("SKIP_OCR") == "true"

LEVENSHTEIN_THRESHOLD = 0.9
TIMEOUT_SECONDS = 120

report = []
report_full = []


# Generate reports after all tests have run
@pytest.fixture(scope="session", autouse=True)
def write_reports_at_end():
    yield
    Path("e2e.report.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    Path("e2e.report.full.json").write_text(
        json.dumps(report_full, indent=2), encoding="utf8"
    )


TABLE = [
    {
        "page": "anastasimatarion_john_p0011",
        "deskew": True,
        "despeckle": False,
        "close": False,
    },
    {
        "page": "heirmologion_john_p0120",
        "deskew": True,
        "despeckle": False,
        "close": False,
    },
    {
        "page": "liturgica_karamanis_1990_p0257",
        "deskew": True,
        "despeckle": True,
        "close": False,
    },
    {
        "page": "heirmologion_pandektis_1955_p0160",
        "deskew": True,
        "despeckle": True,
        "close": True,
        "splitLeftRight": True,
    },
    {
        "page": "doxastarion_pringos_p0141",
        "deskew": True,
        "despeckle": True,
        "close": True,
    },
    {
        "page": "vespers_sam_p0411",
    },
]


@pytest.mark.parametrize("row", TABLE, ids=lambda r: f"OCR-{r['page']}")
def test_ocr_page(row):
    page = row["page"]
    deskew = row.get("deskew", False)
    despeckle = row.get("despeckle", False)
    close = row.get("close", False)
    splitLeftRight = row.get("splitLeftRight", False)

    preprocess_options = PreprocessOptions()
    preprocess_options.deskew = deskew
    preprocess_options.despeckle = despeckle
    preprocess_options.close = close

    image_path = Path(f"data/{page}.png")
    byzx_path = Path(f"data/{page}.byzx")
    output_yaml = Path(f"data/{page}.actual.yaml")
    expected_yaml = Path(f"data/{page}.expected.yaml")

    # Load expected score (from byzx JSON)
    expected_score = json.loads(Path(byzx_path).read_text(encoding="utf8"))

    # Extract expected neumes
    expected_elements = []
    for i, e in enumerate(expected_score["staff"]["elements"]):
        if e["elementType"] == "Note":
            expected_elements.append(
                NoteElement(
                    neume=neume_map.get(e["quantitativeNeume"]),
                    index=i,
                    accidental=neume_map.get(e.get("accidental", None)),
                    fthora=neume_map.get(e.get("fthora", None)),
                    gorgon=neume_map.get(e.get("gorgonNeume", None)),
                    quality=neume_map.get(e.get("vocalExpressionNeume", None)),
                    time=neume_map.get(e.get("timeNeume", None)),
                    vareia=e.get("vareia", False),
                )
            )

        elif e["elementType"] == "Martyria":
            expected_elements.append(
                MartyriaElement(index=i, fthora=neume_map.get(e.get("fthora", None)))
            )
        elif e["elementType"] == "Tempo":
            expected_elements.append(
                TempoElement(index=i, neume=neume_map.get(e["neume"]))
            )

    yaml.safe_dump(
        {"interpreted_groups": [x.to_dict() for x in expected_elements]},
        expected_yaml.open("w", encoding="utf8"),
    )

    expected = [x.neume for x in expected_elements if isinstance(x, NoteElement)]

    # Run OCR only if needed
    if not os.path.exists(output_yaml) or not SKIP_OCR:
        classes = load_metadata("../models/metadata.json")
        model = load_onnx_model("../models/current_model.onnx")

        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        analysis = process_image(
            image,
            model,
            classes,
            preprocess_options=preprocess_options,
            split_lr=splitLeftRight,
        )

        save_analysis(analysis, filepath=output_yaml)

    # Load actual YAML output
    actual_groups = [
        group
        for page in yaml.safe_load(output_yaml.read_text(encoding="utf8"))["pages"]
        for group in page["interpreted_groups"]
    ]

    actual_elements = []

    for i, e in enumerate(actual_groups):
        if e["type"] == "note":
            actual_elements.append(
                NoteElement(
                    neume=e["neume"],
                    index=i,
                    accidental=e.get("accidental", None),
                    fthora=e.get("fthora", None),
                    gorgon=e.get("gorgon", None),
                    quality=e.get("quality", None),
                    time=e.get("time", None),
                    vareia=e.get("vareia", False),
                )
            )

        elif e["type"] == "martyria":
            actual_elements.append(
                MartyriaElement(index=i, fthora=e.get("fthora", None))
            )
        elif e["type"] == "tempo":
            actual_elements.append(TempoElement(index=i, neume=e["neume"]))

    actual = [x.neume for x in actual_elements if isinstance(x, NoteElement)]

    # Levenshtein
    distance, matrix = levenshtein_distance(expected, actual)

    similarity = 1 - distance / max(len(expected), len(actual))

    # Note-level comparison
    expected_notes = [x for x in expected_elements if isinstance(x, NoteElement)]
    actual_notes = [x for x in actual_elements if isinstance(x, NoteElement)]

    aligned_a, aligned_b = backtrack_alignment(expected_notes, actual_notes, matrix)
    scorecard = calculate_scorecard(aligned_a, aligned_b)

    # Log for report.json and report.full.json
    report.append(
        {
            "testName": f"OCR {page}",
            "page": page,
            "levenshteinSimilarity": similarity,
            "levenshteinDistance": distance,
            "scorecard": {
                "penalties": asdict(scorecard["penalties"]),
                "similarities": asdict(scorecard["similarities"]),
                "similarity": scorecard["similarity"],
            },
        }
    )

    report_full.append(
        {
            "testName": f"OCR {page}",
            "page": page,
            "levenshteinSimilarity": similarity,
            "levenshteinDistance": distance,
            "scorecard": {
                "penalties": asdict(scorecard["penalties"]),
                "totals": asdict(scorecard["totals"]),
                "similarities": asdict(scorecard["similarities"]),
                "similarity": scorecard["similarity"],
                "elements_with_issues": [
                    asdict(
                        x,
                        dict_factory=lambda x: {
                            k: (v.value if isinstance(v, Enum) else v) for k, v in x
                        },
                    )
                    for x in scorecard["elements_with_issues"]
                ],
            },
        }
    )

    # Assertion
    assert similarity >= LEVENSHTEIN_THRESHOLD
