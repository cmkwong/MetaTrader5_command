import pandas as pd
from datetime import timedelta

def find_target_index(series, target, step=1, numeric=False):
    """
    :param series: pd.Series, index can be any types of index
    :param target: int (the value need to find)
    :return: list
    """
    start_index = []
    start_index.extend([get_step_index_by_index(series, index, step, numeric) for index in series[series == target].index])  # see note point 6 why added by 1
    return start_index

def get_step_index_by_index(series, curr_index, step, numeric=False):
    """
    :param series: pd.Series, pd.DataFrame
    :param curr_index: index
    :param step: int, +/-
    :return: index
    """
    if numeric:
        required_index = series.index.get_loc(curr_index) + step
    else:
        required_index = series.index[series.index.get_loc(curr_index) + step]
    return required_index

def simple_limit_end_index(starts, ends, limit_unit):
    """
    modify the ends_index, eg. close the trade until specific unit
    :param starts: list [int] index
    :param ends: list [int] index
    :return: starts, ends
    """
    new_starts_index, new_ends_index = [], []
    for s, e in zip(starts, ends):
        new_starts_index.append(s)
        new_end = min(s + limit_unit, e)
        new_ends_index.append(new_end)
    return new_starts_index, new_ends_index

def discard_head_tail_signal(signal):
    """
    :param signal: pd.Series
    :return: signal: pd.Series
    """
    # head
    if signal[0] == True:
        for index, value in signal.items():
            if value == True:
                signal[index] = False
            else:
                break

    # tail
    last_tailed_index = 3   # See Note 6. and 11., why -3 note 90a issue 2
    length = len(signal)
    for start in range(1, last_tailed_index+1):
        if signal[len(signal) - start] == True:
            for ii, value in enumerate(reversed(signal.iloc[:length - start + 1].values)):
                if value == True:
                    signal[length - start - ii] = False
                else:
                    break
    return signal

def get_start_end_index(signal, step=1, numeric=False):
    """
    :param signal: pd.Series
    :return: list: start_index, end_index
    """
    int_signal = get_int_signal(signal)
    # buy index
    start_index = find_target_index(int_signal, 1, step=step, numeric=numeric)
    # sell index
    end_index = find_target_index(int_signal, -1, step=step, numeric=numeric)
    return start_index, end_index

def get_int_signal(signal):
    """
    :param signal: pd.Series()
    :return: pd.Series(), int_signal
    """
    int_signal = signal.astype(int).diff(1)
    return int_signal

def maxLimitClosed(signal, limit_unit):
    """
    :param signal(backtesting): pd.Series [Boolean]
    :param limit_unit: int
    :return: modified_signal: pd.Series
    """
    # assert signal[0] != True, "Signal not for backtesting"
    # assert signal[len(signal) - 1] != True, "Signal not for backtesting"
    # assert signal[len(signal) - 2] != True, "Signal not for backtesting"

    int_signal = get_int_signal(signal)
    signal_starts = [i for i in find_target_index(int_signal.reset_index(drop=True), target=1, step=0)]
    signal_ends = [i for i in find_target_index(int_signal.reset_index(drop=True), target=-1, step=0)]
    starts, ends = simple_limit_end_index(signal_starts, signal_ends, limit_unit)

    # assign new signal
    signal.iloc[:] = False
    for s, e in zip(starts, ends):
        signal.iloc[s:e] = True
    return signal

def get_resoluted_signal(signal, index):
    """
    :param signal: pd.Series
    :param index: pd.DateTimeIndex / str in time format
    :param freq_step: the time step in hour
    :return:
    """
    # resume to datetime index
    signal.index = pd.to_datetime(signal.index)
    index = pd.to_datetime(index)

    # get int signal and its start_indexes and end_indexes
    start_indexes, end_indexes = get_start_end_index(signal, step=0)
    # start_indexes = pd.to_datetime(signal[signal==True].index)
    # end_indexes = pd.to_datetime(signal[signal==True].index).shift(freq_step, freq='H').shift(-1, freq='min') # note 82e

    # init the empty signal series
    resoluted_signal = pd.Series(False, index=index)
    for s, e in zip(start_indexes, end_indexes):
        e = e + timedelta(minutes=-1) # note 82e, use the timedelta to reduce 1 minute instead of shift()
        resoluted_signal.loc[s:e] = True
    return resoluted_signal