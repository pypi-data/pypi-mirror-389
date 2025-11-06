# Copyright 2025 Cotality
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

import pandas as pd
import panel as pn
import plotly.graph_objects as go

from ....core.locales import keys
from ....core.utils.misc import int_to_datetime_string
from ....xapi.clip.typing import (
    INPUT_TABLE_NAME,
    LAST_CLIP_RUN_DATE,
    LAST_CLIP_RUN_RECORDS,
    LAST_CLIP_RUN_STATUS,
    TOTAL_CLIP_RECORDS,
    TOTAL_DUPLICATE_RECORDS,
    TOTAL_INVALID_RECORDS,
    TOTAL_RECORDS,
    TOTAL_UNIQUE_RECORDS,
    TOTAL_UNMATCHED_RECORDS,
)
from ...base.base_app import BaseApp
from .input import display as display_create_input_table


def display(app: BaseApp):
    """Select the input table for the Clip Lookup Panel app.
    Args:
        platform (Platform): The platform instance.
    """

    tables = app.clip_client.get_clip_input_tables()

    if len(tables) == 0:
        return display_create_input_table(
            app, keys.TEXT_NO_INPUT_TABLES_CREATED, keys.TEXT_ADD_INPUT_TABLE_INTRO
        )
    else:
        return __display_dashboard(app)


def __display_dashboard(app: BaseApp):
    input_table = ""

    main_title = pn.pane.Markdown(
        f"# {app._(keys.TEXT_DASHBOARD)}", sizing_mode="stretch_width"
    )

    reset_btn = pn.widgets.Button(
        name=app._(keys.TEXT_DASHBOARD_START),
        button_type="primary",
    )

    run_job_section = pn.Row(
        sizing_mode="stretch_width", css_classes=["run-job-section"]
    )
    jobs_section = pn.Column(sizing_mode="stretch_width")
    main_section = pn.Column(sizing_mode="stretch_width")

    # if user want to reset dashboard
    def _reset_dashboard(event):
        nonlocal input_table

        app.toggle_loading()

        main_title.object = f"# {app._(keys.TEXT_DASHBOARD)}"
        main_section.objects = [__display_summary_tables(app, _on_select_row)]
        run_job_section.objects = []
        input_table = ""

        app.toggle_loading()

    # if user want to run job for a table
    def _click_run_job(event):
        main_section.objects = [run_job_view(app, input_table, _reset_dashboard)]

    # if user selected a row
    def _on_select_row(row):
        """On select row from table"""
        nonlocal input_table

        if row is None:
            run_job_section.objects = []
            main_title.object = f"# {app._(keys.TEXT_DASHBOARD)}"
            jobs_section.objects = []
            input_table = ""
            return

        app.toggle_loading()

        name = row[app._(keys.COLUMN_INPUT_TABLE_NAME)]
        input_table = str(name)
        main_title.object = f"# {app._(keys.TEXT_DASHBOARD)} - " + input_table
        jobs_section.objects = [__display_summary(app, input_table)]

        run_job_btn = pn.widgets.Button(
            name=app._(keys.BUTTON_RUN_JOB), button_type="primary"
        )

        run_job_section.objects = [run_job_btn]
        run_job_btn.on_click(_click_run_job)

        app.toggle_loading()

    # load data
    app.toggle_loading()
    main_section.objects = [
        __display_summary_tables(app, _on_select_row),
        jobs_section,
    ]
    app.toggle_loading()

    reset_btn.on_click(_reset_dashboard)

    return pn.Column(
        main_title,
        pn.Row(
            reset_btn,
            run_job_section,
            sizing_mode="stretch_width",
        ),
        main_section,
        sizing_mode="stretch_width",
    )


