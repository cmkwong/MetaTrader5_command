import numpy as np
import pandas as pd

from strategies.baseStrategy import BaseStrategy
from models import signalModel, techModel
from views import plotView, printout
from utils import tools
from models.paramModel import SymbolList, InputBoolean

class MovingAverage(BaseStrategy):
    def __init__(self, dataLoader, *,
                 symbols:SymbolList, timeframe:str, local:InputBoolean, start:str, end:str, limit_unit:int, max_index:int, long_mode:InputBoolean,
                 fast_param=None, slow_param=None, percentage=0.8,
                 debug_path='', debug_file='', debug=False):
        super(MovingAverage, self).__init__(symbols, timeframe, start, end, dataLoader, debug_path, debug_file, debug, local, percentage, long_mode)

        # training
        self.fast_param = fast_param
        self.slow_param = slow_param
        self.limit_unit = limit_unit
        self.max_index = max_index
        self.long_mode = long_mode

    def setup_model(self, fast_param, slow_param):
        self.fast_param = fast_param
        self.slow_param = slow_param
        print("setup ok")

    def get_signal(self, ma_data, training=True):
        if self.long_mode:
            signal = pd.Series(ma_data['fast'] > ma_data['slow'], index=ma_data.index)
        else:
            signal = pd.Series(ma_data['fast'] < ma_data['slow'], index=ma_data.index)
        if training:
            signal = signalModel.discard_head_tail_signal(signal)  # see 40c
        if self.limit_unit > 0:
            signal = signalModel.maxLimitClosed(signal, self.limit_unit)
        return signal

    def get_ma_data(self, close_prices, fast_param=None, slow_param=None):
        if fast_param and slow_param:
            fast, slow = fast_param, slow_param
        else:
            fast, slow = self.fast_param, self.slow_param
        ma_data = pd.DataFrame(index=close_prices.index)
        ma_data['fast'] = techModel.get_moving_average(close_prices, fast)
        ma_data['slow'] = techModel.get_moving_average(close_prices, slow)
        return ma_data

    def train(self):
        stat_csv_txt = ''
        stat = {}
        for slow_index in range(1, self.max_index):
            for fast_index in range(1, slow_index):
                if slow_index == fast_index:
                    continue
                # moving average object
                ma_data = self.get_ma_data(self.train_Prices.c, fast_index, slow_index)
                signal, short_signal = self.get_signal(ma_data, training=True)

                Graph_Data = self._get_graph_data(self.train_Prices, signal, coefficient_vector=np.array([]))

                # stat
                stat = Graph_Data.stat['earning'] # that is dictionary
                stat['limit_unit'], stat['slow'], stat['fast'] = self.limit_unit, slow_index, fast_index

                if stat["total"] > 0: stat_csv_txt = tools.append_dictValues_into_text(stat, stat_csv_txt)

                # # print results
                print("\nlimit unit: {}; slow index: {}; fast index: {}".format(self.limit_unit, slow_index, fast_index))
                printout.print_dict(stat)
        # added to header to the text
        stat_csv_txt = ','.join(list(stat.keys())) + '\n' + stat_csv_txt
        return stat_csv_txt

    def get_plt_datas(self):
        if self.fast_param == None or self.slow_param == None:
            print("The parameter have not set yet.\nType -setup to setup the parameter.")
            return False

        plt_datas = {}
        for train_test, Prices in {'train': self.train_Prices, 'test': self.test_Prices}.items():
            # prepare
            ma_data = self.get_ma_data(Prices.c)
            signal = self.get_signal(ma_data, training=True)
            # Get Graph Data
            Graph_Data = self._get_graph_data(Prices, signal, coefficient_vector=np.array([]))

            # -------------------------------------------------------------------- standard graph --------------------------------------------------------------------
            plt_datas[train_test] = {}
            # 1 graph: close price, fast ma,  slow ma
            ma_df = pd.concat([Prices.c, ma_data['fast'], ma_data['slow']], axis=1)
            if self.long_mode:
                text = 'Long: \n  fast: {}\n  slow: {}'.format(self.fast_param, self.slow_param)
            else:
                text = 'short: \n  fast: {}\n  slow: {}'.format(self.fast_param, self.slow_param)
            plt_datas[train_test][0] = plotView._get_format_plot_data(df=ma_df, text=text)

            # 3 graph: ret
            accum_ret_df = pd.DataFrame(index=Prices.c.index)
            accum_ret_df["accum_ret"] = Graph_Data.accum_ret
            text = plotView.get_stat_text_condition(Graph_Data.stats, 'ret')
            plt_datas[train_test][1] = plotView._get_format_plot_data(df=accum_ret_df, text=text)

            # 4 graph: earning
            accum_earning_df = pd.DataFrame(index=Prices.c.index)
            accum_earning_df["accum_earning"] = Graph_Data.accum_earning
            text = plotView.get_stat_text_condition(Graph_Data.stats, 'earning')
            plt_datas[train_test][2] = plotView._get_format_plot_data(df=accum_earning_df, text=text)

            # 5 graph: ret histogram
            plt_datas[train_test][3] = plotView._get_format_plot_data(hist=pd.Series(Graph_Data.ret_list, name='ret'))

            # ------------ DEBUG -------------
            if self.debug:
                self.get_debug(Prices, Graph_Data, ma_data, signal, accum_ret_df, accum_earning_df, train_test)

        return plt_datas['train'], plt_datas['test']

    def run(self, inputs):
        ma_data = self.get_ma_data(inputs)
        signal = self.get_signal(ma_data, training=False)
        return signal