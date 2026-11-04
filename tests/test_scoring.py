import json

import pytest

from course2video.cli import main
from course2video.scoring import cohen_kappa, read_sheet, score_report

HEADER = "slide_id,accuracy,completeness,formulas,clarity,faithfulness,equation_reading,comment\n"


def _sheet(path, rows):
    path.write_text(HEADER + "".join(rows), encoding="utf-8")
    return path


def test_kappa():
    assert cohen_kappa([2, 2, 1, 0], [2, 2, 1, 0]) == 1.0
    assert cohen_kappa([2, 1, 2, 1], [1, 2, 1, 2]) < 0


def test_invalid_score_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="must be 0, 1, 2"):
        read_sheet(_sheet(tmp_path / "a.csv", ["1,3,2,2,2,2,2,\n"]))


def test_report_with_two_reviewers_and_automatic_checks(tmp_path):
    a = _sheet(tmp_path / "anna.csv", ["1,2,2,2,2,2,2,\n", "2,1,2,,2,2,2,\n", "3,0,1,1,1,1,1,wrong\n"])
    b = _sheet(tmp_path / "mo.csv", ["1,2,2,2,2,2,2,\n", "2,2,2,,2,2,2,\n", "3,0,0,1,1,1,1,\n"])
    out = tmp_path / "run"
    out.mkdir()
    (out / "grounding.json").write_text(json.dumps({"flagged_slides": [3]}))
    log = tmp_path / "log.csv"
    log.write_text("reviewer,course,slides,review_minutes,corrections,correction_kinds,"
                   "manual_estimate_minutes\nanna,MIT 18.05,14,35,6,wording; one formula,240\n")
    report = score_report({"anna": a, "mo": b}, out, log)
    acc = report["criteria"]["accuracy"]
    assert acc["disagreements"] == [2]
    assert report["criteria"]["formulas"]["per_reviewer"]["anna"] == 1.5
    g = report["automatic_checks"]["grounding"]
    assert g["flagged"] == [3] and g["mean_score_flagged"] < g["mean_score_not_flagged"]
    assert report["review_time"][0]["review_minutes"] == "35"


def test_score_command_writes_markdown_and_json(tmp_path, capsys):
    a = _sheet(tmp_path / "anna.csv", ["1,2,2,2,2,2,2,\n"])
    b = _sheet(tmp_path / "mo.csv", ["1,2,1,2,2,2,2,\n"])
    rep = tmp_path / "results" / "mit.md"
    assert main(["score", str(a), str(b), "--report", str(rep)]) == 0
    assert "| completeness |" in rep.read_text() and rep.with_suffix(".json").exists()
    assert "Scoring report" in capsys.readouterr().out
