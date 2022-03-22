import pandas as pd
import numpy as np
import os
import seaborn as sns
from matplotlib import pyplot as plt
from models import timeModel
from selfUtils import maths

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

def _get_format_plot_data(df=None, hist=None, text=None, equation=None, height=2):
    """
    :param df: pd.DataFrame
    :param hist: pd.Series
    :param text: str
    :param equation: str
    :param height: int
    :return: dictionary
    """
    plt_data = {}
    plt_data['df'] = df
    plt_data['hist'] = hist
    plt_data['text'] = text
    plt_data['equation'] = equation
    plt_data['height'] = height
    return plt_data

def get_total_height(plt_datas):
    # graph proportion
    total_height = 0
    for plt_data in plt_datas.values():
        total_height += plt_data['height']
    return total_height

def get_plot_title(start, end, timeframe_str, local):
    # end_str
    start_str = timeModel.get_time_string(start)
    if end != None:
        end_str = timeModel.get_time_string(end)
    else:
        end_str = timeModel.get_current_time_string()
    # local/mt5
    if local:
        source = 'local'
    else:
        source = 'mt5'
    title = "{} : {}, timeframe={}, source={}".format(start_str, end_str, timeframe_str, source)
    return title

def get_coin_NN_plot_image_name(dt_str, symbols, episode):
    symbols_str = ''
    for symbol in symbols:
        symbols_str += '_' + symbol
    name = "{}-{}-episode-{}.jpg".format(dt_str, episode, symbols_str)
    return name

def get_spread_plt_datas(spreads):
    """
    :param spreads: pd.DataFrame
    :return: plt_data, nested dict
    """
    i = 0
    plt_data = {}
    for symbol in spreads.columns:
        plt_data[i] = _get_format_plot_data(df=pd.DataFrame(spreads[symbol]), text="mean: {:.2f} pt\nstd: {:.2f} pt".format(np.mean(spreads[symbol]), np.std(spreads[symbol]))) # np.mean(pd.Series) will ignore the nan value, note 56c
        i += 1
        plt_data[i] = _get_format_plot_data(hist=spreads[symbol])
        i += 1
    return plt_data

def append_all_df_debug(df_list):
    # [Prices.c, Prices.o, points_dff_values_df, coin_signal, int_signal, changes, ret_by_signal]
    prefix_names = ['open', 'pt_diff_values', 'q2d', 'b2d', 'ret', 'plt_data', 'signal', 'int_signal', 'earning', 'earning_by_signal']
    all_df = None
    for i, df in enumerate(df_list):
        df.columns = [(col_name + '_' + prefix_names[i]) for col_name in df.columns]
        if i == 0:
            all_df = pd.DataFrame(df.values, index=df.index, columns=df.columns)
        else:
            all_df = pd.concat([all_df, df], axis=1, join='inner')
    return all_df

def get_ADF_text_result(spread):
    """
    :param spread: np.array
    :return:
    """
    text = ''
    result = maths.perform_ADF_test(spread)
    text += "The test statistic: {:.6f}\n".format(result.test_statistic)
    text += "The p-value: {:.6f}\n".format(result.pvalue)
    text += "The critical values: \n"
    for key, value in result.critical_values.items():
        text += "     {} = {:.6f}\n".format(key, value)
    return text

def get_stat_text_condition(stats, required_type):
    """
    :param stat: including the long and short stat
    :param required_type: str 'earning' / 'ret'
    :return: str, only for required type
    """
    txt = ''
    for mode, types in stats.items():  # long or short
        txt += "{}:\n".format(mode)
        for type, stat in types.items():  # count, accuracy, (return / earning)
            if type == required_type:
                txt += "  {}:\n".format(type)
                for key, value in stat.items():  # stat dict
                    txt += "    {}:{:.5f}\n".format(key, value)
    return txt

def get_setting_txt(setting_dict):
    setting = 'Setting: \n'
    for key, value in setting_dict.items():
        # for nested dictionary (Second level)
        if type(value) == dict:
            setting += "{}: \n".format(key)
            for k, v in value.items():
                setting += "  {}: {}\n".format(k, v)
        # if only one level of dictionary
        else:
            setting += "{}: {}\n".format(key, value)
    return setting

