from models import exchgModel, returnModel
from utils import tools
import collections

class BaseStrategy:
    def __init__(self, symbols, dataLoader, debug_path, debug_file, debug, long_mode=None):
        self.symbols = symbols
        self.dataLoader = dataLoader
        self.long_mode = long_mode

        # debug file
        self.debug_path = debug_path
        self.debug_file = debug_file
        self.debug = debug  # Boolean, if True output the debug file

        # prepare
        self.q2d_exchg_symbols = exchgModel.get_exchange_symbols(symbols, dataLoader.all_symbols_info, dataLoader.deposit_currency, 'q2d')
        self.b2d_exchg_symbols = exchgModel.get_exchange_symbols(symbols, dataLoader.all_symbols_info, dataLoader.deposit_currency, 'b2d')

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

    # def get_plt_datas(self, **args):
    #     raise NotImplementedError("Please Implement this method")
    #
    # def train(self):
    #     raise NotImplementedError("Please Implement this method")