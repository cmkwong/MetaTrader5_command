import pandas as pd
import MetaTrader5 as mt5
from models import timeModel

class TickController:
    def __init__(self):
        pass

    def get_ticks(self, symbol, utc_from, utc_to):
        ticks = mt5.copy_ticks_range(symbol, utc_from, utc_to, mt5.COPY_TICKS_ALL)
        return ticks

    def get_last_ticks(self, symbol):
        lasttick = mt5.symbol_info_tick(symbol)
        return lasttick

    def get_spread_from_ticks(self, ticks_frame, symbol):
        """
        :param ticks_frame: pd.DataFrame, all tick info
        :return: pd.Series
        """
        spread = pd.Series((ticks_frame['ask'] - ticks_frame['bid']) * (10 ** mt5.symbol_info(symbol).digits), index=ticks_frame.index, name='ask_bid_spread_pt')
        spread = spread.groupby(spread.index).mean()  # groupby() note 56b
        return spread

    def get_ticks_range(self, symbol, start, end, timezone):
        """
        :param symbol: str, symbol
        :param start: tuple, (2019,1,1)
        :param end: tuple, (2020,1,1)
        :param count:
        :return:
        """
        utc_from = timeModel.get_utc_time_from_broker(start, timezone)
        utc_to = timeModel.get_utc_time_from_broker(end, timezone)
        ticks = mt5.copy_ticks_range(symbol, utc_from, utc_to, mt5.COPY_TICKS_ALL)
        ticks_frame = pd.DataFrame(ticks)  # set to dataframe, several name of cols like, bid, ask, volume...
        ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')  # transfer numeric time into second
        ticks_frame = ticks_frame.set_index('time')  # set the index
        return ticks_frame

    def get_last_tick(self, symbol):
        """
        :param symbol: str
        :return: dict: symbol info
        """
        # display the last GBPUSD tick
        lasttick = mt5.symbol_info_tick(symbol)
        # display tick field values in the form of a list
        last_tick_dict = lasttick._asdict()
        for key, value in last_tick_dict.items():
            print("  {}={}".format(key, value))
        return last_tick_dict