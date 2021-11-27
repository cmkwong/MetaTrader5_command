import talib
import pandas as pd
import numpy as np

def get_macd(closes, fastperiod, slowperiod, signalperiod):
    """
    :param closes: pd.DataFrame
    :param fastperiod: int
    :param slowperiod: int
    :param signalperiod: int
    :return: pd.DataFrame
    """
    symbols = closes.columns
    # prepare level 2 column name
    level_2_arr = np.array(['value', 'signal', 'hist'] * len(symbols))
    # prepare level 1 column name
    l = []
    for symbol in symbols:
        l.extend([symbol] * 3)
    level_1_arr = np.array(l)
    column_index_arr = [
        level_1_arr, level_2_arr
    ]
    # calculate macd
    macd = pd.DataFrame(columns=column_index_arr, index=closes.index)
    for symbol in closes.columns:
        macd.loc[:,(symbol,'value')], macd.loc[:,(symbol,'signal')], macd.loc[:,(symbol,'hist')] = talib.MACD(closes[symbol], fastperiod, slowperiod, signalperiod)
    return macd

def get_rsi(closes, period, normalized=True):
    """
    :param closes: pd.DataFrame
    :param period: int
    :param normalized: boolean, the non-normalized value is between 0 - 100
    :return: pd.DataFrame
    """
    rsi = pd.DataFrame(columns=closes.columns, index=closes.index)
    for symbol in closes.columns:
        if normalized:
            rsi[symbol] = talib.RSI(closes[symbol], timeperiod=period) / 100
        else:
            rsi[symbol] = talib.RSI(closes[symbol], timeperiod=period)
    return rsi

def get_moving_average(closes, m_value, normalized=True):
    """
    :param closes: pd.DataFrame
    :param m_value: int
    :param normalized: boolean, the non-normalized value average by close price
    :return: pd.DataFrame
    """
    ma = pd.DataFrame(columns=closes.columns, index=closes.index)
    for symbol in closes.columns:
        if normalized:
            ma[symbol] = (closes[symbol].rolling(m_value).sum() / m_value ) - closes[symbol]
        else:
            ma[symbol] = closes[symbol].rolling(m_value).sum() / m_value
    return ma

def get_bollinger_band(closes, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0, normalized=True):
    """
    :param closes: pd.DataFrame
    :param timeperiod: int
    :param nbdevup: int
    :param nbdevdn: int
    :param matype: int, #MA_Type: 0=SMA, 1=EMA, 2=WMA, 3=DEMA, 4=TEMA, 5=TRIMA, 6=KAMA, 7=MAMA, 8=T3 (Default=SMA)
    :param normalized: boolean, the non-normalized value average by close price
    :return: upperband (pd.DataFrame), middleband (pd.DataFrame), lowerband (pd.DataFrame)
    """
    # define 2 level of columns for dataframe
    symbols = closes.columns
    # prepare level 2 column name
    level_2_arr = np.array(['upper', 'middle', 'lower'] * len(symbols))
    # prepare level 1 column name
    l = []
    for symbol in symbols:
        l.extend([symbol] * 3)
    level_1_arr = np.array(l)
    column_index_arr = [
        level_1_arr, level_2_arr
    ]
    # calculate the bb
    bb = pd.DataFrame(columns=column_index_arr, index=closes.index)
    for symbol in closes.columns:
        bb.loc[:,(symbol, 'upper')], bb.loc[:,(symbol,'middle')], bb.loc[:,(symbol, 'lower')] = talib.BBANDS(closes[symbol], timeperiod, nbdevup, nbdevdn, matype)
        if normalized:
            bb.loc[:, (symbol, 'upper')], bb.loc[:, (symbol, 'middle')], bb.loc[:, (symbol, 'lower')] = bb[symbol, 'upper'] - closes[symbol], bb[symbol,'middle'] - closes[symbol], bb[symbol, 'lower'] - closes[symbol]
    return bb

def get_stochastic_oscillator(highs, lows, closes, fastk_period=5, slowk_period=3, slowd_period=3, slowk_matype=0, slowd_matype=0, normalized=True):
    """
    :param highs: pd.DataFrame
    :param lows: pd.DataFrame
    :param closes: pd.DataFrame
    :param fastk_period: int
    :param slowk_period: int
    :param slowd_period: int
    :param slowk_matype: int, MA_Type: 0=SMA, 1=EMA, 2=WMA, 3=DEMA, 4=TEMA, 5=TRIMA, 6=KAMA, 7=MAMA, 8=T3 (Default=SMA)
    :param slowd_matype: int, MA_Type: 0=SMA, 1=EMA, 2=WMA, 3=DEMA, 4=TEMA, 5=TRIMA, 6=KAMA, 7=MAMA, 8=T3 (Default=SMA)
    :param normalized: boolean, the non-normalized value is between 0 - 100
    :return: slowk (pd.DataFrame), slowd (pd.DataFrame)
    """
    # define 2 level of columns for dataframe
    symbols = closes.columns
    # prepare level 2 column name
    level_2_arr = np.array(['k', 'd'] * len(symbols))
    # prepare level 1 column name
    l = []
    for symbol in symbols:
        l.extend([symbol] * 2)
    level_1_arr = np.array(l)
    column_index_arr = [
        level_1_arr, level_2_arr
    ]
    # calculate stochastic oscillator
    stocOsci = pd.DataFrame(columns=column_index_arr, index=closes.index)
    for symbol in closes.columns:
        stocOsci.loc[:,(symbol,'k')], stocOsci.loc[:,(symbol,'d')] = talib.STOCH(highs[symbol], lows[symbol], closes[symbol], fastk_period, slowk_period, slowk_matype, slowd_period, slowd_matype)
        if normalized:
            stocOsci.loc[:, (symbol, 'k')], stocOsci.loc[:, (symbol, 'd')] = stocOsci[symbol, 'k'] / 100, stocOsci[symbol, 'd'] / 100
    return stocOsci

def get_standard_deviation(closes, timeperiod, nbdev=0):
    """
    :param closes: pd.DataFrame
    :param timeperiod: int
    :param nbdev: int,
    :return: pd.DataFrame
    """
    std = pd.DataFrame(columns=closes.columns, index=closes.index)
    for symbol in closes.columns:
        std[symbol] = talib.STDDEV(closes[symbol], timeperiod, nbdev)
    return std

def get_tech_datas(Prices, params, tech_name):
    """
    :param Prices: collection object
    :param params: {'ma': [param]}
    :param tech_name: str
    :return:
    """
    datas = {}
    for param in params:
        if tech_name == 'ma':
            datas[param] = get_moving_average(Prices.c, param)
        elif tech_name == 'bb':
            datas[param] = get_bollinger_band(Prices.c, *param)
        elif tech_name == 'std':
            datas[param] = get_standard_deviation(Prices.c, *param)
        elif tech_name == 'rsi':
            datas[param] = get_rsi(Prices.c, param)
        elif tech_name == 'stocOsci':
            datas[param] = get_stochastic_oscillator(Prices.h, Prices.l, Prices.c, *param)
        elif tech_name == 'macd':
            datas[param] = get_macd(Prices.c, *param)
    return datas
