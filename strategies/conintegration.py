import numpy as np
import pandas as pd
import os

from models import signalModel, exchgModel, returnModel
from views import plotView
from utils import maths, tools
from strategies.baseStrategy import BaseStrategy

class Cointegration(BaseStrategy):
    def __int__(self, Prices, min_Prices, change_of_close):
        super(Cointegration, self).__init__(Prices)
        self.Prices = Prices
        self.min_Prices = min_Prices
        self.change_of_close = change_of_close # False: using close price; True: using change of close price
        self.coefficient_vector = None

    def get_strategy_id(self, train_options):
        id = 'coin'
        for key, value in train_options.items():
            id += str(value)
        long_id = id + 'long'
        short_id = id + 'short'
        return long_id, short_id

    def get_predicted_arr(self, input, coefficient_vector):
        """
        Ax=b
        :param input: array, size = (total_len, feature_size)
        :param coefficient_vector: coefficient vector, size = (feature_size, )
        :return: predicted array
        """
        A = np.concatenate((np.ones((len(input), 1)), input.reshape(len(input), -1)), axis=1)
        b = np.dot(A, coefficient_vector.reshape(-1, 1)).reshape(-1, )
        return b

    def get_signal(self, coin_NN_data, upper_th, lower_th, discard_head_tail=True):
        """
        this function can available for coinNN and coin model
        :param coin_NN_data: pd.Dataframe(), columns='real','predict','spread','z_score'
        :param upper_th: float
        :param lower_th: float
        :return: pd.Series() for long and short
        """
        long_signal = pd.Series(coin_NN_data['z_score'].values < lower_th, index=coin_NN_data.index, name='long_signal')
        short_signal = pd.Series(coin_NN_data['z_score'].values > upper_th, index=coin_NN_data.index, name='short_signal')
        if discard_head_tail:
            long_signal = signalModel.discard_head_tail_signal(long_signal)  # see 40c
            short_signal = signalModel.discard_head_tail_signal(short_signal)
        return long_signal, short_signal

    def get_coin_data(self, inputs, coefficient_vector, mean_window, std_window):
        """
        :param inputs: accept the train and test prices in pd.dataframe format
        :param coefficient_vector:
        :return:
        """
        coin_data = pd.DataFrame(index=inputs.index)
        coin_data['real'] = inputs.iloc[:, -1]
        coin_data['predict'] = self.get_predicted_arr(inputs.iloc[:, :-1].values, coefficient_vector)
        spread = coin_data['real'] - coin_data['predict']
        coin_data['spread'] = spread
        coin_data['z_score'] = maths.z_score_with_rolling_mean(spread.values, mean_window, std_window)
        return coin_data

    def get_coin_NN_equation_text(self, symbols, coefficient_vector):
        """
        :param symbols: [str]
        :param coefficient_vector: np.array
        :return: str
        """
        coefficient_vector = coefficient_vector.reshape(-1, )
        equation = "{:.5f}".format(coefficient_vector[0])
        for i, symbol in enumerate(symbols[:-1]):
            if coefficient_vector[i + 1] >= 0:
                equation += "+{:.5f}[{}]".format(coefficient_vector[i + 1], symbol)
            else:
                equation += "{:.5f}[{}]".format(coefficient_vector[i + 1], symbol)
        equation += " = [{}]".format(symbols[-1])
        return equation

    def get_plt_datas(self, upper_th, lower_th, z_score_mean_window, z_score_std_window, slsp, timeframe, debug_path, debug_file, debug):
        """
            :param Prices: collections.nametuple object
            :param coefficient_vector: np.array
            :param upper_th: np.float
            :param lower_th: np.float
            :param z_score_mean_window: int
            :param z_score_std_window: int
            :param slsp: tuple(stop loss (negative), stop profit (positive))
            :param timeframe: needed when calculating slsp
            :param debug_file: str
            :param debug: Boolean
            :return: nested dictionary
            """
        # -------------------------------------------------------------------- standard --------------------------------------------------------------------
        # prepare signal
        dependent_variable = self.Prices.c
        if self.change_of_close:
            dependent_variable = self.Prices.cc
        coin_data = self.get_coin_data(dependent_variable, self.coefficient_vector, z_score_mean_window, z_score_std_window)  # get_coin_data() can work for coinNN and coin
        long_signal, short_signal = self.get_signal(coin_data, upper_th, lower_th)
        # Get Graph Data
        Graph_Data = self._get_graph_data(long_signal, short_signal, self.coefficient_vector)

        # -------------------------------------------------------------------- standard graph --------------------------------------------------------------------
        plt_datas = {}
        # 1 graph: real and predict
        real_predict_df = pd.concat([coin_data['real'], coin_data['predict']], axis=1)
        adf_result_text = plotView.get_ADF_text_result(coin_data['spread'].values)
        equation = self.get_coin_NN_equation_text(dependent_variable.columns, self.coefficient_vector)
        plt_datas[0] = plotView._get_format_plot_data(df=real_predict_df, text=adf_result_text, equation=equation)

        # 2 graph: spread
        spread_df = pd.DataFrame(coin_data['spread'], index=dependent_variable.index)
        plt_datas[1] = plotView._get_format_plot_data(df=spread_df)

        # 3 graph: z-score
        z_df = pd.DataFrame(coin_data['z_score'], index=dependent_variable.index)
        plt_datas[2] = plotView._get_format_plot_data(df=z_df)

        # 4 graph: return for long and short
        accum_ret_df = pd.DataFrame(index=dependent_variable.index)
        accum_ret_df["long_accum_ret"] = Graph_Data.long_accum_ret
        accum_ret_df["short_accum_ret"] = Graph_Data.short_accum_ret
        text = plotView.get_stat_text_condition(Graph_Data.stats, 'ret')
        plt_datas[3] = plotView._get_format_plot_data(df=accum_ret_df, text=text)

        # 5 graph: earning for long and short
        accum_earning_df = pd.DataFrame(index=dependent_variable.index)
        accum_earning_df["long_accum_earning"] = Graph_Data.long_accum_earning
        accum_earning_df["short_accum_earning"] = Graph_Data.short_accum_earning
        text = plotView.get_stat_text_condition(Graph_Data.stats, 'earning')
        plt_datas[4] = plotView._get_format_plot_data(df=accum_earning_df, text=text)

        # 6 graph: earning histogram for long
        plt_datas[5] = plotView._get_format_plot_data(hist=pd.Series(Graph_Data.long_earning_list, name='long earning'))

        # 7 graph: earning histogram for short
        plt_datas[6] = plotView._get_format_plot_data(hist=pd.Series(Graph_Data.short_earning_list, name='short earning'))

        # ------------ DEBUG -------------
        df_debug = pd.DataFrame(index=self.Prices.c.index)
        df_debug = pd.concat([df_debug, self.Prices.c, Graph_Data.long_modify_exchg_q2d, Graph_Data.short_modify_exchg_q2d, self.Prices.ptDv, coin_data,
                              long_signal, short_signal,
                              Graph_Data.long_ret, Graph_Data.short_ret, accum_ret_df,
                              Graph_Data.long_earning, Graph_Data.short_earning, accum_earning_df
                              ], axis=1)

        # -------------------------------------------------------------------- slsp --------------------------------------------------------------------
        if len(self.min_Prices) != 0:
            # prepare minute data for slsp part
            long_min_signal, short_min_signal = signalModel.get_resoluted_signal(long_signal, self.min_Prices.quote_exchg.index), signalModel.get_resoluted_signal(short_signal, self.min_Prices.quote_exchg.index)
            long_modify_min_exchg_q2d = exchgModel.get_exchg_by_signal(self.min_Prices.quote_exchg, long_signal)
            short_modify_min_exchg_q2d = exchgModel.get_exchg_by_signal(self.min_Prices.quote_exchg, short_signal)
            long_min_ret, long_min_earning = returnModel.get_ret_earning(self.min_Prices.c, self.min_Prices.c.shift(1), long_modify_min_exchg_q2d, self.min_Prices.ptDv, self.coefficient_vector, long_mode=True)
            short_min_ret, short_min_earning = returnModel.get_ret_earning(self.min_Prices.c, self.min_Prices.c.shift(1), short_modify_min_exchg_q2d, self.min_Prices.ptDv, self.coefficient_vector, long_mode=False)

            # prepare data for graph 8 and 9: ret and earning with stop-loss and stop-profit
            long_ret_by_signal_slsp, long_earning_by_signal_slsp = returnModel.get_ret_earning_by_signal(Graph_Data.long_ret, Graph_Data.long_earning, long_signal, long_min_ret, long_min_earning, slsp, timeframe)
            long_accum_ret_slsp, long_accum_earning_slsp = returnModel.get_accum_ret_earning(long_ret_by_signal_slsp, long_earning_by_signal_slsp)
            short_ret_by_signal_slsp, short_earning_by_signal_slsp = returnModel.get_ret_earning_by_signal(Graph_Data.short_ret, Graph_Data.short_earning, short_signal, short_min_ret, short_min_earning, slsp, timeframe)
            short_accum_ret_slsp, short_accum_earning_slsp = returnModel.get_accum_ret_earning(short_ret_by_signal_slsp, short_earning_by_signal_slsp)

            # prepare data for graph 10 and 11
            long_ret_list_slsp, long_earning_list_slsp = returnModel.get_ret_earning_list(long_ret_by_signal_slsp, long_earning_by_signal_slsp, long_signal)
            short_ret_list_slsp, short_earning_list_slsp = returnModel.get_ret_earning_list(short_ret_by_signal_slsp, short_earning_by_signal_slsp, short_signal)

            # prepare stat
            stats_slsp = tools.get_stats(long_ret_list_slsp, long_earning_list_slsp, short_ret_list_slsp, short_earning_list_slsp)

            # -------------------------------------------------------------------- slsp graph --------------------------------------------------------------------
            # 8 graph: ret with stop loss and stop profit for long and short
            accum_ret_slsp = pd.DataFrame(index=dependent_variable.index)
            accum_ret_slsp['long_accum_ret_slsp'] = long_accum_ret_slsp
            accum_ret_slsp['short_accum_ret_slsp'] = short_accum_ret_slsp
            text = plotView.get_stat_text_condition(stats_slsp, 'ret')
            plt_datas[7] = plotView._get_format_plot_data(df=accum_ret_slsp, text=text)

            # 9 graph: earning with stop loss and stop profit for long and short
            accum_earning_slsp = pd.DataFrame(index=dependent_variable.index)
            accum_earning_slsp['long_accum_earning_slsp'] = long_accum_earning_slsp
            accum_earning_slsp['short_accum_earning_slsp'] = short_accum_earning_slsp
            text = plotView.get_stat_text_condition(stats_slsp, 'earning')
            plt_datas[8] = plotView._get_format_plot_data(df=accum_earning_slsp, text=text)

            # 10 graph: earning histogram for long
            plt_datas[9] = plotView._get_format_plot_data(hist=pd.Series(long_earning_list_slsp, name='long earning slsp'))

            # 11 graph: earning histogram for short
            plt_datas[10] = plotView._get_format_plot_data(hist=pd.Series(short_earning_list_slsp, name='short earning slsp'))

            # ------------ slsp DEBUG -------------
            # concat more data if slsp available
            df_debug = pd.concat([df_debug,
                                  long_accum_ret_slsp, short_accum_ret_slsp,
                                  long_accum_earning_slsp, short_accum_earning_slsp], axis=1)
            # for minute data
            range = [150000, 200000]
            df_min_debug = pd.DataFrame(index=self.min_Prices.o.iloc[range[0]:range[1]].index)
            df_min_debug = pd.concat([df_min_debug, self.min_Prices.o.iloc[range[0]:range[1]], long_modify_min_exchg_q2d.iloc[range[0]:range[1]],
                                      short_modify_min_exchg_q2d.iloc[range[0]:range[1]], self.min_Prices.ptDv.iloc[range[0]:range[1]],
                                      long_min_signal.iloc[range[0]:range[1]], short_min_signal.iloc[range[0]:range[1]],
                                      long_min_ret.iloc[range[0]:range[1]], short_min_ret.iloc[range[0]:range[1]],
                                      long_min_earning.iloc[range[0]:range[1]], short_min_earning.iloc[range[0]:range[1]]
                                      ], axis=1)
            if debug:
                df_min_debug.to_csv(os.path.join(debug_path, "min_" + debug_file))
        if debug:
            df_debug.to_csv(os.path.join(debug_path, debug_file))

        return plt_datas

    def train(self):
        dependent_variable = self.Prices.c
        if self.change_of_close:
            dependent_variable = self.Prices.cc
        self.coefficient_vector = maths.run_regression_LA(dependent_variable.values[:, :-1], dependent_variable.values[:, -1])