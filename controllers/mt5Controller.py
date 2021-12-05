import collections

import MetaTrader5 as mt5

class Mt5Controller:
    def __init__(self, timezone):
        """
        :param timezone: Check: set(pytz.all_timezones_set) - (Etc/UTC)
        """
        self.connect_server()
        self.timezone = timezone
        self.all_symbols_info = self.get_all_symbols_info() # get from broker

    def connect_server(self):
        # connect to MetaTrader 5
        if not mt5.initialize():
            print("initialize() failed")
            mt5.shutdown()
        else:
            print("MetaTrader Connected")

    def disconnect_server(self):
        # disconnect to MetaTrader 5
        mt5.shutdown()
        print("MetaTrader Shutdown.")

    def get_all_symbols_info(self):
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
                symbols_info[symbol_name].pt_value = 100  # 100 dollar for quote per each point    (See note Stock Market - Knowledge - note 3)
            else:
                symbols_info[symbol_name].pt_value = 1  # 1 dollar for quote per each point  (See note Stock Market - Knowledge - note 3)
        return symbols_info

    def get_symbol_info(self, symbol):
        return mt5.symbol_info(symbol)

    def get_data(self, symbol, timeframe, utc_from, utc_to):
        """
        :param symbol: str
        :param timeframe: str, '1H'
        :param utc_from (local time): datetime
        :param utc_to (local time): datetime
        :return: dataframe
        """
        rates = mt5.copy_rates_range(symbol, timeframe, utc_from, utc_to)
        return rates

    def get_data_from_pos(self, symbol, timeframe, start_pos, count):
        rates = mt5.copy_rates_from_pos(symbol, timeframe, start_pos=start_pos, count=count)  # 0 means the current bar
        return rates

    def get_ticks(self, symbol, utc_from, utc_to):
        ticks = mt5.copy_ticks_range(symbol, utc_from, utc_to, mt5.COPY_TICKS_ALL)
        return ticks

    def get_last_ticks(self, symbol):
        lasttick = mt5.symbol_info_tick(symbol)
        return lasttick