#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
電子ペーパ表示用の画像を生成します．

Usage:
  create_image.py [-f CONFIG] [-o PNG_FILE]

Options:
  -f CONFIG    : CONFIG を設定ファイルとして読み込んで実行します．[default: config.yaml]
  -o PNG_FILE  : 生成した画像を指定されたパスに保存します．
"""

from docopt import docopt

import sys
import PIL.Image
import logging
import traceback
import textwrap
import notify_slack

import logger
from sensor_graph import draw_sensor_graph

from usage_panel import draw_usage_panel
from pil_util import draw_text, get_font, convert_to_gray
from config import load_config


def notify_error(config):
    notify_slack.error(
        config["SLACK"]["BOT_TOKEN"],
        config["SLACK"]["ERROR"]["CHANNEL"],
        config["SLACK"]["FROM"],
        traceback.format_exc(),
        config["SLACK"]["ERROR"]["INTERVAL_MIN"],
    )


######################################################################
args = docopt(__doc__)

logger.init("panel.kindle.power", level=logging.INFO)

logging.info("start to create image")

config = load_config(args["-f"])

img = PIL.Image.new(
    "RGBA",
    (config["PANEL"]["DEVICE"]["WIDTH"], config["PANEL"]["DEVICE"]["HEIGHT"]),
    (255, 255, 255, 255),
)

status = 0
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
        fill=(255, 255, 255, 255),
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
        notify_error(config)

    print(traceback.format_exc(), file=sys.stderr)
    # NOTE: 使われてなさそうな値にしておく．
    # display_image.py と合わせる必要あり．
    status = 222

if args["-o"] is not None:
    out_file = args["-o"]
else:
    out_file = sys.stdout.buffer

logging.info("Save {out_file}.".format(out_file=str(out_file)))
convert_to_gray(img).save(out_file, "PNG")

exit(status)
