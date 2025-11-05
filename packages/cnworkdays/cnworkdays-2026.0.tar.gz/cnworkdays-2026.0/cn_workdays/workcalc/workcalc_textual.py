from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, ClassVar

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import Resize
from textual.message import Message
from textual.reactive import reactive
from textual.validation import Number, ValidationResult, Validator
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
    Switch,
)

from cn_workdays import calculate_working_date
from cn_workdays.__version__ import __version__


@dataclass
class CalculationRecord:
    """Data class for calculation records."""

    start_date: str
    days: int
    target_date: date

    @property
    def operation(self) -> str:
        """Return the operation symbol based on days value."""
        return "+" if self.days >= 0 else "-"

    @property
    def formatted_target_date(self) -> str:
        """Return formatted target date string."""
        return self.target_date.strftime("%Y-%m-%d")


class DateValidator(Validator):
    """Validator for date input in YYYY-MM-DD format."""

    DATE_FORMAT: ClassVar[str] = "%Y-%m-%d"

    def validate(self, value: str) -> ValidationResult:
        """Validate date string format."""
        if not value:
            return self.success()
        try:
            datetime.strptime(value, self.DATE_FORMAT)
            return self.success()
        except ValueError:
            return self.failure(f"Please enter date in {self.DATE_FORMAT} format")


class HistoryTable(DataTable):
    """Table to display calculation history."""

    class RecordAdded(Message):
        """Message emitted when a new record is added."""

        def __init__(self, record: CalculationRecord) -> None:
            super().__init__()
            self.record = record

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cursor_type = "row"
        self._id_counter = 1  # Initialize counter for row IDs

    def on_mount(self) -> None:
        """Initialize table columns."""
        self.add_columns("ID", "Start Date", "Operation", "Days", "Target Date")

    def add_record(self, record: CalculationRecord) -> None:
        """Add a new calculation record to the table."""
        row_id = str(self._id_counter)
        self.add_row(
            row_id,
            record.start_date,
            record.operation,
            abs(record.days),
            record.formatted_target_date,
            key=row_id,
        )
        self._id_counter += 1

    def clear_history(self) -> None:
        """Clear all history and reset counter."""
        self.clear()
        self._id_counter = 1


class CalculatorArea(Static):
    """Calculator widget handling the main calculation logic."""

    start_date: reactive[str] = reactive("")
    days: reactive[int] = reactive(-1)
    is_add: reactive[bool] = reactive(False)
    result: reactive[Optional[CalculationRecord]] = reactive(None)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Horizontal(classes="input-container"):
            # Date input group
            with Vertical(classes="input-group"):
                yield Label("Start Date", classes="input-label")
                yield Input(
                    placeholder="YYYY-MM-DD",
                    id="start_date",
                    validators=[DateValidator()],
                    max_length=10,
                )

            # Direction switch group
            with Vertical(classes="input-group-switch"):
                with Horizontal(classes="labeled-switch"):
                    yield Label("Subtract", classes="switch-label")
                    yield Switch(id="direction", animate=False)
                    yield Label("  Add   ", classes="switch-label")

            # Days input group
            with Vertical(classes="input-group"):
                yield Label("Working Days", classes="input-label")
                yield Input(
                    placeholder="Enter number of days",
                    id="num_days",
                    type="number",
                    validators=[Number(minimum=0)],
                )

            with Vertical(classes="result-container"):
                yield Label(
                    "Result", id="result-label", classes="result-container-label"
                )
                yield Horizontal(
                    Input(id="result_date", classes="result-value", disabled=True),
                    Button(
                        "Save",
                        id="save_history",
                        variant="primary",
                        classes="button-container",
                    ),
                )

    def watch_result(self) -> None:
        """Update result display when result.result_date changes."""
        if self.result and self.result.formatted_target_date:
            self.query_one("#result_date").value = self.result.formatted_target_date
            self.app.query_one("#save_history", Button).disabled = False
        else:
            self.query_one("#result_date").value = "No calculation yet"
            self.app.query_one("#save_history", Button).disabled = True

    def _calculate(self) -> None:
        """Perform the calculation if inputs are valid."""
        if not (self.start_date and self.days >= 0):
            return

        try:
            days_to_add = self.days if self.is_add else -1 * self.days
            target_date = calculate_working_date(self.start_date, days_to_add)
            self.result = CalculationRecord(self.start_date, days_to_add, target_date)
            result_input = self.query_one("#result_date")
            result_input.styles.outline = None
            result_input._tooltip = None
        except ValueError as e:
            result_input = self.query_one("#result_date")
            result_input.value = "Invalid result"
            result_input.styles.outline = ("round", "red")
            result_input._tooltip = str(e)
            self.app.notify(str(e), severity="error")

    def save_current_result(self) -> None:
        """Save the current result to history."""
        if self.result:
            self.app.query_one(HistoryTable).add_record(self.result)

    @on(Input.Changed, "#start_date")
    def on_start_date_changed(self, event: Input.Changed) -> None:
        """Handle start date input changes."""
        self.start_date = event.value if event.input.is_valid else ""
        self._calculate()

    @on(Input.Changed, "#num_days")
    def on_days_changed(self, event: Input.Changed) -> None:
        """Handle days input changes."""
        self.days = int(event.value) if event.input.is_valid else -1
        self._calculate()

    @on(Switch.Changed, "#direction")
    def on_direction_changed(self, event: Switch.Changed) -> None:
        """Handle direction switch changes."""
        self.is_add = event.value
        self._calculate()

    @on(Button.Pressed, "#save_history")
    def on_save_pressed(self) -> None:
        """Handle save button press."""
        self.app.query_one(CalculatorArea).save_current_result()

    @on(Resize)
    def on_resize(self) -> None:
        """Handle terminal resize events."""
        input_container = self.query_one(".input-container")
        # Changed threshold to match min-width in CSS
        if self.size.width < 100:  # Adjusted threshold for better responsiveness
            input_container.add_class("narrow")
            self.styles.height = 16
        else:
            input_container.remove_class("narrow")
            self.styles.height = 8


class WorkDayCalApp(App):
    """Working Day Calculator Application."""

    TITLE = "Working Day Calculator"
    SUB_TITLE = __version__
    CSS_PATH = "calculator.tcss"

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("s", "save_history", "Save to history"),
        ("r", "remove_record", "Remove a record"),
        ("c", "clear_history", "Clear history"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield CalculatorArea()
        yield HistoryTable(classes="history-table")
        yield Footer()

    def on_history_table_calculation_record(
        self, message: HistoryTable.RecordAdded
    ) -> None:
        """Handle saving to history."""
        history_table = self.query_one(HistoryTable)
        history_table.add_record(message)

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def action_save_history(self) -> None:
        """Save current calculation to history."""
        calculator_area = self.app.query_one(CalculatorArea)
        if calculator_area.result:
            self.app.query_one("#save_history").press()

    def action_remove_record(self) -> None:
        """Remove selected record from history."""
        history_table = self.query_one(HistoryTable)
        row_index = history_table.cursor_row

        if row_index is None or not history_table.is_valid_row_index(row_index):
            self.notify("Please select a record to remove", severity="warning")
            return

        try:
            row_key = history_table.get_row_at(row_index)[0]
            history_table.remove_row(row_key)
        except Exception as e:
            self.notify(f"Failed to remove record: {str(e)}", severity="error")

    def action_clear_history(self) -> None:
        """Clear all history records."""
        self.query_one(HistoryTable).clear_history()
        self.notify("History cleared", severity="information")
