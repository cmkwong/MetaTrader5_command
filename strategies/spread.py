import pandas as pd
import numpy as np

from strategies.baseStrategy import BaseStrategy
from views import plotView

class Spread(BaseStrategy):
    def __init__(self, symbols, timeframe, start, end, dataLoader):
        super(Spread, self).__init__(symbols, timeframe, start, end, dataLoader)

    def get_spread_plt_datas(self, spreads):
        """
        :param spreads: pd.DataFrame
        :return: plt_data, nested dict
        """
        i = 0
        plt_data = {}
        for symbol in spreads.columns:
            text = "mean: {:.2f} pt\nstd: {:.2f} pt".format(np.mean(spreads[symbol]), np.std(spreads[symbol]))
            plt_data[i] = plotView._get_format_plot_data(df=pd.DataFrame(spreads[symbol]), text=text)  # np.mean(pd.Series) will ignore the nan value,
            # note 56c
            i += 1
            plt_data[i] = plotView._get_format_plot_data(hist=spreads[symbol])
            i += 1
        return plt_data

    def get_plt_datas(self):
        spreads = self.dataLoader.get_spreads(self.symbols, self.start, self.end)
        plt_datas = self.get_spread_plt_datas(spreads)
        return plt_datas