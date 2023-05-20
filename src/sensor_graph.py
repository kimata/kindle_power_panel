#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pathlib
import os
import datetime
import io
import matplotlib
import PIL.Image
import logging

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()
from matplotlib.font_manager import FontProperties

from sensor_data import fetch_data
from sensor_data import get_valve_on_range

IMAGE_DPI = 100.0


def get_plot_font(config, font_type, size):
    font_path = str(
        pathlib.Path(
            os.path.dirname(__file__), config["PATH"], config["MAP"][font_type]
        )
    )

    logging.info("Load font: {path}".format(path=font_path))

    return FontProperties(
        fname=font_path,
        size=size,
    )


def get_face_map(font_config):
    return {
        "title": get_plot_font(font_config, "JP_BOLD", 60),
        "value": get_plot_font(font_config, "EN_MEDIUM", 100),
        "value_small": get_plot_font(font_config, "EN_COND_BOLD", 80),
        "value_unit": get_plot_font(font_config, "EN_MEDIUM", 30),
        "xaxis_major": get_plot_font(font_config, "JP_REGULAR", 30),
        "xaxis_minor": get_plot_font(font_config, "EN_MEDIUM", 24),
        "yaxis": get_plot_font(font_config, "EN_MEDIUM", 16),
    }


def plot_item(
    ax,
    title,
    unit,
    data,
    xbegin,
    ylabel,
    ylim,
    fmt,
    small,
    face_map,
    vspan_list,
    is_show_value=True,
):
    x = data["time"]
    y = data["value"]

    if title is not None:
        ax.set_title(
            title,
            x=0.02,
            y=0.65,
            loc="left",
            fontproperties=face_map["title"],
            color="#111111",
        )
    ax.set_ylim(ylim)
    ax.set_xlim([xbegin, x[-1] + datetime.timedelta(hours=1)])

    ax.plot(
        x,
        y,
        color="#999999",
        marker="o",
        markevery=[len(y) - 1],
        markersize=8,
        markerfacecolor="#CCCCCC",
        markeredgewidth=5,
        markeredgecolor="#333333",
        linewidth=5.0,
        linestyle="solid",
    )

    ax.fill_between(x, y, 0, facecolor="#AAAAAA", alpha=0.5)

    if vspan_list is not None:
        for vspan in vspan_list:
            ax.axvspan(
                vspan[0], vspan[1], color="#000000", alpha=0.16 if vspan[2] else 0.07
            )

    if not data["valid"]:
        text = "?"
    else:
        text = fmt.format(
            next((item for item in reversed(y) if item is not None), None)
        )

    if small:
        font = face_map["value_small"]
    else:
        font = face_map["value"]

    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 6)))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter("\n%-H"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%-d日"))

    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3))
    ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))

    for label in ax.get_xticklabels():
        label.set_fontproperties(face_map["xaxis_major"])
    for label in ax.get_xminorticklabels():
        label.set_fontproperties(face_map["xaxis_minor"])

    for label in ax.get_yticklabels():
        label.set_fontproperties(face_map["yaxis"])

    ax.grid(
        axis="x", color="#000000", alpha=0.1, linestyle="-", which="both", linewidth=1
    )
    ax.grid(axis="y", color="#000000", alpha=0.1, linestyle="-", linewidth=1)

    if is_show_value:
        ax.text(
            0.96 - len(unit) * 0.05,
            0.05,
            text,
            transform=ax.transAxes,
            horizontalalignment="right",
            color="#000000",
            alpha=0.95,
            fontproperties=font,
        )

        ax.text(
            0.96,
            0.05,
            unit,
            transform=ax.transAxes,
            horizontalalignment="right",
            color="#000000",
            alpha=0.95,
            fontproperties=face_map["value_unit"],
        )

    ax.label_outer()


def draw_sensor_graph(graph_config, db_config, font_config):
    logging.info("draw sensor graph")

    face_map = get_face_map(font_config)

    equip_list = graph_config["EQUIP_LIST"]
    width = graph_config["WIDTH"]
    height = graph_config["HEIGHT"]

    plt.style.use("grayscale")

    fig = plt.figure(facecolor="azure", edgecolor="coral", linewidth=2)

    fig.set_size_inches(width / IMAGE_DPI, height / IMAGE_DPI)

    cache = None
    time_begin = datetime.datetime.now(datetime.timezone.utc)
    for row in range(0, len(equip_list)):
        data = fetch_data(
            db_config,
            equip_list[row]["TYPE"],
            equip_list[row]["HOST"],
            graph_config["PARAM"]["NAME"],
            graph_config["PARAM"]["PERIOD"],
        )
        if not data["valid"]:
            continue

        if data["time"][0] < time_begin:
            time_begin = data["time"][0]
        if cache is None:
            cache = {
                "time": data["time"],
                "value": [-100.0 for x in range(len(data["time"]))],
                "valid": False,
            }

    valve_on_range = get_valve_on_range(
        db_config,
        graph_config["VALVE"]["TYPE"],
        graph_config["VALVE"]["HOST"],
        graph_config["VALVE"]["PARAM"],
        graph_config["VALVE"]["THRESHOLD"],
        graph_config["PARAM"]["PERIOD"],
    )

    for row in range(0, len(equip_list)):
        data = fetch_data(
            db_config,
            equip_list[row]["TYPE"],
            equip_list[row]["HOST"],
            graph_config["PARAM"]["NAME"],
            graph_config["PARAM"]["PERIOD"],
        )
        if not data["valid"]:
            data = cache

        ax = fig.add_subplot(len(equip_list), 1, 1 + row)

        if "LABEL" not in equip_list[row]:
            title = equip_list[row]["HOST"]
        else:
            title = equip_list[row]["LABEL"]

        if "RANGE" in equip_list[row]:
            yrange = equip_list[row]["RANGE"]
        else:
            yrange = graph_config["PARAM"]["RANGE"]

        plot_item(
            ax,
            title,
            graph_config["PARAM"]["UNIT"],
            data,
            time_begin,
            graph_config["PARAM"]["UNIT"],
            yrange,
            graph_config["PARAM"]["FORMAT"],
            graph_config["PARAM"]["SIZE_SMALL"],
            face_map,
            valve_on_range if row != 0 else None,
            equip_list[row]["SHOW_VALUE"] if "SHOW_VALUE" in equip_list[row] else True,
        )

    fig.tight_layout()
    plt.subplots_adjust(hspace=0.1, wspace=0)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=IMAGE_DPI)

    return PIL.Image.open(buf)


if __name__ == "__main__":
    import logger

    from config import load_config

    logger.init("test")

    config = load_config()

    sensor_graph_img = draw_sensor_graph(
        config["GRAPH"], config["INFLUXDB"], config["FONT"]
    )

    sensor_graph_img.save("test.png", "PNG")
