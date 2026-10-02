# test_ingest.py

import pytest
from ingest import is_good_service, status_summary, parse


def make_line(name, line_id, mode, statuses):
    """Helper to build a fake TfL API line response for testing."""
    return {
        "id": line_id,
        "name": name,
        "modeName": mode,
        "lineStatuses": [
            {"statusSeverity": sev, "statusSeverityDescription": desc}
            for sev, desc in statuses
        ],
    }


# --- is_good_service ---

def test_is_good_service_true_for_single_good_status():
    line = make_line("Bakerloo", "bakerloo", "tube", [(10, "Good Service")])
    assert is_good_service(line) is True


def test_is_good_service_false_for_single_bad_status():
    line = make_line("Victoria", "victoria", "tube", [(6, "Severe Delays")])
    assert is_good_service(line) is False


def test_is_good_service_false_when_any_status_is_bad():
    line = make_line(
        "Metropolitan", "metropolitan", "tube",
        [(9, "Minor Delays"), (6, "Severe Delays")],
    )
    assert is_good_service(line) is False


def test_is_good_service_true_when_all_statuses_are_good():
    # A line could theoretically report "Good Service" more than once
    line = make_line(
        "Circle", "circle", "tube",
        [(10, "Good Service"), (10, "Good Service")],
    )
    assert is_good_service(line) is True


# --- status_summary ---

def test_status_summary_single_status():
    line = make_line("Bakerloo", "bakerloo", "tube", [(10, "Good Service")])
    assert status_summary(line) == "Good Service"


def test_status_summary_joins_multiple_statuses():
    line = make_line(
        "Metropolitan", "metropolitan", "tube",
        [(9, "Minor Delays"), (6, "Severe Delays")],
    )
    assert status_summary(line) == "Minor Delays; Severe Delays"


# --- parse ---

def test_parse_good_service_line():
    line = make_line("Bakerloo", "bakerloo", "tube", [(10, "Good Service")])
    result = parse(line)
    assert result == {
        "line_id": "bakerloo",
        "line_name": "Bakerloo",
        "mode": "tube",
        "is_good": True,
        "status_description": "Good Service",
    }


def test_parse_disrupted_line():
    line = make_line("Victoria", "victoria", "tube", [(6, "Severe Delays")])
    result = parse(line)
    assert result["is_good"] is False
    assert result["status_description"] == "Severe Delays"


def test_parse_multi_status_line():
    line = make_line(
        "Metropolitan", "metropolitan", "tube",
        [(9, "Minor Delays"), (6, "Severe Delays")],
    )
    result = parse(line)
    assert result["line_id"] == "metropolitan"
    assert result["is_good"] is False
    assert result["status_description"] == "Minor Delays; Severe Delays"