def run_job_view(app: BaseApp, input_table: str, _reset_dashboard) -> pn.Column:

    main_title = pn.pane.Markdown(
        f"# {app._(keys.BUTTON_RUN_JOB_DIALOG)}", sizing_mode="stretch_width"
    )

    subtitle = pn.pane.Markdown(app._(keys.TEXT_CLIP_INFO), sizing_mode="stretch_width")

    run_job_btn = pn.widgets.Button(
        name=app._(keys.BUTTON_RUN_JOB_DIALOG),
        button_type="primary",
    )

    info = pn.pane.Markdown("", sizing_mode="stretch_width")

    def _click_run_job(event):
        info.object = f"## {app._(keys.TEXT_OPERATION_IN_PROGRESS)}"
        app.toggle_loading()

        try:
            app.clip_client.clip(input_table=input_table)
            info.object = ""
        except Exception:
            info.object = f"# {app._(keys.SYS_ERROR_CLIP_LOOKUP)}"
        finally:
            app.toggle_loading()
            _reset_dashboard(None)

    run_job_btn.on_click(_click_run_job)

    return pn.Column(
        main_title,
        subtitle,
        run_job_btn,
        info,
        sizing_mode="stretch_width",
        css_classes=["center-wrapper"],
    )


def __display_summary_tables(app: BaseApp, _on_select_row):

    try:
        summary_df = app.clip_client.get_input_tables_summary()
    except Exception:
        return pn.pane.Markdown(
            app._(keys.SYS_ERROR_GET_SUMMARY), sizing_mode="stretch_width"
        )

    column_config = {
        INPUT_TABLE_NAME: app._(keys.COLUMN_INPUT_TABLE_NAME),
        TOTAL_RECORDS: app._(keys.COLUMN_TOTAL_RECORDS),
        TOTAL_CLIP_RECORDS: app._(keys.COLUMN_TOTAL_CLIP_RECORDS),
        TOTAL_UNMATCHED_RECORDS: app._(keys.COLUMN_TOTAL_UNMATCHED_RECORDS),
        TOTAL_INVALID_RECORDS: app._(keys.COLUMN_TOTAL_INVALID_RECORDS),
        TOTAL_UNIQUE_RECORDS: app._(keys.COLUMN_TOTAL_UNIQUE_RECORDS),
        TOTAL_DUPLICATE_RECORDS: app._(keys.COLUMN_TOTAL_DUPLICATE_RECORDS),
        LAST_CLIP_RUN_STATUS: app._(keys.COLUMN_INPUT_TABLE_STATUS),
        LAST_CLIP_RUN_RECORDS: app._(keys.COLUMN_INPUT_TABLE_RECORDS),
        LAST_CLIP_RUN_DATE: app._(keys.COLUMN_INPUT_TABLE_LAST_RUN),
    }

    available_cols = [col for col in column_config.keys() if col in summary_df.columns]
    summary_df = summary_df[available_cols]
    summary_df = summary_df.rename(columns=column_config)

    table = pn.widgets.Tabulator(
        summary_df,
        disabled=False,
        selectable="checkbox",
        show_index=False,
        sizing_mode="stretch_width",
        layout="fit_columns",
        theme="modern",
        configuration={
            "rowHeight": 35,
            "headerSort": False,
        },
        editors={col: None for col in summary_df.columns},
        css_classes=["dashboard-table"],
    )

    last_selection = []

    def update_selection(event):
        """
        Callback when selection changes - enforces single selection
        """
        nonlocal last_selection, _on_select_row

        selection = event.new
        if (
            selection
            and len(selection) > 0
            and (len(selection) > 1 or selection != last_selection)
        ):
            new_selection = [selection[-1]]
            table.selection = new_selection
            last_selection = new_selection

            row_data = summary_df.iloc[selection[-1]]
            _on_select_row(row_data)
        else:
            last_selection = []
            _on_select_row(None)

    table.param.watch(update_selection, "selection")

    return table


