import numpy as np
from statsmodels.tsa.stattools import adfuller
import collections
import pandas as pd

def z_col(col):
    mean = np.mean(col)
    std = np.std(col)
    normalized_col = (col - mean) / std
    return normalized_col

def z_score(x):
    z = (x - np.mean(x)) / np.std(x)
    return z

def z_score_with_rolling_mean2(spread, fast_mean=3, slow_mean=20, std_window=20):
    """
    :param spread: array, shape = (total_len, )
    :param window: int
    :return: np.array
    """
    spread = spread.reshape(-1, )
    slow_rolling_mean = pd.Series(spread.reshape(-1, )).rolling(slow_mean).mean()
    fast_rolling_mean = pd.Series(spread.reshape(-1, )).rolling(fast_mean).mean()
    rolling_std = pd.Series(spread.reshape(-1, )).rolling(std_window).std()
    z = (np.array(fast_rolling_mean) - np.array(slow_rolling_mean)) / np.array(rolling_std)
    return z

def z_score_with_rolling_mean(spread, mean_window, std_window):
    """
    :param spread: array, shape = (total_len, )
    :param window: int
    :return: np.array
    """
    spread = spread.reshape(-1, )
    rolling_mean = pd.Series(spread.reshape(-1, )).rolling(mean_window).mean()
    rolling_std = pd.Series(spread.reshape(-1, )).rolling(std_window).std()
    z = (spread - np.array(rolling_mean)) / np.array(rolling_std)
    return z

def perform_ADF_test(x):
    adf_result = collections.namedtuple("adf_result", ["test_statistic", "pvalue", "critical_values"])
    result = adfuller(x)
    adf_result.test_statistic = result[0]
    adf_result.pvalue = result[1]
    adf_result.critical_values = result[4]
    return adf_result

def run_regression_LA(input, target):
    """
    Linear Algebra: matrix operation
    :param input: array, size = (total_len, )
    :param target: array, size = (total_len, )
    :return: coefficient
    """
    A = np.concatenate((np.ones((len(input), 1), dtype=float), input.reshape(len(input), -1)), axis=1)
    b = target.reshape(-1, 1)
    A_T_A = np.dot(np.transpose(A), A)
    A_T_b = np.dot(np.transpose(A), b)
    coefficient_vector = np.dot(np.linalg.inv(A_T_A), A_T_b)
    return coefficient_vector