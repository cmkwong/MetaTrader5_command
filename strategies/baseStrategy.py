import os
import pandas as pd
import collections

from models import exchgModel, returnModel, fileModel
from utils import tools
import config

class BaseStrategy:
    def __init__(self, strategy_id, symbols, timeframe, start, end, dataLoader, debug=False, local=False, percentage=0.8, long_mode=True):
        self.strategy_id = strategy_id

        # data
        self.symbols = symbols
        self.timeframe = timeframe
        self.local = local
        self.start = start
        self.end = end
        self.dataLoader = dataLoader
        self.long_mode = long_mode

        # debug
        self.debug = debug  # Boolean, if True output the debug file

        # prepare
        self.q2d_exchg_symbols = exchgModel.get_exchange_symbols(symbols, dataLoader.mt5Controller.all_symbols_info, dataLoader.deposit_currency, 'q2d')
        self.b2d_exchg_symbols = exchgModel.get_exchange_symbols(symbols, dataLoader.mt5Controller.all_symbols_info, dataLoader.deposit_currency, 'b2d')
        self.Prices = dataLoader.get_data(self.symbols, self.q2d_exchg_symbols, self.b2d_exchg_symbols, self.timeframe, self.local, self.start, self.end)
        self.train_Prices, self.test_Prices = dataLoader.split_Prices(self.Prices, percentage)

        # define the path
        self.setup_base_paths()

    def _get_graph_data(self, Prices, signal, coefficient_vector):
        Graph_Data = collections.namedtuple("Graph_Data", ["modify_exchg_q2d",
                                                           "ret", "earning",
                                                           "accum_ret", "accum_earning",
                                                           "ret_list", "earning_list",
                                                           "stat"])
        # prepare q2d
        modify_exchg_q2d = exchgModel.get_exchg_by_signal(Prices.quote_exchg, signal)

        # prepare data for graph ret and earning
        ret, earning = returnModel.get_ret_earning(Prices.c, Prices.c.shift(1), modify_exchg_q2d, Prices.ptDv, coefficient_vector, long_mode=self.long_mode)
        ret_by_signal, earning_by_signal = returnModel.get_ret_earning_by_signal(ret, earning, signal)
        accum_ret, accum_earning = returnModel.get_accum_ret_earning(ret_by_signal, earning_by_signal)

        # prepare data for graph histogram
        ret_list, earning_list = returnModel.get_ret_earning_list(ret_by_signal, earning_by_signal, signal)

        # prepare stat
        stat = tools.get_stat(ret_list, earning_list)

        # assigned to Graph_Data
        Graph_Data.modify_exchg_q2d = modify_exchg_q2d
        Graph_Data.ret, Graph_Data.earning = ret, earning
        Graph_Data.accum_ret, Graph_Data.accum_earning = accum_ret, accum_earning
        Graph_Data.ret_list, Graph_Data.earning_list = ret_list, earning_list
        Graph_Data.stat = stat
        return Graph_Data

    def get_numeric_debug(self, Prices, Graph_Data, strategy_data, signal, accum_ret_df, accum_earning_df, train_test):
        df_debug = pd.DataFrame(index=Prices.c.index)
        df_debug = pd.concat([df_debug, Prices.c, Graph_Data.modify_exchg_q2d, Prices.ptDv,
                              strategy_data, signal,
                              Graph_Data.ret, accum_ret_df,
                              Graph_Data.earning, accum_earning_df
                              ], axis=1)
        debug_file = "{}-numeric".format(train_test)
        df_debug.to_csv(os.path.join(self.debug_path, debug_file))

    def setup_base_paths(self):
        strategy_record_path = os.path.join(config.RECORDS_PATH, self.strategy_id)
        self.debug_path = fileModel.create_dir(strategy_record_path, 'debugs')
        self.train_save_path = fileModel.create_dir(strategy_record_path, 'trains')
        self.test_save_path = fileModel.create_dir(strategy_record_path, 'tests')

    # def get_plt_datas(self, **args):
    #     raise NotImplementedError("Please Implement this method")
    #
    # def train(self):
    #     raise NotImplementedError("Please Implement this method")