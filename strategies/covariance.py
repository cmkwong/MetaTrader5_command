import numpy as np
import pandas as pd

from strategies.baseStrategy import BaseStrategy

class Covariance(BaseStrategy):
    def __int__(self, dataLoader, symbols, timeframe, local, start, end,
                long_mode, percentage=0.8,
                debug_path='', debug_file='', debug=False):
        super(Covariance, self).__init__(symbols, timeframe, start, end, dataLoader, debug_path, debug_file, debug, local, percentage, long_mode)

    def get_cov_matrix(self, array_2d, rowvar=False, bias=False):
        matrix = np.cov(array_2d, rowvar=rowvar, bias=bias)
        return matrix

    def get_corela_matrix(self, array_2d, rowvar=False, bias=False):
        matrix = np.corrcoef(array_2d, rowvar=rowvar, bias=bias)
        return matrix

    def get_corela_table(self, cor_matrix, symbol_list):
        cor_table = pd.DataFrame(cor_matrix, index=symbol_list, columns=symbol_list)
        return cor_table

    def get_cor_matrix(self, prices_loader, local):
        """
        :param prices_loader: class object: Prices_Loader
        :param local: Boolean
        :return:
        """
        Prices = prices_loader.get_Prices_format(local)
        price_matrix = Prices.cc.values  # note 83i
        corela_matrix = self.get_corela_matrix(price_matrix)
        corela_table = self.get_corela_table(corela_matrix, self.symbols)
        return corela_matrix, corela_table