import re
from collections import OrderedDict
from datetime import date, datetime, timedelta

YEAR_PATTERN = re.compile(r"国务院办公厅关于(\d{4})年")
HOLIDAY_PATTERN = re.compile(
    r"((\d{4})年)?(\d{1,2})月(\d{1,2})日(?:.*?(?:星期|周).*?）)?(至(((\d{4})年)?(\d{1,2})月)?(\d{1,2})日(?:.*?(?:星期|周).*?）)?)?放假"
)
HAS_COMP_WORKING_PATTERN = re.compile(r"(.*)上班")
COMP_WORKING_DAY_PATTERN = re.compile(
    r"((\d{4}年)?\d{1,2}月\d{1,2}日)（(?:星期|周)[六日]）"
)


def str_to_date(date_str: str) -> date:
    """Convert a Chinese date string in 'YYYY年MM月DD日' format to a date object.

    Args:
        date_str: String in format 'YYYY年MM月DD日'. Leading zeros are optional.

    Returns:
        datetime.date: The parsed date object.

    Examples:
        >>> import datetime
        >>> str_to_date("2023年11月01日")
        datetime.date(2023, 11, 1)
        >>> str_to_date("2023年1月1日")
        datetime.date(2023, 1, 1)
    """
    return datetime.strptime(date_str, "%Y年%m月%d日").date()


def parse_holidays(line: str, default_year: str) -> list[date]:
    """Extract holiday dates from a Chinese holiday announcement line.

    Parses holiday periods and returns a list of weekday dates (Monday-Friday) that are designated as holidays.

    Args:
        line: Text line containing holiday announcement in Chinese.
        default_year: Year to use when year is not specified in the announcement.

    Returns:
        list[date]: List of weekday dates designated as holidays, sorted chronologically.

    Examples:
        >>> import datetime
        >>> parse_holidays("一、元旦：2022年12月31日至2023年1月2日放假调休，共3天。","2023")
        [datetime.date(2023, 1, 2)]
        >>> parse_holidays("一、元旦：1月1日放假，与周末连休。","2024")
        [datetime.date(2024, 1, 1)]
        >>> parse_holidays("一、元旦：1月1日（周三）放假1天，不调休。","2025")
        [datetime.date(2025, 1, 1)]
        >>> parse_holidays("二、春节：2月10日至17日放假调休，共8天。2月4日（星期日）、2月18日（星期日）上班。鼓励各单位结合带薪年休假等制度落实，安排职工在除夕（2月9日）休息。","2024")
        [datetime.date(2024, 2, 12), datetime.date(2024, 2, 13), datetime.date(2024, 2, 14), datetime.date(2024, 2, 15), datetime.date(2024, 2, 16)]
        >>> parse_holidays("二、春节：1月28日（农历除夕、周二）至2月4日（农历正月初七、周二）放假调休，共8天。1月26日（周日）、2月8日（周六）上班。","2025")
        [datetime.date(2025, 1, 28), datetime.date(2025, 1, 29), datetime.date(2025, 1, 30), datetime.date(2025, 1, 31), datetime.date(2025, 2, 3), datetime.date(2025, 2, 4)]
        >>> parse_holidays("三、清明节：4月4日（周五）至6日（周日）放假，共3天。", "2025")
        [datetime.date(2025, 4, 4)]
        >>> parse_holidays("四、劳动节：5月1日（周四）至5日（周一）放假调休，共5天。4月27日（周日）上班。", "2025")
        [datetime.date(2025, 5, 1), datetime.date(2025, 5, 2), datetime.date(2025, 5, 5)]
        >>> parse_holidays("五、端午节：5月31日（周六）至6月2日（周一）放假，共3天。", "2025")
        [datetime.date(2025, 6, 2)]
        >>> parse_holidays("六、国庆节、中秋节：10月1日（周三）至8日（周三）放假调休，共8天。9月28日（周日）、10月11日（周六）上班。", "2025")
        [datetime.date(2025, 10, 1), datetime.date(2025, 10, 2), datetime.date(2025, 10, 3), datetime.date(2025, 10, 6), datetime.date(2025, 10, 7), datetime.date(2025, 10, 8)]
    """
    holidays = []
    for match in HOLIDAY_PATTERN.finditer(line):
        start_year = match.group(2) or default_year
        start_month, start_day = match.group(3), match.group(4)
        end_year = match.group(8) or default_year
        end_month = match.group(9) or start_month
        end_day = match.group(10) or start_day
        start_date = str_to_date(f"{start_year}年{start_month}月{start_day}日")
        end_date = str_to_date(f"{end_year}年{end_month}月{end_day}日")
        date_range = [
            start_date + timedelta(days=i)
            for i in range((end_date - start_date).days + 1)
        ]
        holidays.extend(
            [d for d in date_range if d.weekday() < 5]
        )  # Only include weekdays
    return list(OrderedDict.fromkeys(holidays))


