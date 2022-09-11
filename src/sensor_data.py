#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import influxdb_client
import datetime
import os
import re
import logging
import traceback

FLUX_QUERY = """
from(bucket: "{bucket}")
    |> range(start: -{period})
    |> filter(fn:(r) => r._measurement == "{sensor_type}")
    |> filter(fn: (r) => r.hostname == "{hostname}")
    |> filter(fn: (r) => r["_field"] == "{param}")
    |> fill(usePrevious: true)
    |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
"""


def fetch_data_impl(config, sensor_type, hostname, param, period, window="10m"):
    try:
        token = os.environ.get("INFLUXDB_TOKEN", config["TOKEN"])
        query = FLUX_QUERY.format(
            bucket=config["BUCKET"],
            sensor_type=sensor_type,
            hostname=hostname,
            param=param,
            period=period,
            window=window,
        )
        logging.debug("Flux query = {query}".format(query=query))
        client = influxdb_client.InfluxDBClient(
            url=config["URL"], token=token, org=config["ORG"]
        )
        query_api = client.query_api()

        return query_api.query(query=query)
    except:
        logging.error("Flux query = {query}".format(query=query))
        logging.error(traceback.format_exc())
        raise


def fetch_data(config, sensor_type, hostname, param, period="30h", window="10m"):
    try:
        table_list = fetch_data_impl(
            config, sensor_type, hostname, param, period, window
        )
        data = []
        time = []
        localtime_offset = datetime.timedelta(hours=9)

        if len(table_list) != 0:
            for record in table_list[0].records:
                data.append(record.get_value())
                time.append(record.get_time() + localtime_offset)

        return {"value": data, "time": time, "valid": len(time) != 0}
    except:
        return {"value": [], "time": [], "valid": False}


def get_valve_on_range(
    config, sensor_type, hostname, param, threshold, period="30h", window="10m"
):
    try:
        table_list = fetch_data_impl(
            config, sensor_type, hostname, param, period, window
        )

        if len(table_list) != 0:
            # NOTE: 常時冷却と間欠冷却の期間を求める
            on_range = []
            state = "IDLE"
            start_time = None
            localtime_offset = datetime.timedelta(hours=9)

            for record in table_list[0].records:
                if record.get_value() > threshold["FULL"]:
                    if state != "FULL":
                        if state == "INTERM":
                            on_range.append(
                                [
                                    start_time + localtime_offset,
                                    record.get_time() + localtime_offset,
                                    False,
                                ]
                            )
                        state = "FULL"
                        start_time = record.get_time()
                elif record.get_value() > threshold["INTERM"]:
                    if state != "INTERM":
                        if state == "FULL":
                            on_range.append(
                                [
                                    start_time + localtime_offset,
                                    record.get_time() + localtime_offset,
                                    True,
                                ]
                            )
                        state = "INTERM"
                        start_time = record.get_time()
                else:
                    if state != "IDLE":
                        on_range.append(
                            [
                                start_time + localtime_offset,
                                record.get_time() + localtime_offset,
                                state == "FULL",
                            ]
                        )
                    state = "IDLE"

        if state != "IDLE":
            on_range.append(
                [
                    start_time + localtime_offset,
                    table_list[0].records[-1].get_time() + localtime_offset,
                    state == "FULL",
                ]
            )

        return on_range
    except:
        return []


def get_equip_on_minutes(
    config, sensor_type, hostname, param, threshold, period="30h", window="10m"
):
    m = re.search(r"^(\d+)m$", window)
    if m is None:
        raise RuntimeError("引数が異常です")
    else:
        unit = int(m.group(1))

    try:
        table_list = fetch_data_impl(
            config, sensor_type, hostname, param, period, window
        )

        count = 0
        if len(table_list) != 0:
            for record in table_list[0].records:
                if record.get_value() >= threshold:
                    count += 1

        return count * unit
    except:
        return 0


if __name__ == "__main__":
    import logger
    import json

    from config import load_config

    logger.init("test", logging.DEBUG)

    config = load_config()

    now = datetime.datetime.now()
    sensor_type = config["USAGE"]["TARGET"]["TYPE"]
    hostname = config["USAGE"]["TARGET"]["HOST"]
    param = config["USAGE"]["TARGET"]["PARAM"]
    threshold = config["USAGE"]["TARGET"]["THRESHOLD"]["WORK"]
    period = config["GRAPH"]["PARAM"]["PERIOD"]

    logging.info(
        "data = {data}".format(
            data=json.dumps(
                fetch_data(config["INFLUXDB"], sensor_type, hostname, param, period),
                sort_keys=True,
                indent=2,
                default=str,
            )
        )
    )
    period = "{hour}h{minute}m".format(hour=now.hour, minute=now.minute)

    logging.info(
        "ON minutes (for {period}) = {minutes} min".format(
            period=period,
            minutes=get_equip_on_minutes(
                config["INFLUXDB"], sensor_type, hostname, param, threshold, period
            ),
        )
    )

    sensor_type = config["GRAPH"]["VALVE"]["TYPE"]
    hostname = config["GRAPH"]["VALVE"]["HOST"]
    param = config["GRAPH"]["VALVE"]["PARAM"]
    threshold = config["GRAPH"]["VALVE"]["THRESHOLD"]
    period = config["GRAPH"]["PARAM"]["PERIOD"]

    logging.info(
        "Valve on range = {range_list}".format(
            range_list=json.dumps(
                get_valve_on_range(
                    config["INFLUXDB"], sensor_type, hostname, param, threshold, period
                ),
                indent=2,
                default=str,
            )
        )
    )
