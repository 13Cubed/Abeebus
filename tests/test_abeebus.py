import os
import sys

import pytest

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

import abeebus


def test_missing_file_error_goes_to_stderr(capsys):
    with pytest.raises(SystemExit) as exc_info:
        abeebus.getData(["does-not-exist-12345.txt"], "")
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Could not find the specified file" in captured.err
    assert "Could not find the specified file" not in captured.out


def test_unwritable_output_error_goes_to_stderr(capsys, tmp_path):
    missing_dir = tmp_path / "no-such-dir" / "out.csv"
    with pytest.raises(SystemExit) as exc_info:
        abeebus.writeData(["header"], str(missing_dir))
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Could not write the specified file" in captured.err
    assert "Could not write the specified file" not in captured.out


def test_write_data_roundtrip(tmp_path):
    outfile = tmp_path / "out.csv"
    abeebus.writeData(["a,b", "c,d"], str(outfile))
    with open(str(outfile), encoding="utf-8-sig") as fh:
        assert fh.read().splitlines() == ["a,b", "c,d"]
