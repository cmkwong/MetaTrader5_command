import pandas as pd
import numpy as np
import os

import config

def _get_names_and_usecols(ohlc):
    """
    note 84e
    :param ohlc: str, eg: '1001'
    :return:    names, [str], names assigned to columns
                usecols, int that column will be used
    """
    type_names = ['open', 'high', 'low', 'close']
    names = ['time']
    usecols = [0]
    for i, code in enumerate(ohlc):
        if code == '1':
           names.append(type_names[i])
           usecols.append(i+1)
    return names, usecols

def read_MyCSV(symbol_path, file_name, data_time_difference_to_UTC, names, usecols):
    """
    the timezone is Eastern Standard Time (EST) time-zone WITHOUT Day Light Savings adjustments
    :param symbol_path: str
    :param file_name: str
    :param time_difference_in_hr: time difference between current broker
    :param ohlc: str, eg: '1001'
    :return: pd.DataFrame
    """
    shifted_hr = config.BROKER_TIME_BETWEEN_UTC + data_time_difference_to_UTC
    full_path = os.path.join(symbol_path, file_name)
    df = pd.read_csv(full_path, header=None, names=names, usecols=usecols)
    df.set_index('time', inplace=True)
    df.index = pd.to_datetime(df.index).shift(shifted_hr, freq='H')
    return df

def read_symbol_price(data_path, symbol, data_time_difference_to_UTC, ohlc='1001'):
    """
    :param main_path: str, file path that contains several minute excel data
    :param data_time_difference_to_UTC: int, the time difference between downloaded data and broker
    :param timeframe: str, '1H'
    :param ohlc: str, '1001'
    :return: pd.DataFrame, symbol_prices
    """
    symbol_prices = None
    names, usecols = _get_names_and_usecols(ohlc)
    symbol_path = os.path.join(data_path, symbol)
    min_data_names = get_file_list(symbol_path)
    # concat a symbol in a dataframe (axis = 0)
    for file_count, file_name in enumerate(min_data_names):
        df = read_MyCSV(symbol_path, file_name, data_time_difference_to_UTC, names, usecols)
        if file_count == 0:
            symbol_prices = df.copy()
        else:
            symbol_prices = pd.concat([symbol_prices, df], axis=0)
    # drop the duplicated index row
    symbol_prices = symbol_prices[~symbol_prices.index.duplicated(keep='first')]  # note 80b and note 81c
    return symbol_prices

def write_min_extra_info(main_path, file_name, symbols, long_signal, short_signal, long_modify_exchg_q2d, short_modify_exchg_q2d):
    """
    :param main_path: str
    :param file_name: str
    :param symbols: list
    :param long_signal: pd.Series
    :param short_signal: pd.Series
    :param long_modify_exchg_q2d: pd.DataFrame
    :param short_modify_exchg_q2d: pd.DataFrame
    :return: None
    """
    # concat the data axis=1
    df_for_min = pd.concat([long_signal, short_signal, long_modify_exchg_q2d, short_modify_exchg_q2d], axis=1)
    # re-name
    level_2_arr = np.array(['long', 'short'] + symbols * 2)
    level_1_arr = np.array(['signal'] * 2 + ['long_q2d'] * len(symbols) + ['short_q2d'] * len(symbols))
    df_for_min.columns = [level_1_arr, level_2_arr]
    df_for_min.to_csv(os.path.join(main_path, file_name))
    print("Extra info write to {}".format(main_path))

def read_min_extra_info(main_path):
    """
    :param main_path: str
    :param col_list: list, [str/int]: required column names
    :return: Series, Series, DataFrame, DataFrame
    """
    file_names = get_file_list(main_path, reverse=True)
    dfs = None
    for i, file_name in enumerate(file_names):
        full_path = os.path.join(main_path, file_name)
        df = pd.read_csv(full_path, header=[0, 1], index_col=0)
        if i == 0:
            dfs = df.copy()
        else:
            dfs = pd.concat([dfs, df], axis=0)
    # di-assemble into different parts
    long_signal = dfs.loc[:, ('signal', 'long')]
    short_signal = dfs.loc[:, ('signal', 'short')]
    long_q2d = dfs.loc[:, ('long_q2d')]
    short_q2d = dfs.loc[:, ('short_q2d')]
    return long_signal, short_signal, long_q2d, short_q2d

def transfer_all_xlsx_to_csv(main_path):
    """
    note 84d
    :param main_path: str, the xlsx files directory
    :return:
    """
    files = get_file_list(main_path, reverse=False)
    for file in files:

        # read excel file
        excel_full_path = os.path.join(main_path, file)
        print("Reading the {}".format(file))
        df = pd.read_excel(excel_full_path, header=None)

        # csv file name
        csv_file = file.split('.')[0] + '.csv'
        csv_full_path = os.path.join(main_path, csv_file)
        print("Writing the {}".format(csv_file))
        df.to_csv(csv_full_path, encoding='utf-8', index=False, header=False)

    return True

def get_file_list(files_path, reverse=False):
    """
    :param files_path: str, data_path + symbol
    :param symbol: str
    :return: list
    """
    list_dir = os.listdir(files_path)
    list_dir = sorted(list_dir, reverse=reverse)
    return list_dir

def clear_files(main_path):
    # clear before write
    for file in get_file_list(main_path):
        remove_full_path = os.path.join(main_path, file)
        os.remove(remove_full_path)
        print("The file {} has been removed.".format(file))

def create_dir(main_path, dir_name, readme=None):
    """
    Create directory with readme.txt
    """
    path = os.path.join(main_path, dir_name)
    os.mkdir(path)
    if readme:
        with open(os.path.join(path, 'readme.txt'), 'a') as f:
            f.write(readme)