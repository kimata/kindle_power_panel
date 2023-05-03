#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import PIL.Image
import logging
import traceback
import textwrap
import notify_slack

import logger
from sensor_graph import draw_sensor_graph

from usage_panel import draw_usage_panel
from pil_util import draw_text, get_font
from config import load_config

######################################################################
logger.init("panel.kindle.power")

logging.info("start to create image")

config = load_config()

img = PIL.Image.new(
    "L",
    (config["PANEL"]["DEVICE"]["WIDTH"], config["PANEL"]["DEVICE"]["HEIGHT"]),
    "#FFF",
)
try:
    usage_panel_img = draw_usage_panel(
        config["USAGE"], config["INFLUXDB"], config["FONT"], config["ICON"]
    )
    sensor_graph_img = draw_sensor_graph(
        config["GRAPH"], config["INFLUXDB"], config["FONT"]
    )

    img.paste(sensor_graph_img, (0, config["GRAPH"]["OFFSET"]))
    img.alpha_composite(usage_panel_img, (0, 0))

except:
    draw = PIL.ImageDraw.Draw(img)
    draw.rectangle(
        (0, 0, config["PANEL"]["DEVICE"]["WIDTH"], config["PANEL"]["DEVICE"]["HEIGHT"]),
        fill=(255),
    )

    draw_text(
        img,
        "ERROR",
        (10, 40),
        get_font(config["FONT"], "EN_BOLD", 160),
        "left",
        "#666",
    )

    draw_text(
        img,
        "\n".join(textwrap.wrap(traceback.format_exc(), 60)),
        (20, 180),
        get_font(config["FONT"], "EN_MEDIUM", 36),
        "left" "#333",
    )
    if "SLACK" in config:
        notify_slack.error(
            config["SLACK"]["BOT_TOKEN"],
            config["SLACK"]["ERROR"]["CHANNEL"],
            traceback.format_exc(),
            "エラー",
            config["SLACK"]["ERROR"]["INTERVAL_MIN"],
        )
    print(traceback.format_exc(), file=sys.stderr)


img.save(sys.stdout.buffer, "PNG")
