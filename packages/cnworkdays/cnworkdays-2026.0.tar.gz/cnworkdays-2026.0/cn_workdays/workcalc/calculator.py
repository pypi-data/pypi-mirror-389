import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Union

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

DateInput = Union[str, datetime, date]  # Type alias for date inputs


def is_weekday(d: date) -> bool:
    """Check if a given date falls on a weekday (Monday through Friday).

    Args:
        d: The date object to check

    Returns:
        True if the date is a weekday (Mon-Fri), False if weekend (Sat-Sun)

    Examples:
        >>> from datetime import date
        >>> is_weekday(date(2024, 5, 11))  # Saturday
        False
        >>> is_weekday(date(2024, 5, 12))  # Sunday
        False
        >>> is_weekday(date(2024, 5, 13))  # Monday
        True
    """
    return d.weekday() < 5


@dataclass
class Config:
    """Configuration for working day calculations.

    Attributes:
        holidays: List of holiday dates (must be weekdays)
        compensatory_working_days: List of working days that fall on weekends
        range_min: Minimum valid date for calculations
        range_max: Maximum valid date for calculations
    """

    holidays: list[date]
    compensatory_working_days: list[date]
    range_min: date
    range_max: date

    def __post_init__(self) -> None:
        """Validate configuration data after initialization."""
        errors = []
        # Check holidays for correctness
        for holiday in self.holidays:
            if not is_weekday(holiday):
                errors.append(f"Holiday {holiday} must be a weekday")

        # Check compensatory working days for correctness
        for working_day in self.compensatory_working_days:
            if is_weekday(working_day):
                errors.append(
                    f"Compensatory working day {working_day} must be a weekend"
                )

        # Validate that all dates fall within the configured range.
        all_dates = self.holidays + self.compensatory_working_days
        min_date = min(all_dates)
        max_date = max(all_dates)

        if self.range_max < max_date:
            errors.append(f"range_max should be {max_date}")

        if self.range_min > min_date:
            errors.append(f"range_min should be {min_date}")

        if errors:
            raise ValueError("\n".join(errors))


def parse_date(date_input: DateInput) -> date:
    """Convert various date formats to a date object.

    Args:
        date_input: Date input in one of the following formats:
            - string: ISO 8601 format ("2024-06-07", "20240607") or "%Y-%m-%d" format without leading zero ("2024-6-7")
            - datetime object
            - date object

    Returns:
        Converted date object

    Raises:
        ValueError: If date_input format is invalid

    Examples:
        >>> from datetime import datetime, date
        >>> parse_date("2024-06-07")
        datetime.date(2024, 6, 7)
        >>> parse_date("20240607")
        datetime.date(2024, 6, 7)
        >>> parse_date("2024-6-7")
        datetime.date(2024, 6, 7)
        >>> parse_date(datetime(2024, 6, 7, 0, 0))
        datetime.date(2024, 6, 7)
        >>> parse_date(date(2024, 6, 7))
        datetime.date(2024, 6, 7)
    """
    if isinstance(date_input, str):
        try:
            return date.fromisoformat(date_input)
        except ValueError:
            return datetime.strptime(date_input, "%Y-%m-%d").date()
    elif isinstance(date_input, datetime):
        return date_input.date()
    elif isinstance(date_input, date):
        return date_input
    raise ValueError("Invalid date input")


def load_config(file_path: Union[str, Path] = CONFIG_PATH) -> Config:
    """Load configuration from JSON file.

    Args:
        file_path: Path to configuration JSON file

    Returns:
        Config object with holiday and working day information
    """
    with open(file_path, "r") as _f:
        data = json.load(_f)

    config = Config(
        # List of holidays (Monday to Friday)
        holidays=list(map(parse_date, data["holidays"])),
        # List of compensatory working days (Saturday and Sunday)
        compensatory_working_days=list(
            map(parse_date, data["compensatory_working_days"])
        ),
        range_max=parse_date(data["range_max"]),
        range_min=parse_date(data["range_min"]),
    )
    return config


def is_working_day(
    date_input: DateInput,
    holidays: list[date],
    compensatory_working_days: list[date],
) -> bool:
    """Check if a given date is a working day, considering holidays and compensatory days.

    A date is considered a working day if it is either:
    1. A weekday that is not a holiday
    2. A weekend that is designated as a compensatory working day

    Args:
        date_input: Date to check
        holidays: List of holiday dates
        compensatory_working_days: List of compensatory working dates

    Returns:
        True if date is a working day, False otherwise

    Examples:
        >>> from datetime import date
        >>> is_working_day("20240511", [], [date(2024, 5, 11)])
        True
        >>> is_working_day("20240512", [], [date(2024, 5, 11)])
        False
    """
    date_obj = parse_date(date_input)
    if is_weekday(date_obj) and date_obj not in holidays:
        return True
    if not is_weekday(date_obj) and date_obj in compensatory_working_days:
        return True
    return False


def calculate_working_date(start_date: DateInput, num_days: int) -> date:
    """Calculate a date by adding or subtracting working days in the Chinese calendar.

    This function handles the complexity of Chinese working calendar, including:
    - Regular weekends (Sat-Sun)
    - Public holidays
    - Compensatory working days (weekend days that are worked to compensate for holidays)

    Args:
        start_date: The reference date to start calculations from. Accepts:
            - string (format: "YYYYMMDD" or "YYYY-MM-DD")
            - datetime object
            - date object
        num_days: Number of working days to calculate:
            - Positive values add working days
            - Negative values subtract working days
            - Zero returns the next working day if start_date is non-working

    Returns:
        Calculated working date

    Raises:
        ValueError: When either:
            - start_date is outside the configured valid date range
            - the resulting calculated date would fall outside the valid range

    Examples:
        >>> from datetime import date
        >>> calculate_working_date("20240607", 1)
        datetime.date(2024, 6, 11)
        >>> calculate_working_date("2024-06-08", 0)
        datetime.date(2024, 6, 11)
        >>> calculate_working_date("2024-6-8", 0)
        datetime.date(2024, 6, 11)
        >>> calculate_working_date(date(2024, 5, 13), -1)
        datetime.date(2024, 5, 11)
    """
    # Parse the start_date to a date object
    current_date: date = parse_date(start_date)

    # Determine direction of days based on num_days (positive for addition, negative for subtraction)
    if num_days < 0:
        days_direction = -1
    else:
        days_direction = 1
    remaining_days = abs(num_days)

    # Load the configuration containing holidays and valid date range
    config = load_config()

    # Validate that the start_date is within the allowed date range
    if current_date < config.range_min or current_date > config.range_max:
        raise ValueError(
            f"Start date {current_date} is outside the valid range [{config.range_min}, {config.range_max}]"
        )

    # Count the number of working days as we traverse through the calendar
    working_days_count = None

    while True:
        # Check if the current date is a working day (i.e., not a holiday or compensatory day off)
        if is_working_day(
            current_date, config.holidays, config.compensatory_working_days
        ):
            if working_days_count is None:
                working_days_count = 0
            else:
                working_days_count += 1
        # If the required number of working days has been reached, return the current date
        if working_days_count == remaining_days:
            # Ensure the final date is within the valid date range
            if current_date < config.range_min or current_date > config.range_max:
                raise ValueError(
                    f"Calculated date {current_date} is outside the valid range [{config.range_min}, {config.range_max}]"
                )

            return current_date
        # Move to the next date in the specified direction (forward or backward)
        current_date += timedelta(days=days_direction)
