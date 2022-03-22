import collections
from datetime import datetime
import pandas as pd

import config
from models import exchgModel, fileModel, pointsModel, timeModel
from selfUtils import tools

class DataLoader: # created note 86a
    def __init__(self, mt5Controller, local_data_path='', deposit_currency='USD'):

        # for local
        self.local_data_path = local_data_path # a symbol of data that stored in this directory
        self.deposit_currency = deposit_currency
        self.data_time_difference_to_UTC = config.DOWNLOADED_MIN_DATA_TIME_BETWEEN_UTC

        # for mt5
        self.mt5Controller = mt5Controller

    def prepare(self):
        # prepare
        self.Prices_Collection = collections.namedtuple("Prices_Collection", ['o','h','l','c', 'cc', 'ptDv','quote_exchg','base_exchg'])
        self.latest_Prices_Collection = collections.namedtuple("latest_Prices_Collection", ['c', 'cc', 'ptDv', 'quote_exchg']) # for latest Prices
        self._symbols_available = False # only for usage of _check_if_symbols_available()

    def _price_type_from_code(self, ohlc):
        """
        :param ohlc: str of code, eg: '1001'
        :return: list, eg: ['open', 'close']
        """
        type_names = ['open', 'high', 'low', 'close']
        required_types = []
        for i, c in enumerate(ohlc):
            if c == '1':
                required_types.append(type_names[i])
        return required_types

    def _prices_df2dict(self, prices_df, symbols, ohlc):

        # rename columns of the prices_df
        col_names = self._price_type_from_code(ohlc)
        prices_df.columns = col_names * len(symbols)

        prices = {}
        max_length = len(prices_df.columns)
        step = len(col_names)
        for i in range(0, max_length, step):
            symbol = symbols[int(i / step)]
            prices[symbol] = prices_df.iloc[:, i:i + step]
        return prices

    def _get_specific_from_prices(self, prices, required_symbols, ohlc):
        """
        :param prices: {symbol: pd.DataFrame}
        :param required_symbols: [str]
        :param ohlc: str, '1000'
        :return: pd.DataFrame
        """
        types = self._price_type_from_code(ohlc)
        required_prices = pd.DataFrame()
        for i, symbol in enumerate(required_symbols):
            if i == 0:
                required_prices = prices[symbol].loc[:, types].copy()
            else:
                required_prices = pd.concat([required_prices, prices[symbol].loc[:, types]], axis=1)
        required_prices.columns = required_symbols
        return required_prices

    def _check_if_symbols_available(self, required_symbols, local):
        """
        check if symbols exist, note 83h
        :param required_symbols: [str]
        :return: None
        """
        if not self._symbols_available:
            for symbol in required_symbols:
                if not local:
                    try:
                        _ = self.mt5Controller.all_symbols_info[symbol]
                    except KeyError:
                        raise Exception("The {} is not provided in this broker.".format(symbol))
                else:
                    fs = fileModel.get_file_list(self.local_data_path)
                    if symbol not in fs:
                        raise Exception("The {} is not provided in my {}.".format(symbol, self.local_data_path))
            self._symbols_available = True

    def _get_ohlc_rule(self, df):
        """
        note 85e
        Only for usage on change_timeframe()
        :param check_code: list
        :return: raise exception
        """
        check_code = [0, 0, 0, 0]
        ohlc_rule = {}
        for key in df.columns:
            if key == 'open':
                check_code[0] = 1
                ohlc_rule['open'] = 'first'
            elif key == 'high':
                check_code[1] = 1
                ohlc_rule['high'] = 'max'
            elif key == 'low':
                check_code[2] = 1
                ohlc_rule['low'] = 'min'
            elif key == 'close':
                check_code[3] = 1
                ohlc_rule['close'] = 'last'
        # first exception
        if check_code[1] == 1 or check_code[2] == 1:
            if check_code[0] == 0 or check_code[3] == 0:
                raise Exception("When high/low needed, there must be open/close data included. \nThere is not open/close data.")
        # Second exception
        if len(df.columns) > 4:
            raise Exception("The DataFrame columns is exceeding 4")
        return ohlc_rule

    def _change_timeframe(self, df, timeframe):
        """
        note 84f
        :param df: pd.DataFrame, having header: open high low close
        :param rule: can '2H', https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#resampling
        :return:
        """
        ohlc_rule = self._get_ohlc_rule(df)
        df = df.resample(timeframe).apply(ohlc_rule)
        df.dropna(inplace=True)
        return df

    def get_ticks_range(self, symbol, start, end):
        """
        :param symbol: str, symbol
        :param start: tuple, (2019,1,1)
        :param end: tuple, (2020,1,1)
        :param count:
        :return:
        """
        utc_from = timeModel.get_utc_time_from_broker(start, self.mt5Controller.timezone)
        utc_to = timeModel.get_utc_time_from_broker(end, self.mt5Controller.timezone)
        ticks = self.mt5Controller.get_ticks(symbol, utc_from, utc_to)
        ticks_frame = pd.DataFrame(ticks)  # set to dataframe, several name of cols like, bid, ask, volume...
        ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')  # transfer numeric time into second
        ticks_frame = ticks_frame.set_index('time')  # set the index
        return ticks_frame

    def get_spread_from_ticks(self, ticks_frame, symbol):
        """
        :param ticks_frame: pd.DataFrame, all tick info
        :return: pd.Series
        """
        spread = pd.Series((ticks_frame['ask'] - ticks_frame['bid']) * (10 ** self.mt5Controller.get_symbol_info(symbol).digits), index=ticks_frame.index, name='ask_bid_spread_pt')
        spread = spread.groupby(spread.index).mean()  # groupby() note 56b
        return spread

    def get_spreads(self, symbols, start, end):
        """
        :param symbols: [str]
        :param start (local time): tuple (year, month, day, hour, mins) eg: (2010, 10, 30, 0, 0)
        :param end (local time): tuple (year, month, day, hour, mins), if None, then take data until present
        :return: pd.DataFrame
        """
        spreads = pd.DataFrame()
        for symbol in symbols:
            tick_frame = self.get_ticks_range(symbol, start, end)
            spread = self.get_spread_from_ticks(tick_frame, symbol)
            spreads = pd.concat([spreads, spread], axis=1, join='outer')
        spreads.columns = symbols
        return spreads

    def split_Prices(self, Prices, percentage):
        keys = list(Prices._asdict().keys())
        prices = collections.namedtuple("prices", keys)
        train_list, test_list = [], []
        for df in Prices:
            train, test = tools.split_df(df, percentage)
            train_list.append(train)
            test_list.append(test)
        Train_Prices = prices._make(train_list)
        Test_Prices = prices._make(test_list)
        return Train_Prices, Test_Prices

    def get_Prices_format(self, symbols, q2d_exchg_symbols, b2d_exchg_symbols, prices):
        """
        standard Prices format
        :param prices:
        :return:
        """
        # get open prices
        open_prices = self._get_specific_from_prices(prices, symbols, ohlc='1000')

        # get the change of close price
        close_prices = self._get_specific_from_prices(prices, symbols, ohlc='0001')
        changes = ((close_prices - close_prices.shift(1)) / close_prices.shift(1)).fillna(0.0)

        # get the change of high price
        high_prices = self._get_specific_from_prices(prices, symbols, ohlc='0100')

        # get the change of low price
        low_prices = self._get_specific_from_prices(prices, symbols, ohlc='0010')

        # get point diff values
        # open_prices = _get_specific_from_prices(prices, symbols, ohlc='1000')
        points_dff_values_df = pointsModel.get_points_dff_values_df(symbols, close_prices, close_prices.shift(periods=1), self.mt5Controller.all_symbols_info)

        # get the quote to deposit exchange rate
        exchg_close_prices = self._get_specific_from_prices(prices, q2d_exchg_symbols, ohlc='0001')
        q2d_exchange_rate_df = exchgModel.get_exchange_df(symbols, q2d_exchg_symbols, exchg_close_prices, self.deposit_currency, "q2d")

        # get the base to deposit exchange rate
        exchg_close_prices = self._get_specific_from_prices(prices, b2d_exchg_symbols, ohlc='0001')
        b2d_exchange_rate_df = exchgModel.get_exchange_df(symbols, b2d_exchg_symbols, exchg_close_prices, self.deposit_currency, "b2d")

        # assign the column into each collection tuple
        Prices = self.Prices_Collection(o=open_prices,
                                        h=high_prices,
                                        l=low_prices,
                                        c=close_prices,
                                        cc=changes,
                                        ptDv=points_dff_values_df,
                                        quote_exchg=q2d_exchange_rate_df,
                                        base_exchg=b2d_exchange_rate_df)

        return Prices

    def get_latest_Prices_format(self, symbols, q2d_exchg_symbols, prices, count):
        """
        this format as simple as possible
        """
        close_prices = self._get_specific_from_prices(prices, symbols, ohlc='0001')
        if len(close_prices) != count:  # note 63a
            print("prices_df length of Data is not equal to count")
            return False

        # calculate the change of close price (with latest close prices)
        change_close_prices = ((close_prices - close_prices.shift(1)) / close_prices.shift(1)).fillna(0.0)

        # get point diff values with latest value
        points_dff_values_df = pointsModel.get_points_dff_values_df(symbols, close_prices, close_prices.shift(periods=1), self.mt5Controller.all_symbols_info)

        # get quote exchange with values
        exchg_close_prices = self._get_specific_from_prices(prices, q2d_exchg_symbols, ohlc='0001')
        q2d_exchange_rate_df = exchgModel.get_exchange_df(symbols, q2d_exchg_symbols, exchg_close_prices, self.deposit_currency, "q2d")
        # if len(q2d_exchange_rate_df_o) or len(q2d_exchange_rate_df_c) == 39, return false and run again
        if len(q2d_exchange_rate_df) != count:  # note 63a
            print("q2d_exchange_rate_df_o or q2d_exchange_rate_df_c length of Data is not equal to count")
            return False

        Prices = self.latest_Prices_Collection(c=close_prices,
                                               cc=change_close_prices,
                                               ptDv=points_dff_values_df,
                                               quote_exchg=q2d_exchange_rate_df)

        return Prices

    def get_historical_data(self, symbol, timeframe, start, end=None):
        """
        :param symbol: str
        :param timeframe: str, '1H'
        :param start (local time): tuple (year, month, day, hour, mins) eg: (2010, 10, 30, 0, 0)
        :param end (local time): tuple (year, month, day, hour, mins), if None, then take data until present
        :return: dataframe
        """
        timeframe = timeModel.get_txt2timeframe(timeframe)
        utc_from = timeModel.get_utc_time_from_broker(start, self.mt5Controller.timezone)
        if end == None:  # if end is None, get the data at current time
            now = datetime.today()
            now_tuple = (now.year, now.month, now.day, now.hour, now.minute)
            utc_to = timeModel.get_utc_time_from_broker(now_tuple, self.mt5Controller.timezone)
        else:
            utc_to = timeModel.get_utc_time_from_broker(end, self.mt5Controller.timezone)
        rates = self.mt5Controller.get_data(symbol, timeframe, utc_from, utc_to)
        rates_frame = pd.DataFrame(rates, dtype=float)  # create DataFrame out of the obtained data
        rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')  # convert time in seconds into the datetime format
        rates_frame = rates_frame.set_index('time')
        return rates_frame

    def get_current_bars(self, symbol, timeframe, count):
        """
        :param symbols: str
        :param timeframe: str, '1H'
        :param count: int
        :return: df
        """
        timeframe = timeModel.get_txt2timeframe(timeframe)
        rates = self.mt5Controller.get_data_from_pos(symbol, timeframe, 0, count)  # 0 means the current bar
        rates_frame = pd.DataFrame(rates, dtype=float)
        rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')
        rates_frame = rates_frame.set_index('time')
        return rates_frame

    def get_mt5_prices(self, required_symbols, timeframe, start, end, latest, count, ohlc='1111'):
        """
        :param required_symbols: [str]
        :param timeframe: str, '1H'
        :param timezone: str "Hongkong"
        :param start: (2010,1,1,0,0), if both start and end is None, use function get_current_bars()
        :param end: (2020,1,1,0,0), if just end is None, get the historical data from date to current
        :param ohlc: str, eg: '1111'
        :param count: int, for get_current_bar_function()
        :return: pd.DataFrame
        """
        join = 'outer'
        required_types = self._price_type_from_code(ohlc)
        prices_df = None
        for i, symbol in enumerate(required_symbols):
            if latest:  # get the latest units of data
                price = self.get_current_bars(symbol, timeframe, count).loc[:, required_types]
                join = 'inner'  # if getting count, need to join=inner to check if data getting completed
            elif not latest and start != None:  # get data from start to end
                price = self.get_historical_data(symbol, timeframe, start, end).loc[:, required_types]
            else:
                raise Exception('start-date must be set when end-date is being set.')
            if i == 0:
                prices_df = price.copy()
            else:
                prices_df = pd.concat([prices_df, price], axis=1, join=join)

        # replace NaN values with preceding values
        prices_df.fillna(method='ffill', inplace=True)
        prices_df.dropna(inplace=True, axis=0)

        # get prices in dict
        prices = self._prices_df2dict(prices_df, required_symbols, ohlc)

        return prices

    def get_local_prices(self, required_symbols, data_time_difference_to_UTC, ohlc):
        """
        :param required_symbols: [str]
        :param data_time_difference_to_UTC: int
        :param timeframe: str, eg: '1H', '1min'
        :param ohlc: str, eg: '1001'
        :return: pd.DataFrame
        """
        prices_df = pd.DataFrame()
        for i, symbol in enumerate(required_symbols):
            print("Processing: {}".format(symbol))
            price_df = fileModel.read_symbol_price(self.local_data_path, symbol, data_time_difference_to_UTC, ohlc=ohlc)
            if i == 0:
                prices_df = price_df.copy()
            else:
                # join='outer' method with all symbols in a bigger dataframe (axis = 1)
                prices_df = pd.concat([prices_df, price_df], axis=1, join='outer')  # because of 1 minute data and for ensure the completion of data, concat in join='outer' method

        # replace NaN values with preceding values
        prices_df.fillna(method='ffill', inplace=True)
        prices_df.dropna(inplace=True, axis=0)

        # get prices in dict
        prices = self._prices_df2dict(prices_df, required_symbols, ohlc)

        return prices

    def get_data(self, symbols, q2d_exchg_symbols, b2d_exchg_symbols, timeframe, local, start, end, latest=False, count=40):
        # read data in dictionary format
        prices, min_prices = {}, {}
        required_symbols = list(set(symbols + q2d_exchg_symbols + b2d_exchg_symbols))
        self._check_if_symbols_available(required_symbols, local) # if not, raise Exception
        # get data from local / mt5
        if local:
            min_prices = self.get_local_prices(required_symbols, self.data_time_difference_to_UTC, '1111')
            # change the timeframe if needed
            if timeframe != '1min':  # 1 minute data should not modify, saving the computation cost
                for symbol in required_symbols:
                    prices[symbol] = self._change_timeframe(min_prices[symbol], timeframe)
            # self.min_Prices = self.get_Prices_format(symbols, q2d_exchg_symbols, b2d_exchg_symbols, min_prices)
        else:
            prices = self.get_mt5_prices(required_symbols, timeframe, start, end, latest, count, '1111')
        # format the Prices depend on latest or not
        if not latest:
            Prices = self.get_Prices_format(symbols, q2d_exchg_symbols, b2d_exchg_symbols, prices) # completed format
        else:
            Prices = self.get_latest_Prices_format(symbols, q2d_exchg_symbols, prices, count) # faster and simple format
        return Prices