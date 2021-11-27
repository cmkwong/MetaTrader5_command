import numpy as np
import pandas as pd
import os

from models import signalModel, exchgModel, returnModel
from views import plotView
from utils import maths, tools
from strategies.baseStrategy import BaseStrategy

class Cointegration(BaseStrategy):
    def __int__(self, dataLoader, symbols, timeframe, local, start, end,
                change_of_close, long_mode, threshold, z_score_mean_window, z_score_std_window, percentage=0.8,
                debug_path='', debug_file='', debug=False):
        super(Cointegration, self).__init__(symbols, timeframe, start, end, dataLoader, debug_path, debug_file, debug, local, percentage, long_mode)

        # training
        self.change_of_close = change_of_close # False: using close price; True: using change of close price
        self.long_mode = long_mode
        self.threshold = threshold
        self.z_score_mean_window = z_score_mean_window
        self.z_score_std_window = z_score_std_window
        self.coefficient_vector = None

    def get_strategy_id(self, train_options):
        id = 'coin'
        for key, value in train_options.items():
            id += str(value)
        if self.long_mode:
            id += 'long'
        else:
            id += 'short'
        return id

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

    def get_signal(self, coin_data, training=True):
        """
        this function can available for coinNN and coin model
        :param coin_NN_data: pd.Dataframe(), columns='real','predict','spread','z_score'
        :param upper_th: float
        :param lower_th: float
        :return: pd.Series()
        """
        if self.long_mode:
            signal = pd.Series(coin_data['z_score'].values < self.threshold, index=coin_data.index, name='signal')
        else:
            signal = pd.Series(coin_data['z_score'].values > self.threshold, index=coin_data.index, name='signal')
        if training:
            signal = signalModel.discard_head_tail_signal(signal)  # see 40c
        return signal

    def get_coin_data(self, inputs):
        """
        :param inputs: accept the train and test prices in pd.dataframe format
        :param coefficient_vector:
        :return:
        """
        coin_data = pd.DataFrame(index=inputs.index)
        coin_data['real'] = inputs.iloc[:, -1]
        coin_data['predict'] = self.get_predicted_arr(inputs.iloc[:, :-1].values, self.coefficient_vector)
        spread = coin_data['real'] - coin_data['predict']
        coin_data['spread'] = spread
        coin_data['z_score'] = maths.z_score_with_rolling_mean(spread.values, self.z_score_mean_window, self.z_score_std_window)
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

    def train(self):
        dependent_variable = self.train_Prices.c
        if self.change_of_close:
            dependent_variable = self.train_Prices.cc
        self.coefficient_vector = maths.run_regression_LA(input=dependent_variable.values[:, :-1], target=dependent_variable.values[:, -1])

    def get_plt_datas(self):
        """
            :param Prices: collections.nametuple object
            :param threshold: np.float
            :param z_score_mean_window: int
            :param z_score_std_window: int
            :return: nested dictionary
            """
        plt_datas = {}
        for key, Prices in {'train': self.train_Prices, 'test': self.test_Prices}.items():
            # -------------------------------------------------------------------- standard --------------------------------------------------------------------
            dependent_variable = Prices.c
            if self.change_of_close:
                dependent_variable = Prices.cc
            # prepare signal
            coin_data = self.get_coin_data(dependent_variable)  # get_coin_data() can work for coinNN and coin
            signal = self.get_signal(coin_data, training=True)
            # Get Graph Data
            Graph_Data = self._get_graph_data(Prices, signal, self.coefficient_vector)

            # -------------------------------------------------------------------- standard graph --------------------------------------------------------------------
            plt_datas[key] = {}
            # 1 graph: real and predict
            real_predict_df = pd.concat([coin_data['real'], coin_data['predict']], axis=1)
            adf_result_text = plotView.get_ADF_text_result(coin_data['spread'].values)
            equation = self.get_coin_NN_equation_text(dependent_variable.columns, self.coefficient_vector)
            plt_datas[key][0] = plotView._get_format_plot_data(df=real_predict_df, text=adf_result_text, equation=equation)

            # 2 graph: spread
            spread_df = pd.DataFrame(coin_data['spread'], index=dependent_variable.index)
            plt_datas[key][1] = plotView._get_format_plot_data(df=spread_df)

            # 3 graph: z-score
            z_df = pd.DataFrame(coin_data['z_score'], index=dependent_variable.index)
            plt_datas[key][2] = plotView._get_format_plot_data(df=z_df)

            # 4 graph: return
            accum_ret_df = pd.DataFrame(index=dependent_variable.index)
            accum_ret_df["accum_ret"] = Graph_Data.accum_ret
            text = plotView.get_stat_text_condition(Graph_Data.stats, 'ret')
            plt_datas[key][3] = plotView._get_format_plot_data(df=accum_ret_df, text=text)

            # 5 graph: earning
            accum_earning_df = pd.DataFrame(index=dependent_variable.index)
            accum_earning_df["accum_earning"] = Graph_Data.accum_earning
            text = plotView.get_stat_text_condition(Graph_Data.stats, 'earning')
            plt_datas[key][4] = plotView._get_format_plot_data(df=accum_earning_df, text=text)

            # 6 graph: earning histogram
            plt_datas[key][5] = plotView._get_format_plot_data(hist=pd.Series(Graph_Data.earning_list, name='earning'))

            # ------------ DEBUG -------------
            df_debug = pd.DataFrame(index=Prices.c.index)
            df_debug = pd.concat([df_debug, Prices.c, Graph_Data.modify_exchg_q2d, Prices.ptDv, coin_data,
                                  signal,
                                  Graph_Data.ret, accum_ret_df,
                                  Graph_Data.earning, accum_earning_df
                                  ], axis=1)

            if self.debug:
                debug_file = "{}_{}".format(key, self.debug_file)
                df_debug.to_csv(os.path.join(self.debug_path, debug_file))

        return plt_datas['train'], plt_datas['test']

    def run(self, inputs):
        coin_data = self.get_coin_data(inputs)  # get_coin_data() can work for coinNN and coin
        signal = self.get_signal(coin_data, training=False)
        return signal