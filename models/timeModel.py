import MetaTrader5 as mt5
import pytz

import config
from datetime import datetime, timedelta

def get_txt2timeframe(timeframe_txt):
    timeframe_dicts = {"1min": mt5.TIMEFRAME_M1, "2min": mt5.TIMEFRAME_M2, "3min": mt5.TIMEFRAME_M3, "4min": mt5.TIMEFRAME_M4,
                      "5min": mt5.TIMEFRAME_M5, "6min": mt5.TIMEFRAME_M6, "10min": mt5.TIMEFRAME_M10,
                      "12min": mt5.TIMEFRAME_M12,
                      "15min": mt5.TIMEFRAME_M15, "20min": mt5.TIMEFRAME_M20, "30min": mt5.TIMEFRAME_M30,
                      "1H": mt5.TIMEFRAME_H1,
                      "2H": mt5.TIMEFRAME_H2, "3H": mt5.TIMEFRAME_H3, "4H": mt5.TIMEFRAME_H4, "6H": mt5.TIMEFRAME_H6,
                      "8H": mt5.TIMEFRAME_H8, "12H": mt5.TIMEFRAME_H12, "1D": mt5.TIMEFRAME_D1, "1W": mt5.TIMEFRAME_W1,
                      "1MN": mt5.TIMEFRAME_MN1}
    return timeframe_dicts[timeframe_txt]

def get_timeframe2txt(mt5_timeframe_txt):
    timeframe_dicts = {mt5.TIMEFRAME_M1: "1min", mt5.TIMEFRAME_M2: "2min", mt5.TIMEFRAME_M3: "3min", mt5.TIMEFRAME_M4: "4min",
                      mt5.TIMEFRAME_M5: "5min", mt5.TIMEFRAME_M6: "6min", mt5.TIMEFRAME_M10: "10min",
                      mt5.TIMEFRAME_M12: "12min",
                      mt5.TIMEFRAME_M15: "15min", mt5.TIMEFRAME_M20: "M20", mt5.TIMEFRAME_M30: "30min",
                      mt5.TIMEFRAME_H1: "1H",
                      mt5.TIMEFRAME_H2: "2H", mt5.TIMEFRAME_H3: "3H", mt5.TIMEFRAME_H4: "4H", mt5.TIMEFRAME_H6: "6H",
                      mt5.TIMEFRAME_H8: "8H", mt5.TIMEFRAME_H12: "12H", mt5.TIMEFRAME_D1: "1D", mt5.TIMEFRAME_W1: "1D",
                      mt5.TIMEFRAME_MN1: "1MN"}
    return timeframe_dicts[mt5_timeframe_txt]

def get_utc_time_from_broker(time, timezone):
    """
    :param time: tuple (year, month, day, hour, mins) eg: (2010, 10, 30, 0, 0)
    :param time: str '2110300000'
    :param timezone: Check: set(pytz.all_timezones_set) - (Etc/UTC)
    :return: datetime format
    """
    if isinstance(time, (tuple, list)):
        dt = datetime(time[0], time[1], time[2], hour=time[3], minute=time[4])
    elif isinstance(time, str) and len(time) == 10:
        dt = datetime(int('20' + time[0:2]), int(time[2:4]), int(time[4:6]), hour=int(time[6:8]), minute=int(time[8:10]))
    else:
        raise Exception("Not correct type for time")
    dt = dt + timedelta(hours=config.BROKER_TIME_BETWEEN_UTC, minutes=0)
    utc_time = pytz.timezone(timezone).localize(dt)
    return utc_time

def get_current_utc_time_from_broker(timezone):
    """
    :param time: tuple (year, month, day, hour, mins) eg: (2010, 10, 30, 0, 0)
    :param timezone: Check: set(pytz.all_timezones_set) - (Etc/UTC)
    :return: datetime format
    """
    now = datetime.today()
    dt = datetime(now.year, now.month, now.day, hour=now.hour, minute=now.minute) + timedelta(hours=config.BROKER_TIME_BETWEEN_UTC, minutes=0)
    utc_time = pytz.timezone(timezone).localize(dt)
    return utc_time

def get_time_string(time):
    """
    :param time: time_tuple: tuple (yyyy,m,d,h,m): (2021, 10, 30, 0, 0)
    :return: string: '2110300000'
    """
    if isinstance(time, (tuple, list)):
        time_string = ''
        for slot in time:
            time_string += str(slot).zfill(2) + '-'
    else:
        raise Exception("Not correct type for time")
    return time_string[:-1]

def get_current_time_string(with_seconds=False):
    now = datetime.today()
    if not with_seconds:
        end_str = get_time_string((now.year, now.month, now.day, now.hour, now.minute))
    else:
        end_str = get_time_string((now.year, now.month, now.day, now.hour, now.minute, now.second))
    return end_str