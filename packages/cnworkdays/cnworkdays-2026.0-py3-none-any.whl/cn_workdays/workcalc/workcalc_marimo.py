import marimo

__generated_with = "0.10.5"
app = marimo.App(width="medium", app_title="Working Day Calculator")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # Working Day Calculator

        Calculate precise dates by adding or subtracting specific working days in China, taking into account holidays and compensatory working days.
        """
    )
    return


@app.cell
def load(mo):
    start_date = mo.ui.date()
    operation = mo.ui.dropdown(options={"Add": 1, "Subtract": -1}, value="Add")
    num_days = mo.ui.text(value="0")
    return num_days, operation, start_date


@app.cell
def calculate(calculate_working_date, user_input):
    try:
        result = calculate_working_date(
            user_input.value["start_date"],
            int(user_input.value["num_days"]) * user_input.value["operation"],
        )
    except Exception as e:
        result = f"Error: {e}"
    return (result,)


@app.cell
def user_input(mo, num_days, operation, start_date):
    user_input = mo.md(
        """
        | Start Date | Operation | Number of Working Days |
        | ---- | ------ | ------------ |
        |{start_date}|{operation}|{num_days}|
        """
    ).batch(
        start_date=start_date,
        operation=operation,
        num_days=num_days,
    )
    return (user_input,)


@app.cell
def response_str(date, mo, result):
    resp = mo.md(
        f"""
    | Result   |
    |----------|
    | {result.strftime("%Y-%m-%d, %A") if isinstance(result, date) else result} |
    """
    )
    return (resp,)


@app.cell
def result(mo, resp, user_input):
    mo.hstack([user_input, resp], justify="center", gap=3)
    return


@app.cell
def _():
    from cn_workdays import calculate_working_date
    from datetime import date
    return calculate_working_date, date


if __name__ == "__main__":
    app.run()
