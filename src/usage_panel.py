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


def open_icon(config, name):
    return PIL.Image.open(
        str(
            pathlib.Path(os.path.dirname(__file__), config["PATH"], config["MAP"][name])
        )
    )


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
            "work": {
                "label": get_font(font_config, "JP_REGULAR", 50),
                "value": get_font(font_config, "EN_HEAVY", 160),
                "unit": get_font(font_config, "JP_REGULAR", 60),
            },
            "leave": {
                "label": get_font(font_config, "JP_REGULAR", 40),
                "value": get_font(font_config, "JP_REGULAR", 40),
                "unit": get_font(font_config, "JP_REGULAR", 30),
            },
        },
        "date": {
            "value": get_font(font_config, "EN_MEDIUM", 40),
        },
    }


def draw_icon(img, config, name, pos_x, pos_y, w=128, h=128):
    icon = open_icon(config, name).resize((w, h))

    img.paste(icon, (pos_x, pos_y))


def draw_text(img, text, pos, font, align="left", color="#000"):
    draw = PIL.ImageDraw.Draw(img)

    if align == "center":
        pos = (pos[0] - font.getsize(text)[0] / 2, pos[1])
    elif align == "right":
        pos = (pos[0] - font.getsize(text)[0], pos[1])

    draw.text(pos, text, color, font, None, font.getsize(text)[1] * 0.4)

    return font.getsize(text)[0]


def draw_time(img, x, y, label, minutes, suffix, face):
    value_height = face["value"].getsize("0")[1]
    unit_dy = value_height - face["unit"].getsize("0")[1]
    label_dy = value_height - face["label"].getsize("0")[1]

    if suffix is not None:
        x -= draw_text(
            img,
            suffix,
            [x, y + label_dy],
            face["label"],
            "right",
            color="#000",
        )
    if (minutes == 0) or (minutes % 60) != 0:
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
                "0" if minutes == 0 else "{minute:02d}".format(minute=minutes % 60),
                [x, y],
                face["value"],
                "right",
                color="#000",
            )
            + 10
        )
    if minutes >= 60:
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
                "{hour:.0f}".format(hour=minutes / 60),
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

    return value_height


def draw_usage(img, panel_config, db_config, icon_config, face):
    now = datetime.datetime.now()
    period = "{hour}h{minute}m".format(hour=now.hour, minute=now.minute)

    work_minutes = get_on_minutes(
        db_config,
        panel_config["TARGET"]["TYPE"],
        panel_config["TARGET"]["HOST"],
        panel_config["TARGET"]["PARAM"],
        panel_config["TARGET"]["THRESHOLD"]["WORK"],
        period,
    )
    wake_minutes = get_on_minutes(
        db_config,
        panel_config["TARGET"]["TYPE"],
        panel_config["TARGET"]["HOST"],
        panel_config["TARGET"]["PARAM"],
        panel_config["TARGET"]["THRESHOLD"]["WAKE"],
        period,
    )
    leave_minutes = wake_minutes - work_minutes

    logging.info(
        "today usage: {work} min (leave: {leave} min)".format(
            work=work_minutes, leave=leave_minutes
        )
    )

    x = 995
    y = 130

    y += draw_time(img, x, y, "本日", work_minutes, None, face["work"])
    if leave_minutes > 5:
        y += 20
        draw_time(img, x, y, "(放置 ", leave_minutes, ")", face["leave"])

    draw_icon(img, icon_config, "TV", 130, 160)
    for i in range(3):
        draw_icon(img, icon_config, "AIRCON", 130, 340 * i + 500)


def draw_datetime(img, panel_config, face):
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), "JST"))

    draw_text(
        img,
        now.strftime("%Y/%-m/%-d %H:%M"),
        [panel_config["WIDTH"] - 20, 10],
        face["value"],
        "right",
        color="#333",
    )


def draw_usage_panel(panel_config, db_config, font_config, icon_config):
    logging.info("draw usage panel")

    img = PIL.Image.new(
        "RGBA", (panel_config["WIDTH"], panel_config["HEIGHT"]), (255, 255, 255, 0)
    )
    face_map = get_face_map(font_config)

    draw_usage(img, panel_config, db_config, icon_config, face_map["usage"])
    draw_datetime(img, panel_config, face_map["date"])

    return img
