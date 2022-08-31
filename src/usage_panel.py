#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import os
import pathlib
import logging
import datetime

from sensor_data import get_on_minutes


def get_font(config, font_type, size):
    return PIL.ImageFont.truetype(
        str(
            pathlib.Path(
                os.path.dirname(__file__), config["PATH"], config["MAP"][font_type]
            )
        ),
        size,
    )


def get_face_map(font_config):
    return {
        "usage": {
            "label": get_font(font_config, "JP_REGULAR", 40),
            "value": get_font(font_config, "JP_BOLD", 120),
            "unit": get_font(font_config, "JP_REGULAR", 50),
        },
    }


def draw_text(img, text, pos, font, align="left", color="#000"):
    draw = PIL.ImageDraw.Draw(img)

    if align == "center":
        pos = (pos[0] - font.getsize(text)[0] / 2, pos[1])
    elif align == "right":
        pos = (pos[0] - font.getsize(text)[0], pos[1])

    draw.text(pos, text, color, font, None, font.getsize(text)[1] * 0.4)

    return font.getsize(text)[0]


def draw_usage(img, panel_config, db_config, face):
    now = datetime.datetime.now()
    period = "{hour}h{minute}m".format(hour=now.hour, minute=now.minute)
    on_minutes = get_on_minutes(
        db_config,
        panel_config["TARGET"]["TYPE"],
        panel_config["TARGET"]["HOST"],
        panel_config["TARGET"]["PARAM"],
        panel_config["TARGET"]["THRESHOLD"],
        period,
    )
    label = "本日"

    x = 1025
    y = 200

    unit_dy = face["value"].getsize("0")[1] - face["unit"].getsize("0")[1]
    label_dy = face["value"].getsize("0")[1] - face["label"].getsize("0")[1]

    if (on_minutes == 0) or (on_minutes % 60) != 0:
        x -= draw_text(
            img,
            "分",
            [x, y + unit_dy],
            face["unit"],
            "right",
            color="#000",
        )
        x -= (
            draw_text(
                img,
                "{minute:02d}".format(minute=on_minutes % 60),
                [x, y],
                face["value"],
                "right",
                color="#000",
            )
            + 10
        )
    if on_minutes >= 60:
        x -= draw_text(
            img,
            "時間",
            [x, y + unit_dy],
            face["unit"],
            "right",
            color="#000",
        )
        x -= (
            draw_text(
                img,
                "{hour:.0f}".format(hour=on_minutes / 60),
                [x, y],
                face["value"],
                "right",
                color="#000",
            )
            + 10
        )
    x -= draw_text(
        img,
        label,
        [x, y + label_dy],
        face["label"],
        "right",
        color="#000",
    )


def draw_usage_panel(panel_config, db_config, font_config):
    logging.info("draw usage panel")

    img = PIL.Image.new(
        "RGBA", (panel_config["WIDTH"], panel_config["HEIGHT"]), (255, 255, 255, 0)
    )
    face_map = get_face_map(font_config)

    draw_usage(img, panel_config, db_config, face_map["usage"])

    return img
