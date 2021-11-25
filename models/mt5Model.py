import collections
from datetime import datetime
import pandas as pd

import MetaTrader5 as mt5
from models import timeModel

def connect_server():
    # connect to MetaTrader 5
    if not mt5.initialize():
        print("initialize() failed")
        mt5.shutdown()
    else:
        print("MetaTrader Connected")

def disconnect_server():
    # disconnect to MetaTrader 5
    mt5.shutdown()
    print("MetaTrader Shutdown.")

def get_historical_data(symbol, timeframe, timezone, start, end=None):
    """
    :param symbol: str
    :param timeframe: str, '1H'
    :param timezone: Check: set(pytz.all_timezones_set) - (Etc/UTC)
    :param start (local time): tuple (year, month, day, hour, mins) eg: (2010, 10, 30, 0, 0)
    :param end (local time): tuple (year, month, day, hour, mins), if None, then take data until present
    :return: dataframe
    """
    timeframe = timeModel.get_txt2timeframe(timeframe)
    utc_from = timeModel.get_utc_time_from_broker(start, timezone)
    if end == None:  # if end is None, get the data at current time
        now = datetime.today()
        now_tuple = (now.year, now.month, now.day, now.hour, now.minute)
        utc_to = timeModel.get_utc_time_from_broker(now_tuple, timezone)
    else:
        utc_to = timeModel.get_utc_time_from_broker(end, timezone)
    rates = mt5.copy_rates_range(symbol, timeframe, utc_from, utc_to)
    rates_frame = pd.DataFrame(rates, dtype=float)  # create DataFrame out of the obtained data
    rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')  # convert time in seconds into the datetime format
    rates_frame = rates_frame.set_index('time')
    return rates_frame

def get_current_bars(symbol, timeframe, count):
    """
    :param symbols: str
    :param timeframe: str, '1H'
    :param count: int
    :return: df
    """
    timeframe = timeModel.get_txt2timeframe(timeframe)
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)  # 0 means the current bar
    rates_frame = pd.DataFrame(rates, dtype=float)
    rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')
    rates_frame = rates_frame.set_index('time')
    return rates_frame

def get_all_symbols_info():
    """
    :return: dict[symbol] = collections.nametuple
    """
    symbols_info = {}
    symbols = mt5.symbols_get()
    for symbol in symbols:
        symbol_name = symbol.name
        symbols_info[symbol_name] = collections.namedtuple("info", ['digits', 'base', 'quote', 'swap_long', 'swap_short', 'pt_value'])
        symbols_info[symbol_name].digits = symbol.digits
        symbols_info[symbol_name].base = symbol.currency_base
        symbols_info[symbol_name].quote = symbol.currency_profit
        symbols_info[symbol_name].swap_long = symbol.swap_long
        symbols_info[symbol_name].swap_short = symbol.swap_short
        if symbol_name[3:] == 'JPY':
            symbols_info[symbol_name].pt_value = 100   # 100 dollar for quote per each point    (See note Stock Market - Knowledge - note 3)
        else:
            symbols_info[symbol_name].pt_value = 1     # 1 dollar for quote per each point  (See note Stock Market - Knowledge - note 3)
    return symbols_info