import MetaTrader5 as mt5
from executeController import Mt5Executor
from symbolController import SymbolController

class Mt5Controller:
    def __init__(self, timezone):
        """
        :param timezone: Check: set(pytz.all_timezones_set) - (Etc/UTC)
        """
        self.symbolController = SymbolController()
        self.executor = Mt5Executor()

        self.connect_server()
        self.timezone = timezone
        self.all_symbols_info = self.symbolController.get_all_symbols_info() # get from broker

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

