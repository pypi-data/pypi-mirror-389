import json
from pathlib import Path

import pytest

from cn_workdays.holiparse.parser import parse_holidays_comp_working_days


@pytest.fixture
def test_data_dir():
    """Fixture to provide the path to test data directory"""
    return Path(__file__).parent / "test_data"


def read_input_file(file_path: Path) -> str:
    """Read input file and return list of strings"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def read_expected_output(file_path: Path) -> dict:
    """Read expected output JSON file"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize(
    "input_file,expected_file,year",
    [
        ("holiparse_2018_input.txt", "holiparse_2018_output.json", "2018"),
        ("holiparse_2019_input.txt", "holiparse_2019_output.json", "2019"),
        ("holiparse_2020_input.txt", "holiparse_2020_output.json", "2020"),
        ("holiparse_2021_input.txt", "holiparse_2021_output.json", "2021"),
        ("holiparse_2022_input.txt", "holiparse_2022_output.json", "2022"),
        ("holiparse_2023_input.txt", "holiparse_2023_output.json", "2023"),
        ("holiparse_2024_input.txt", "holiparse_2024_output.json", "2024"),
        ("holiparse_2025_input.txt", "holiparse_2025_output.json", "2025"),
    ],
)
def test_parse_holidays_from_files(
    test_data_dir: Path, input_file: str, expected_file: str, year: str
):
    # Construct full file paths
    input_path = test_data_dir / input_file
    expected_path = test_data_dir / expected_file

    # Read input and expected output
    input_data = read_input_file(input_path)
    expected_output = read_expected_output(expected_path)

    # Run the function
    result = parse_holidays_comp_working_days(input_data)

    # Compare results
    assert result == expected_output
