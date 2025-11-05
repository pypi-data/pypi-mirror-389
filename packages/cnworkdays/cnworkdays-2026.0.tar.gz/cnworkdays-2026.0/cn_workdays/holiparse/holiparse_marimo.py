import marimo

__generated_with = "0.10.5"
app = marimo.App(width="medium", app_title="Holiday Announcement Parser")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # Holiday Announcement Parser


              The Holiday Announcement Parser is a powerful tool designed to streamline your holiday scheduling process. By simply entering the holiday scheduler text, this app accurately extracts all the holidays and compensatory working days, providing a clear and organized schedule.
        """
    )
    return


@app.cell
def _(mo):
    schedule = mo.ui.text_area(
        label="Enter the annual public holiday schedule for China. You can find the announcement [here](https://sousuo.www.gov.cn/sousuo/search.shtml?code=17da70961a7&searchWord=%E8%8A%82%E5%81%87%E6%97%A5%E5%AE%89%E6%8E%92%E9%80%9A%E7%9F%A5&dataTypeId=107&sign=09a72b8e-f442-48a2-e623-8ee48bd363d8).",
        placeholder="国务院办公厅关于xxxx年",
        full_width=True,
        rows=10,
    )
    schedule
    return (schedule,)


@app.cell
def _(mo, schedule_download, schedule_table):
    mo.vstack(
        [
            schedule_download,
            schedule_table,
        ],
    )
    return


@app.cell
def _(dict_table, json, mo, parse_holidays_comp_working_days, schedule):
    mo.stop(len(schedule.value) == 0)

    try:
        schedule_obj = parse_holidays_comp_working_days(
            schedule.value,
        )
    except ValueError:
        mo.stop(
            True,
            mo.callout(
                value=mo.md("""#### Invalid Holiday Schedule Format
                The holiday announcement you entered couldn't be processed.
                """),
                kind="alert",
            ),
        )
    except Exception as e:
        mo.stop(
            True,
            mo.callout(
                value=mo.md(f"""#### Unable to Process Holiday Schedule
                Details: {e}
                """),
                kind="alert",
            ),
        )

    schedule_table = mo.ui.table(
        data=dict_table(schedule_obj), pagination=True, page_size=20
    )

    schedule_download = mo.download(
        data=json.dumps(schedule_obj, indent=2),
        filename="schedule.json",
        label="Download the schedule in JSON format",
    )
    return schedule_download, schedule_obj, schedule_table


@app.cell
def _():
    import json
    from cn_workdays.holiparse.parser import parse_holidays_comp_working_days
    return json, parse_holidays_comp_working_days


@app.cell
def _():
    def dict_table(obj: dict) -> list:
        max_length = max(len(v) for v in obj.values())

        result = []
        for i in range(max_length):
            new_dict = {}
            for key, value_list in obj.items():
                if i < len(value_list):
                    new_dict[key] = value_list[i]
            if new_dict:  # Only add non-empty dictionaries
                result.append(new_dict)
        return result
    return (dict_table,)


if __name__ == "__main__":
    app.run()