def save_plot(train_plt_data, test_plt_data, symbols, episode, saved_path, dt_str, dpi=500, linewidth=0.2, title=None,
              figure_size=(28, 12), fontsize=9, bins=100, setting='', hist_range=None):
    """
    :param setting:
    :param bins:
    :param train_plt_data: {pd.Dataframe}
    :param test_plt_data: {pd.Dataframe}
    :param symbols: [str]
    :param saved_path: str, file to be saved
    :param episode: int
    :param dt_str: str
    :param dpi: resolution of image
    :param linewidth: line width in plots
    :param figure_size: tuple to indicate the size of figure
    :param show_inputs: Boolean
    """
    # prepare figure
    fig = plt.figure(figsize=figure_size, dpi=dpi)
    fig.suptitle(title, fontsize=fontsize*4)
    plt.figtext(0.1,0.9, setting, fontsize=fontsize*2)
    gs = fig.add_gridspec(get_total_height(train_plt_data), 1)  # slice into grid with different size
    # for histogram range
    if hist_range != None: hist_range = (hist_range[0]+1, hist_range[1]-1) # exclude the range, see note (51a)

    # graph list
    for i in range(len(train_plt_data)):

        # subplot setup
        grid_step = train_plt_data[i]['height']  # height for each grid
        plt.subplot(gs[(i * grid_step):(i * grid_step + grid_step), :])

        # dataframe
        if test_plt_data == None:
            if type(train_plt_data[i]['df']) == pd.DataFrame:
                df = train_plt_data[i]['df']
                for col_name in df.columns:
                    plt.plot(df.index, df[col_name].values, linewidth=linewidth, label=col_name)
        else:
            if type(train_plt_data[i]['df']) == pd.DataFrame and type(test_plt_data[i]['df']) == pd.DataFrame:
                df = pd.concat([train_plt_data[i]['df'], test_plt_data[i]['df']], axis=0)
                for col_name in df.columns:
                    plt.plot(df.index, df[col_name].values, linewidth=linewidth, label=col_name)

        # histogram (pd.Series)
        if test_plt_data == None:
            if type(train_plt_data[i]['hist']) == pd.Series:
                plt.hist(train_plt_data[i]['hist'], bins=bins, label="{} {}".format("Train", train_plt_data[i]['hist'].name), range=hist_range)
        else:
            if type(train_plt_data[i]['hist']) == pd.Series and type(test_plt_data[i]['hist']) == pd.Series:
                plt.hist(train_plt_data[i]['hist'], bins=bins, label="{} {}".format("Train", train_plt_data[i]['hist'].name), range=hist_range)
                plt.hist(test_plt_data[i]['hist'], bins=bins, label="{} {}".format("Test", test_plt_data[i]['hist'].name), range=hist_range)

        # text
        if test_plt_data == None:
            if type(train_plt_data[i]['text']) == str:
                train_start_index = train_plt_data[i]['df'].index[0]
                plt.text(train_start_index, df.iloc[:, 0].quantile(0.01), "Train \n" + train_plt_data[i]['text'], fontsize=fontsize * 0.7)
        else:
            if type(train_plt_data[i]['text']) == str and type(test_plt_data[i]['text']) == str:
                train_start_index, test_start_index = train_plt_data[i]['df'].index[0], test_plt_data[0]['df'].index[0]
                plt.text(train_start_index, df.iloc[:,0].quantile(0.01), "Train \n" + train_plt_data[i]['text'], fontsize=fontsize*0.7)   # calculate the quantile 0.1 to get the y-position
                plt.text(test_start_index, df.iloc[:,0].quantile(0.01), "Test \n" + test_plt_data[i]['text'], fontsize=fontsize*0.7)     # calculate the quantile 0.1 to get the y-position

        # equation
        if type(train_plt_data[i]['equation']) == str:
            plt.text(train_plt_data[i]['df'].index.mean(), df.iloc[:,0].quantile(0.1), train_plt_data[i]['equation'], fontsize=fontsize*2)

        plt.legend()

    full_path = os.path.join(saved_path, get_coin_NN_plot_image_name(dt_str, symbols, episode))
    plt.savefig(full_path)  # save in higher resolution image
    plt.clf()                                                                              # clear the plot data

def density(ret_list, bins=50, color="darkblue", linewidth=1):
    """
    :param ret_list: list
    :param bins: int
    :param color: str
    :param linewidth: int
    :return: None
    """
    sns.distplot(ret_list, hist=True, kde=True,
                 bins=bins, color=color,
                 hist_kws={'edgecolor': 'black'},
                 kde_kws={'linewidth': linewidth})
    plt.show()