import numpy as np
import pandas as pd
from strategies.baseStrategy import BaseStrategy
from models import signalModel
from views import plotView, printout
from utils import tools
import os

class MovingAverage(BaseStrategy):
    def __init__(self, Prices, limit_unit, max_index):
        super(MovingAverage, self).__init__(Prices)
        self.Prices = Prices
        self.limit_unit = limit_unit
        self.max_index = max_index

    def get_signal(self, long_ma_data, short_ma_data, train=True):
        long_signal = pd.Series(long_ma_data['fast'] > long_ma_data['slow'], index=long_ma_data.index)
        short_signal = pd.Series(short_ma_data['fast'] < short_ma_data['slow'], index=short_ma_data.index)
        if train:
            long_signal = signalModel.discard_head_tail_signal(long_signal)  # see 40c
            short_signal = signalModel.discard_head_tail_signal(short_signal)
        if self.limit_unit > 0:
            long_signal = signalModel.maxLimitClosed(long_signal, self.limit_unit)
            short_signal = signalModel.maxLimitClosed(short_signal, self.limit_unit)
        return long_signal, short_signal

    def get_moving_average(self, closes, m_value, normalized=True):
        """
        :param closes: pd.DataFrame
        :param m_value: int
        :param normalized: boolean, the non-normalized value average by close price
        :return: pd.DataFrame
        """
        ma = pd.DataFrame(columns=closes.columns, index=closes.index)
        for symbol in closes.columns:
            if normalized:
                ma[symbol] = (closes[symbol].rolling(m_value).sum() / m_value) - closes[symbol]
            else:
                ma[symbol] = closes[symbol].rolling(m_value).sum() / m_value
        return ma

    def get_ma_data(self, close_prices, fast_param, slow_param):
        ma_data = pd.DataFrame(index=close_prices.index)
        ma_data['fast'] = self.get_moving_average(close_prices, fast_param)
        ma_data['slow'] = self.get_moving_average(close_prices, slow_param)
        return ma_data

    def get_plt_datas(self, long_param, short_param, debug_path, debug_file, debug):
        """
        :param Prices: collections nametuples
        :param long_param: dict ['fast', 'slow']
        :param short_param: dict ['fast', 'slow']
        :return:
        """
        # prepare
        long_ma_data = self.get_ma_data(self.Prices.c, long_param['fast'], long_param['slow'])
        short_ma_data = self.get_ma_data(self.Prices.c, short_param['fast'], short_param['slow'])
        long_signal, short_signal = self.get_signal(long_ma_data, short_ma_data)
        # Get Graph Data
        Graph_Data = self._get_graph_data(long_signal, short_signal, coefficient_vector=np.array([]))

        # -------------------------------------------------------------------- standard graph --------------------------------------------------------------------
        plt_datas = {}
        # 1 graph: close price, fast ma,  slow ma (long)
        long_ma_df = pd.concat([self.Prices.c, long_ma_data['fast'], long_ma_data['slow']], axis=1)
        text = 'Long: \n  fast: {}\n  slow: {}'.format(long_param['fast'], long_param['slow'])
        plt_datas[0] = plotView._get_format_plot_data(df=long_ma_df, text=text)

        # 2 graph: close price, fast ma,  slow ma (short)
        short_ma_df = pd.concat([self.Prices.c, short_ma_data['fast'], short_ma_data['slow']], axis=1)
        text = 'Short: \n  fast: {}\n  slow: {}'.format(short_param['fast'], short_param['slow'])
        plt_datas[1] = plotView._get_format_plot_data(df=short_ma_df, text=text)

        # 3 graph: ret (long and short)
        accum_ret_df = pd.DataFrame(index=self.Prices.c.index)
        accum_ret_df["long_accum_ret"] = Graph_Data.long_accum_ret
        accum_ret_df["short_accum_ret"] = Graph_Data.short_accum_ret
        text = plotView.get_stat_text_condition(Graph_Data.stats, 'ret')
        plt_datas[2] = plotView._get_format_plot_data(df=accum_ret_df, text=text)

        # 4 graph: earning (long and short)
        accum_earning_df = pd.DataFrame(index=self.Prices.c.index)
        accum_earning_df["long_accum_earning"] = Graph_Data.long_accum_earning
        accum_earning_df["short_accum_earning"] = Graph_Data.short_accum_earning
        text = plotView.get_stat_text_condition(Graph_Data.stats, 'earning')
        plt_datas[3] = plotView._get_format_plot_data(df=accum_earning_df, text=text)

        # 5 graph: ret histogram for long
        plt_datas[4] = plotView._get_format_plot_data(hist=pd.Series(Graph_Data.long_ret_list, name='long earning'))

        # 6 graph: ret histogram for short
        plt_datas[5] = plotView._get_format_plot_data(hist=pd.Series(Graph_Data.short_earning_list, name='short earning'))

        # ------------ DEBUG -------------
        df_debug = pd.DataFrame(index=self.Prices.o.index)
        df_debug = pd.concat([df_debug, self.Prices.o, Graph_Data.long_modify_exchg_q2d, Graph_Data.short_modify_exchg_q2d, self.Prices.ptDv,
                              long_ma_data, short_ma_data,
                              long_signal, short_signal,
                              Graph_Data.long_ret, Graph_Data.short_ret, accum_ret_df,
                              Graph_Data.long_earning, Graph_Data.short_earning, accum_earning_df
                              ], axis=1)
        if debug:
            df_debug.to_csv(os.path.join(debug_path, debug_file))
        return plt_datas

    def train(self):
        long_stat_csv_txt, short_stat_csv_txt = '', ''
        long_stat, short_stat = {}, {}
        for slow_index in range(1, self.max_index):
            for fast_index in range(1, slow_index):
                if slow_index == fast_index:
                    continue
                # moving average object
                long_ma_data = self.get_ma_data(self.Prices.c, fast_index, slow_index)
                short_ma_data = self.get_ma_data(self.Prices.c, fast_index, slow_index)
                long_signal, short_signal = self.get_signal(long_ma_data, short_ma_data)

                Graph_Data = self._get_graph_data(long_signal, short_signal, coefficient_vector=np.array([]))

                # stat for both long and short (including header)
                long_stat = Graph_Data.stats['long']['earning']
                short_stat = Graph_Data.stats['short']['earning']
                long_stat['limit_unit'], long_stat['slow'], long_stat['fast'] = self.limit_unit, slow_index, fast_index
                short_stat['limit_unit'], short_stat['slow'], short_stat['fast'] = self.limit_unit, slow_index, fast_index

                if long_stat["total"] > 0: long_stat_csv_txt = tools.append_dict_into_text(long_stat, long_stat_csv_txt)
                if short_stat["total"] > 0: short_stat_csv_txt = tools.append_dict_into_text(short_stat, short_stat_csv_txt)

                # # print results
                print("\nlimit unit: {}; slow index: {}; fast index: {}".format(self.limit_unit, slow_index, fast_index))
                printout.print_dict(long_stat)
                printout.print_dict(short_stat)
        # added to header to the text
        long_stat_csv_txt = ','.join(list(long_stat.keys())) + '\n' + long_stat_csv_txt
        short_stat_csv_txt = ','.join(list(short_stat.keys())) + '\n' + short_stat_csv_txt
        return long_stat_csv_txt, short_stat_csv_txt

    def run(self, fast_index, slow_index):
        # moving average object
        long_ma_data = self.get_ma_data(self.Prices.c, fast_index, slow_index)
        short_ma_data = self.get_ma_data(self.Prices.c, fast_index, slow_index)
        long_signal, short_signal = self.get_signal(long_ma_data, short_ma_data, train=False)