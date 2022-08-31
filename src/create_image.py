#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import PIL.Image
import io
import logging

import logger
from sensor_graph import draw_sensor_graph

from usage_panel import draw_usage_panel
from config import load_config

######################################################################
logger.init("panel.kindle.power")

logging.info("start to create image")

config = load_config()

usage_panel_img = draw_usage_panel(config["USAGE"], config["INFLUXDB"], config["FONT"])
sensor_graph_img = draw_sensor_graph(
    config["GRAPH"], config["INFLUXDB"], config["FONT"]
)

img = PIL.Image.new(
    "RGBA",
    (config["PANEL"]["DEVICE"]["WIDTH"], config["PANEL"]["DEVICE"]["HEIGHT"]),
    (255, 255, 255, 255),
)

img.paste(sensor_graph_img, (0, config["GRAPH"]["OFFSET"]))
img.alpha_composite(usage_panel_img, (0, 0))

bytes_io = io.BytesIO()
img.convert("L").save(bytes_io, "PNG")
bytes_io.seek(0)

sys.stdout.buffer.write(bytes_io.getvalue())
