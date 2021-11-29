import numpy as np
import os
from models import returnModel

def shift_list(lst, s):
    s %= len(lst)
    s *= -1
    shifted_lst = lst[s:] + lst[:s]
    return shifted_lst

def get_accuracy(values, th=0.0):
    """
    :param values: listclose_price_with_last_tick
    :param th: float
    :return: float
    """
    accuracy = np.sum([c > th for c in values]) / len(values)
    return accuracy

def append_dictValues_into_text(dic, txt=''):
    values = list(dic.values())
    txt += ','.join([str(value) for value in values]) + '\n'
    return txt

def dic_into_text(dic):
    text = ''
    for k, v in dic.items():
        text += "{}: {}\n".format(str(k), str(v))
    return text

def find_required_path(path, target):
    while(True):
        head, tail = os.path.split(path)
        if tail == target:
            return path
        path = head

def get_stat(ret_list, earning_list):
    """
    :param ret_list: []
    :param earning_list: []
    :return:
    """
    stat = {}
    total_ret, total_earning = returnModel.get_total_ret_earning(ret_list, earning_list)
    # earning
    stat['earning'] = {}
    stat['earning']['count'] = len(earning_list)
    stat['earning']["accuracy"] = get_accuracy(earning_list, 0.0) # calculate the accuracy separately, note 46a
    stat['earning']["total"] = total_earning
    stat['earning']["mean"] = np.mean(earning_list)
    stat['earning']["max"] = np.max(earning_list)
    stat['earning']["min"] = np.min(earning_list)
    stat['earning']["std"] = np.std(earning_list)

    # return
    stat['ret'] = {}
    stat['ret']['count'] = len(earning_list)
    stat['ret']["accuracy"] = get_accuracy(ret_list, 1.0) # calculate the accuracy separately, note 46a
    stat['ret']["total"] = total_ret
    stat['ret']["mean"] = np.mean(ret_list)
    stat['ret']["max"] = np.max(ret_list)
    stat['ret']["min"] = np.min(ret_list)
    stat['ret']["std"] = np.std(ret_list)

    return stat

def get_stats(long_ret_list, long_earning_list, short_ret_list, short_earning_list):
    """
    get stats both for long and short
    :param Prices: collections nametuple object
    :param long_signal: pd.Series
    :param short_signal: pd.Series
    :param coefficient_vector: np.array, raw coefficient
    :param slsp: tuple(stop loss (negative), stop profit (positive))
    :return: dictionary
    """
    stats = {}
    stats['long'] = get_stat(long_ret_list, long_earning_list)
    stats['short'] = get_stat(short_ret_list, short_earning_list)
    return stats

def split_df(df, percentage):
    split_index = int(len(df) * percentage)
    upper_df = df.iloc[:split_index,:]
    lower_df = df.iloc[split_index:, :]
    return upper_df, lower_df

def split_matrix(arr, percentage=0.8, axis=0):
    """
    :param arr: np.array() 2D
    :param percentage: float
    :param axis: float
    :return: split array
    """
    cutOff = int(arr.shape[axis] * percentage)
    max = arr.shape[axis]
    I = [slice(None)] * arr.ndim
    I[axis] = slice(0, cutOff)
    upper_arr = arr[tuple(I)]
    I[axis] = slice(cutOff, max)
    lower_arr = arr[tuple(I)]
    return upper_arr, lower_arr

def append_dict_df(dict_df, mother_df, join='outer', filled=0):
    """
    :param mother_df: pd.DataFrame
    :param join: 'inner', 'outer'
    :param dict_df: {key: pd.DataFrame}
    :return: pd.DataFrame after concat
    """
    if not isinstance(mother_df, pd.DataFrame):
        mother_df = pd.DataFrame()
    for df in dict_df.values(): # do not care the key name: tech name
        if mother_df.empty:
            mother_df = df.copy()
        else:
            mother_df = pd.concat([mother_df, df], axis=1, join=join)
    return mother_df.fillna(filled)
