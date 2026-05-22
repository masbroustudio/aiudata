"""
Programmatic Chart.js configuration builder.
Generates chart configs without requiring an LLM call — faster and more reliable.
"""
import json
from typing import Any

from dataline.services.llm_flow.llm_calls.chart_generator import ChartType


# Color palettes for charts
CHART_COLORS = [
    "rgba(54, 162, 235, 0.7)",   # blue
    "rgba(255, 99, 132, 0.7)",   # red
    "rgba(75, 192, 192, 0.7)",   # teal
    "rgba(255, 205, 86, 0.7)",   # yellow
    "rgba(153, 102, 255, 0.7)",  # purple
    "rgba(255, 159, 64, 0.7)",   # orange
    "rgba(201, 203, 207, 0.7)",  # grey
    "rgba(46, 204, 113, 0.7)",   # green
    "rgba(142, 68, 173, 0.7)",   # dark purple
    "rgba(52, 73, 94, 0.7)",     # dark blue
]

CHART_BORDER_COLORS = [
    "rgba(54, 162, 235, 1)",
    "rgba(255, 99, 132, 1)",
    "rgba(75, 192, 192, 1)",
    "rgba(255, 205, 86, 1)",
    "rgba(153, 102, 255, 1)",
    "rgba(255, 159, 64, 1)",
    "rgba(201, 203, 207, 1)",
    "rgba(46, 204, 113, 1)",
    "rgba(142, 68, 173, 1)",
    "rgba(52, 73, 94, 1)",
]


def build_chart_config(
    chart_type: ChartType,
    labels: list[Any],
    values: list[Any],
    title: str = "Chart",
) -> str:
    """
    Build a Chart.js configuration programmatically.
    No LLM call needed — deterministic and fast.
    """
    num_items = len(labels)
    bg_colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(num_items)]
    border_colors = [CHART_BORDER_COLORS[i % len(CHART_BORDER_COLORS)] for i in range(num_items)]

    if chart_type == ChartType.bar:
        config = _build_bar_config(labels, values, title, bg_colors, border_colors)
    elif chart_type == ChartType.line:
        config = _build_line_config(labels, values, title)
    elif chart_type == ChartType.doughnut:
        config = _build_doughnut_config(labels, values, title, bg_colors)
    elif chart_type == ChartType.scatter:
        config = _build_scatter_config(labels, values, title)
    else:
        config = _build_bar_config(labels, values, title, bg_colors, border_colors)

    return json.dumps(config)


def _build_bar_config(
    labels: list, values: list, title: str, bg_colors: list, border_colors: list
) -> dict:
    return {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{
                "data": values,
                "backgroundColor": bg_colors,
                "borderColor": border_colors,
                "borderWidth": 1,
            }],
        },
        "options": {
            "plugins": {
                "legend": {"display": False},
                "title": {"display": True, "text": title},
            },
            "scales": {
                "y": {"beginAtZero": True},
            },
        },
    }


def _build_line_config(labels: list, values: list, title: str) -> dict:
    return {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": [{
                "data": values,
                "fill": False,
                "borderColor": "rgba(54, 162, 235, 1)",
                "backgroundColor": "rgba(54, 162, 235, 0.2)",
                "tension": 0.1,
            }],
        },
        "options": {
            "plugins": {
                "legend": {"display": False},
                "title": {"display": True, "text": title},
            },
            "scales": {
                "x": {"beginAtZero": True},
                "y": {"beginAtZero": True},
            },
        },
    }


def _build_doughnut_config(labels: list, values: list, title: str, bg_colors: list) -> dict:
    return {
        "type": "doughnut",
        "data": {
            "labels": labels,
            "datasets": [{
                "data": values,
                "backgroundColor": bg_colors,
                "hoverOffset": 4,
            }],
        },
        "options": {
            "plugins": {
                "legend": {"display": True},
                "title": {"display": True, "text": title},
            },
        },
    }


def _build_scatter_config(labels: list, values: list, title: str) -> dict:
    # For scatter, labels are X values and values are Y values
    data_points = [{"x": x, "y": y} for x, y in zip(labels, values)]
    return {
        "type": "scatter",
        "data": {
            "datasets": [{
                "label": title,
                "data": data_points,
                "backgroundColor": "rgba(54, 162, 235, 0.7)",
            }],
        },
        "options": {
            "plugins": {
                "title": {"display": True, "text": title},
            },
            "scales": {
                "x": {"type": "linear", "position": "bottom"},
                "y": {"type": "linear", "position": "left"},
            },
        },
    }
