from models import exchgModel, returnModel
from utils import tools
import collections

class BaseStrategy:
    def __init__(self, Prices):
        self.Prices = Prices

    def _get_graph_data(self, long_signal, short_signal, coefficient_vector):
        Graph_Data = collections.namedtuple("Graph_Data", ["long_modify_exchg_q2d", "short_modify_exchg_q2d",
                                                           "long_ret", "long_earning",
                                                           "long_accum_ret", "long_accum_earning",
                                                           "short_ret", "short_earning",
                                                           "short_accum_ret", "short_accum_earning",
                                                           "long_ret_list", "long_earning_list",
                                                           "short_ret_list", "short_earning_list",
                                                           "stats"])
        # prepare q2d
        long_modify_exchg_q2d = exchgModel.get_exchg_by_signal(self.Prices.quote_exchg, long_signal)
        short_modify_exchg_q2d = exchgModel.get_exchg_by_signal(self.Prices.quote_exchg, short_signal)

        # prepare data for graph ret and earning
        long_ret, long_earning = returnModel.get_ret_earning(self.Prices.c, self.Prices.c.shift(1), long_modify_exchg_q2d, self.Prices.ptDv, coefficient_vector, long_mode=True)
        long_ret_by_signal, long_earning_by_signal = returnModel.get_ret_earning_by_signal(long_ret, long_earning, long_signal)
        long_accum_ret, long_accum_earning = returnModel.get_accum_ret_earning(long_ret_by_signal, long_earning_by_signal)

        short_ret, short_earning = returnModel.get_ret_earning(self.Prices.c, self.Prices.c.shift(1), short_modify_exchg_q2d, self.Prices.ptDv, coefficient_vector, long_mode=False)
        short_ret_by_signal, short_earning_by_signal = returnModel.get_ret_earning_by_signal(short_ret, short_earning, short_signal)
        short_accum_ret, short_accum_earning = returnModel.get_accum_ret_earning(short_ret_by_signal, short_earning_by_signal)

        # prepare data for graph histogram
        long_ret_list, long_earning_list = returnModel.get_ret_earning_list(long_ret_by_signal, long_earning_by_signal, long_signal)
        short_ret_list, short_earning_list = returnModel.get_ret_earning_list(short_ret_by_signal, short_earning_by_signal, short_signal)

        # prepare stat
        stats = tools.get_stats(long_ret_list, long_earning_list, short_ret_list, short_earning_list)

        # assigned to Graph_Data
        Graph_Data.long_modify_exchg_q2d, Graph_Data.short_modify_exchg_q2d = long_modify_exchg_q2d, short_modify_exchg_q2d
        Graph_Data.long_ret, Graph_Data.long_earning = long_ret, long_earning
        Graph_Data.long_accum_ret, Graph_Data.long_accum_earning = long_accum_ret, long_accum_earning
        Graph_Data.short_ret, Graph_Data.short_earning = short_ret, short_earning
        Graph_Data.short_accum_ret, Graph_Data.short_accum_earning = short_accum_ret, short_accum_earning
        Graph_Data.long_ret_list, Graph_Data.long_earning_list = long_ret_list, long_earning_list
        Graph_Data.short_ret_list, Graph_Data.short_earning_list = short_ret_list, short_earning_list
        Graph_Data.stats = stats
        return Graph_Data

    def get_plt_datas(self, **args):
        raise NotImplementedError("Please Implement this method")

    def train(self):
        raise NotImplementedError("Please Implement this method")