def parse_compensatory_working_days(line: str, default_year: str) -> list[date]:
    """Extract compensatory working days from a Chinese holiday announcement line.

    Identifies weekend dates (Saturday-Sunday) that are designated as working days to compensate for holidays.

    Args:
        line: Text line containing compensatory working day announcement in Chinese.
        default_year: Year to use when year is not specified in the announcement.

    Returns:
        list[date]: List of weekend dates designated as working days, sorted chronologically.

    Examples:
        >>> import datetime
        >>> parse_compensatory_working_days("2022年12月31日（星期六）、2023年1月1日（星期日）、1月1日（星期日）上班。", "2023")
        [datetime.date(2022, 12, 31), datetime.date(2023, 1, 1)]
        >>> parse_compensatory_working_days("2月10日至17日放假调休，共8天。2月4日（星期日）、2月18日（星期日）上班。", "2024")
        [datetime.date(2024, 2, 4), datetime.date(2024, 2, 18)]
        >>> parse_compensatory_working_days("二、春节：1月28日（农历除夕、周二）至2月4日（农历正月初七、周二）放假调休，共8天。1月26日（周日）、2月8日（周六）上班。", "2025")
        [datetime.date(2025, 1, 26), datetime.date(2025, 2, 8)]
        >>> parse_compensatory_working_days("四、劳动节：5月1日（周四）至5日（周一）放假调休，共5天。4月27日（周日）上班。", "2025")
        [datetime.date(2025, 4, 27)]
        >>> parse_compensatory_working_days("六、国庆节、中秋节：10月1日（周三）至8日（周三）放假调休，共8天。9月28日（周日）、10月11日（周六）上班。", "2025")
        [datetime.date(2025, 9, 28), datetime.date(2025, 10, 11)]
    """
    comp_working_days = []
    for match in COMP_WORKING_DAY_PATTERN.findall(line):
        d = match[0] if len(match[1]) else f"{default_year}年{match[0]}"
        comp_working_day = str_to_date(d)
        if comp_working_day.weekday() >= 5:  # Only include weekends
            comp_working_days.append(comp_working_day)
    return list(OrderedDict.fromkeys(comp_working_days))


def parse_holidays_comp_working_days(content: str) -> dict[str, list[str]]:
    """Parse a complete Chinese holiday announcement text for holidays and compensatory working days.

    Args:
        content: Full text of a Chinese holiday announcement.

    Returns:
        dict: Dictionary containing:
            - 'holidays': List of holiday dates as 'YYYY-MM-DD' strings
            - 'compensatory_working_days': List of compensatory working dates as 'YYYY-MM-DD' strings
    """
    schedule = {"holidays": [], "compensatory_working_days": []}
    # Extract year from first matching line
    year_match = YEAR_PATTERN.search(content)
    if not year_match:
        raise ValueError("Unable to find YEAR pattern in holiday announcement.")
    default_year = year_match.group(1)

    # Process holidays
    for holiday_match in HOLIDAY_PATTERN.finditer(content, pos=year_match.end() + 1):
        schedule["holidays"].extend(
            map(
                lambda d: d.isoformat(),
                parse_holidays(holiday_match.group(), default_year),
            )
        )

    # Process compensatory days
    for comp_match in HAS_COMP_WORKING_PATTERN.finditer(
        content, pos=year_match.end() + 1
    ):
        comp_days = parse_compensatory_working_days(comp_match.group(1), default_year)
        schedule["compensatory_working_days"].extend(
            map(lambda d: d.isoformat(), comp_days)
        )

    return schedule
