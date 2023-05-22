#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import logging
import datetime

from sensor_data import get_equip_on_minutes
from pil_util import draw_text, text_size, get_font, load_image


def get_face_map(font_config):
    return {
        "usage": {
            "work": {
                "label": get_font(font_config, "JP_REGULAR", 50),
                "value": get_font(font_config, "JP_BOLD", 150),
                "unit": get_font(font_config, "JP_REGULAR", 60),
            },
            "leave": {
                "label": get_font(font_config, "JP_REGULAR", 40),
                "value": get_font(font_config, "JP_REGULAR", 40),
                "unit": get_font(font_config, "JP_REGULAR", 30),
            },
        },
        "date": {
            "value": get_font(font_config, "EN_MEDIUM", 36),
        },
    }


def draw_icon(img, config, name, pos_x, pos_y):
    img.paste(load_image(config[name]), (pos_x, pos_y))


def draw_time(img, x, y, label, minutes, suffix, face):
    value_height = face["value"].getsize("0")[1]
    unit_dy = value_height - face["unit"].getsize("0")[1]
    label_dy = value_height - face["label"].getsize("0")[1]

    if suffix is not None:
        draw_text(
            img,
            suffix,
            [x, y + label_dy],
            face["label"],
            "right",
            "#000",
            False,
        )
        x -= text_size(face["label"], suffix)[0]

    if (minutes == 0) or (minutes % 60) != 0:
        draw_text(
            img,
            "分",
            [x, y + unit_dy],
            face["unit"],
            "right",
            "#000",
            False,
        )
        x -= text_size(face["unit"], "分")[0] + 10

        if minutes < 10:
            minute_text = "{minute:d}".format(minute=minutes)
        else:
            minute_text = "{minute:02d}".format(minute=minutes % 60)
        draw_text(img, minute_text, [x, y], face["value"], "right", "#000", False)
        x -= text_size(face["value"], minute_text)[0] + 10

    if minutes >= 60:
        draw_text(img, "時間", [x, y + unit_dy], face["unit"], "right", "#000", False)
        x -= text_size(face["unit"], "時間")[0] + 10

        hour_text = "{hour:.0f}".format(hour=minutes / 60)
        draw_text(img, hour_text, [x, y], face["value"], "right", "#000", False)
        x -= text_size(face["value"], hour_text)[0] + 10

    draw_text(img, label, [x, y + label_dy], face["label"], "right", "#000", False)

    return value_height


def draw_usage(
    img,
    panel_config,
    db_config,
    equip_list,
    offset_y,
    sub_plot_height,
    face,
    icon_config,
):
    now = datetime.datetime.now()
    period = "{hour}h{minute}m".format(hour=now.hour, minute=now.minute)

    work_minutes = get_equip_on_minutes(
        db_config,
        panel_config["TARGET"]["TYPE"],
        panel_config["TARGET"]["HOST"],
        panel_config["TARGET"]["PARAM"],
        panel_config["TARGET"]["THRESHOLD"]["WORK"],
        period,
    )
    wake_minutes = get_equip_on_minutes(
        db_config,
        panel_config["TARGET"]["TYPE"],
        panel_config["TARGET"]["HOST"],
        panel_config["TARGET"]["PARAM"],
        panel_config["TARGET"]["THRESHOLD"]["WAKE"],
        period,
    )
    leave_minutes = max(wake_minutes - work_minutes - 5, 0)

    logging.info(
        "today usage: {work} min (leave: {leave} min)".format(
            work=work_minutes, leave=leave_minutes
        )
    )

    x = 980
    y = offset_y + 30

    if leave_minutes > 5:
        y += draw_time(img, x, y, "本日", work_minutes, None, face["work"])
        y += 15
        draw_time(img, x, y, "(放置 ", leave_minutes, ")", face["leave"])
    else:
        y += 45
        draw_time(img, x, y, "本日", work_minutes, None, face["work"])

    y = offset_y + 130
    for i in range(len(equip_list)):
        draw_icon(img, icon_config, equip_list[i]["ICON"], 110, int(y))
        y += sub_plot_height


def draw_datetime(img, panel_config, face):
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), "JST"))

    draw_text(
        img,
        now.strftime("%Y/%-m/%-d %H:%M"),
        [panel_config["WIDTH"] - 20, 15],
        face["value"],
        "right",
        color="#333",
    )


def draw_usage_panel(
    panel_config,
    db_config,
    equip_list,
    offset_y,
    sub_plot_height,
    font_config,
    icon_config,
):
    logging.info("draw usage panel")

    img = PIL.Image.new(
        "RGBA", (panel_config["WIDTH"], panel_config["HEIGHT"]), (255, 255, 255, 0)
    )
    face_map = get_face_map(font_config)

    draw_usage(
        img,
        panel_config,
        db_config,
        equip_list,
        offset_y,
        sub_plot_height,
        face_map["usage"],
        icon_config,
    )
    draw_datetime(img, panel_config, face_map["date"])

    return img
