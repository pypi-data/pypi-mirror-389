# cnworkdays

`cnworkdays` is Python tool that calculates working days in China by considering both public holidays and compensatory working days. It enables you to efficiently manage schedules around Chinese holidays.

`cnworkdays` provides three interfaces:

- <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 -4 48 48"><g fill="none"><path stroke="#000" stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M25 40H7C5.34315 40 4 38.6569 4 37V11C4 9.34315 5.34315 8 7 8H41C42.6569 8 44 9.34315 44 11V24.9412"/><path fill="#2f88ff" stroke="#000" stroke-width="4" d="M4 11C4 9.34315 5.34315 8 7 8H41C42.6569 8 44 9.34315 44 11V20H4V11Z"/><path stroke="#000" stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M32 35H44"/><path stroke="#000" stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M38 29V41"/><circle r="2" fill="#fff" transform="matrix(0 -1 -1 0 10 14)"/><circle r="2" fill="#fff" transform="matrix(0 -1 -1 0 16 14)"/></g></svg> **Web interface**: access a web application powered by [marimo](https://marimo.io).
- <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 -4 24 24"><path fill="currentColor" d="M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16c1.1 0 2-.9 2-2V6a2 2 0 0 0-2-2m0 14H4V8h16zm-2-1h-6v-2h6zM7.5 17l-1.41-1.41L8.67 13l-2.59-2.59L7.5 9l4 4z"/></svg> **Terminal interface**: use a command-line interface built with [Textual](https://textual.textualize.io).
- <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 -1 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 22c-.818 0-1.6-.335-3.163-1.006C4.946 19.324 3 18.49 3 17.085V7.747M12 22c.818 0 1.6-.335 3.163-1.006C19.054 19.324 21 18.49 21 17.085V7.747M12 22v-9.83m9-4.422c0 .603-.802.984-2.405 1.747l-2.92 1.39C13.87 11.741 12.97 12.17 12 12.17m9-4.423c0-.604-.802-.985-2.405-1.748M3 7.747c0 .604.802.986 2.405 1.748l2.92 1.39c1.804.857 2.705 1.286 3.675 1.286M3 7.748c0-.604.802-.985 2.405-1.748m.927 7.311l1.994.948M12 2v2m4-1l-1.5 2M8 3l1.5 2" color="currentColor"/></svg> **Python API**: integrate `cnworkdays` directly into your Python projects.

## Installation

To avoid conflicts with your existing Python environment, install `cnworkdays` using [pipx](https://github.com/pypa/pipx#install-pipx):

```shell
pipx install cnworkdays
```

## Getting Started

1. Run the `cnworkdays` command:

    ```shell
    cnworkdays
    ```

2. Choose an application:

    - `holiparse`: parses official holiday announcements. For more information, see [Holiday Announcement Parser](#holiday-announcement-parser).
    - `workcalc`: calculates working days. For more information, see [Working Day Calculator](#working-day-calculator).

3. Select an interface (for `workcalc`):

    - Web interface (default)
    - Terminal interface

4. Configure connection settings (for the web interface):

    - Host address (default: `127.0.0.1`)
    - Port number (default: `8080`)

## Holiday Announcement Parser

The `holiparse` application extracts structured data from official State Council announcements, including:

- Annual public holidays
- Compensatory working days

### Use the web interface

To launch the web application for parsing holiday announcements:

```shell
cnworkdays holiparse web
```

To specify a custom host and port, use the `--host` and `--port` flags:

```shell
cnworkdays holiparse web --host 0.0.0.0 --port 9000
```

## Working Day Calculator

The `workcalc` application calculates dates before or after a specified number of working days, taking into account:

- Official public holidays
- Compensatory working days

### Use the web interface

To launch the web application for calculating working days:

```shell
cnworkdays workcalc web
```

To specify a custom host and port, use the `--host` and `--port` flags:

```shell
cnworkdays workcalc web --host 0.0.0.0 --port 9000
```

### Use the terminal interface

To launch the terminal interface for calculating working days:

1. Run the following command:

    ```shell
    # Terminal interface
    cnworkdays workcalc terminal
    ```

2. Enter the required information:

     - **Start Date**: enter the start date in the "YYYY-MM-DD" format.
     - Select **Subtract** or **Add**.
     - **Working Days**: enter the number of working days.
     - **Result**: the result date will be displayed.

3. To save the current calculation record, click Save. The record will appear in the table.

Keyboard shortcuts:

- `Ctrl + q`: quit
- `d`: toggle dark mode
- `s`: save to history
- `r`: remove a record
- `c`: clear all history

![Usage example](workcalc_terminal.png)

### Use the Python API

You can programmatically calculate working days using the `cnworkdays.calculate_working_date()` function.

#### Example usage

```python
from datetime import date
from cnworkdays import calculate_working_date

# Calculate using a string date (YYYYMMDD format)
target_working_date = calculate_working_date("20240607", 1)  # Returns: 2024-06-11

# Calculate using a string date (YYYY-MM-DD format)
target_working_date = calculate_working_date("2024-06-08", 0)  # Returns: 2024-06-11

# Calculate using a date object
start_date = date(2024, 5, 13)
target_working_date = calculate_working_date(start_date, -1)  # Returns: 2024-05-11
```

#### API reference

`calculate_working_date(start_date, num_days)`

**Parameters**

- `start_date` (Union[str, datetime, date]): the reference date for calculations.
- `num_days` (int): the number of working days to calculate.
    - Positive values add working days.
    - Negative values subtract working days.
    - Zero returns the next working day if `start_date` is non-working.

**Returns**

- `date`: the calculated date, considering working days, holidays, and compensatory working days.

**Exceptions**

- `ValueError`: for invalid start dates or calculated dates outside the valid range.

## Changelog

### [2025.1] - 2024-12-22

- Introduce a [terminal interface](#use-the-terminal-interface) for `cnworkdays workcalc`, built with Textual.
- Add a Python API with the [`cnworkdays.calculate_working_date()`](#use-the-python-api) function.
- Improve error handling for invalid inputs.

### [2025.0] - 2024-11-25

- Extend date calculation support for `cnworkdays workcalc` through December 31, 2025.
- Fix the issue that `cnworkdays holiparse` fails to parse CY25 announcement.

### [2024.1] - 2024-11-25

- Enhance browser application with more descriptive page titles for better user experience.
- Fix the issue that `workcalc` gets stuck when negative days are provided.

### [2024.0] - 2024-11-13

- Launch `cnworkdays` CLI with two main commands:

  - `holiparse`: generate data for annual public holidays and compensatory working days based on notifications from the General Office of the State Council.
  - `workcalc`: calculate the date after or before a specified number of working days, accounting for official public holidays and compensatory working days in China.

- Add support for date calculations spanning from January 1, 2018, to December 31, 2024.