def __display_summary(app: BaseApp, input_table: str) -> pn.Column:

    jobs = []
    try:
        jobs = app.clip_client.get_input_jobs_list(input_table)
    except Exception:
        return pn.pane.Markdown(
            app._(keys.SYS_ERROR_GET_JOBS), sizing_mode="stretch_width"
        )

    options = [int_to_datetime_string(j.started_at) for j, _ in jobs]

    if len(options) == 0:
        return pn.Column()

    select = pn.widgets.Select(
        name=app._(keys.SELECT_JOB_LABEL), options=options, value=options[0]
    )

    @pn.depends(select)
    def selection_summary(selected: str) -> pn.Column:
        nonlocal jobs

        if len(jobs) == 0:
            return pn.Column("")

        clip_metric = [
            m for j, m in jobs if int_to_datetime_string(j.started_at) == selected
        ][0]
        scores_dict = clip_metric.clip_summary_metric.property_match_score

        scores = [
            {"score": int(float(score if score != "NaN" else 0)), "count": count}
            for score, count in scores_dict.items()
        ]

        total_count = sum(item["count"] for item in scores)
        if total_count > 0:
            weighted_sum = sum(item["score"] * item["count"] for item in scores)
            percentage = round(weighted_sum / total_count, 2)
        else:
            percentage = 0

        labels = ["Matched", "Unmatched"]
        values = [percentage, 10 - percentage]
        colors = ["blue", "gray"]

        fig_pie = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.5,
                    marker={"colors": colors},
                    textinfo="none",
                )
            ]
        )

        fig_pie.add_annotation(
            text=f"{round(percentage*10, 2)}%",
            x=0.5,
            y=0.5,
            font=dict(size=20, color="black"),
            showarrow=False,
            xanchor="center",
            yanchor="middle",
        )

        fig_pie.update_layout(
            margin=dict(t=20, b=40, l=10, r=10),
            legend=dict(
                x=0.5,
                y=-0.15,
                xanchor="center",
                yanchor="top",
                orientation="h",
                bgcolor="rgba(0,0,0,0)",
            ),
            height=300,
        )

        total_count = clip_metric.input_metrics.total_input_counts
        matched_count = clip_metric.input_metrics.clip_counts
        unmatched_count = clip_metric.input_metrics.non_clip_counts
        invalid_count = clip_metric.input_metrics.invalid_counts

        total_label = "record" if total_count == 1 else "records"
        matched_label = "record" if matched_count == 1 else "records"
        unmatched_label = "record" if unmatched_count == 1 else "records"
        invalid_label = "record" if invalid_count == 1 else "records"

        metrics_panel = pn.pane.HTML(
            f"""
        <div style="display: flex; height: 340px; align-items: center; justify-content: center;">
            <div style="width: 100%;">
                <ul style="list-style-type: none; padding-left: 0; margin: 0; text-align: left;">
                    <li><strong>{app._(keys.CLIP_JOB_METRICS)}</strong></li>
                    <li><strong>{app._(keys.TEXT_TOTAL_JOB_RECORDS)}:</strong> {total_count} {total_label}</li>
                    <li><strong>{app._(keys.TEXT_MATCHED)}:</strong> {matched_count} {matched_label}</li>
                    <li><strong>{app._(keys.TEXT_UNMATCHED)}:</strong> {unmatched_count} {unmatched_label}</li>
                    <li><strong>{app._(keys.TEXT_INVALID)}:</strong> {invalid_count} {invalid_label}</li>
                </ul>
            </div>
        </div>
        """,
            sizing_mode="stretch_width",
        )

        return pn.Column(
            pn.Row(
                pn.Column(
                    app._(keys.TEXT_PIE_DESCRIPTION),
                    pn.pane.Plotly(fig_pie, config={"displayModeBar": False}),
                ),
                metrics_panel,
                sizing_mode="stretch_width",
            ),
            get_graphs(app, scores),
        )

    return pn.Column(
        select,
        selection_summary,
        sizing_mode="stretch_width",
    )


def plot_horizontal_bar(value, category, text: str):
    """
    Plots a horizontal bar chart with a single value and a category.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=[value],
            y=[category],
            orientation="h",
            marker={"color": "blue"},
            name="Percentage",
        )
    )
    fig.add_trace(
        go.Bar(
            x=[100 - value],
            y=[category],
            orientation="h",
            marker={"color": "gray"},
            name="Remaining",
        ),
    )

    fig.update_layout(
        barmode="stack",
        showlegend=False,
        xaxis={"showticklabels": False, "showgrid": False, "zeroline": False},
        yaxis={"showticklabels": False, "showgrid": False, "zeroline": False},
        margin={"t": 0, "b": 0, "l": 0, "r": 0},
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=40,
    )

    fig.add_annotation(
        x=0,
        y=category,
        text=text,
        showarrow=False,
        font={"size": 12, "color": "black"},
        align="left",
        xanchor="left",
        yanchor="bottom",
        yshift=-30,
    )

    return fig


def get_graphs(app: BaseApp, scores: list[dict[str, int]]) -> pn.Column:
    """
    Generates the Figure of 4 graphs using Plotly.
    """

    def _percent(count: int, total: int):
        "Percentage without exeception"
        return (count / total) * 100 if total != 0 else 0

    records_8_10_count = sum(
        item["count"] for item in scores if 8 <= item["score"] <= 10
    )
    records_6_7_count = sum(item["count"] for item in scores if 6 <= item["score"] <= 7)
    records_1_5_count = sum(item["count"] for item in scores if 1 <= item["score"] <= 5)
    records_0_count = sum(item["count"] for item in scores if item["score"] == 0)

    records_8_10_percent_sum = (
        records_8_10_count + records_6_7_count + records_1_5_count + records_0_count
    )
    records_8_10_percent = _percent(records_8_10_count, records_8_10_percent_sum)
    records_6_7_percent_sum = (
        records_8_10_count + records_6_7_count + records_1_5_count + records_0_count
    )
    records_6_7_percent = _percent(records_6_7_count, records_6_7_percent_sum)
    records_1_5_percent_sum = (
        records_8_10_count + records_6_7_count + records_1_5_count + records_0_count
    )
    records_1_5_percent = _percent(records_1_5_count, records_1_5_percent_sum)
    records_0_percent_sum = (
        records_8_10_count + records_6_7_count + records_1_5_count + records_0_count
    )
    records_0_percent = _percent(records_0_count, records_0_percent_sum)

    # Top graph
    category0 = app._(keys.TEXT_EXACT_MATCH)
    chart0 = plot_horizontal_bar(
        records_8_10_percent,
        category0,
        app._(keys.TEXT_EXACT_MATCH_DESCRIPTION).format(count=records_8_10_count),
    )
    pct0 = f"{round(records_8_10_percent, 2)}%"
    chart0.update_layout(margin={"t": 0, "b": 0, "l": 80, "r": 0})
    chart0.add_annotation(
        x=0,
        xref="paper",
        xanchor="right",
        xshift=-8,
        y=category0,
        yref="y",
        text=pct0,
        showarrow=False,
        yanchor="middle",
        font={"size": 13, "color": "black"},
    )

    # Second graph
    category1 = app._(keys.TEXT_MEDIUM_MATCH)
    chart1 = plot_horizontal_bar(
        records_6_7_percent,
        category1,
        app._(keys.TEXT_MEDIUM_MATCH_DESCRIPTION).format(count=records_6_7_count),
    )
    pct1 = f"{round(records_6_7_percent, 2)}%"
    chart1.update_layout(margin={"t": 0, "b": 0, "l": 80, "r": 0})
    chart1.add_annotation(
        x=0,
        xref="paper",
        xanchor="right",
        xshift=-8,
        y=category1,
        yref="y",
        text=pct1,
        showarrow=False,
        yanchor="middle",
        font={"size": 13, "color": "black"},
    )

    # Third graph
    category2 = app._(keys.TEXT_LOW_MATCH)
    chart2 = plot_horizontal_bar(
        records_1_5_percent,
        category2,
        app._(keys.TEXT_LOW_MATCH_DESCRIPTION).format(count=records_1_5_count),
    )
    pct2 = f"{round(records_1_5_percent, 2)}%"
    chart2.update_layout(margin={"t": 0, "b": 0, "l": 80, "r": 0})
    chart2.add_annotation(
        x=0,
        xref="paper",
        xanchor="right",
        xshift=-8,
        y=category2,
        yref="y",
        text=pct2,
        showarrow=False,
        yanchor="middle",
        font={"size": 13, "color": "black"},
    )

    # Bottom graph
    category3 = app._(keys.TEXT_NO_MATCH)
    chart3 = plot_horizontal_bar(
        records_0_percent,
        category3,
        app._(keys.TEXT_NO_MATCH_DESCRIPTION).format(count=records_0_count),
    )
    pct3 = f"{round(records_0_percent, 2)}%"
    chart3.update_layout(margin={"t": 0, "b": 0, "l": 80, "r": 0})
    chart3.add_annotation(
        x=0,
        xref="paper",
        xanchor="right",
        xshift=-8,
        y=category3,
        yref="y",
        text=pct3,
        showarrow=False,
        yanchor="middle",
        font={"size": 13, "color": "black"},
    )

    return pn.Column(chart0, chart1, chart2, chart3, sizing_mode="stretch_width")
