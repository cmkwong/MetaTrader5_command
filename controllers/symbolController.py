import MetaTrader5 as mt5
import collections

class SymbolController:
    def __init__(self):
        pass

    def get_all_symbols_info(self):
        """
        :return: dict[symbol] = collections.nametuple
        """
        symbols_info = {}
        symbols = mt5.symbols_get()
        for symbol in symbols:
            symbol_name = symbol.name
            symbols_info[symbol_name] = collections.namedtuple("info", ['digits', 'base', 'quote', 'swap_long', 'swap_short', 'pt_value'])
            symbols_info[symbol_name].digits = symbol.digits
            symbols_info[symbol_name].base = symbol.currency_base
            symbols_info[symbol_name].quote = symbol.currency_profit
            symbols_info[symbol_name].swap_long = symbol.swap_long
            symbols_info[symbol_name].swap_short = symbol.swap_short
            if symbol_name[3:] == 'JPY':
                symbols_info[symbol_name].pt_value = 100  # 100 dollar for quote per each point    (See note Stock Market - Knowledge - note 3)
            else:
                symbols_info[symbol_name].pt_value = 1  # 1 dollar for quote per each point  (See note Stock Market - Knowledge - note 3)
        return symbols_info

    def get_symbol_info(self, symbol):
        return mt5.symbol_info(symbol)

    def get_symbol_total(self):
        """
        :return: int: number of symbols
        """
        num_symbols = mt5.symbols_total()
        if num_symbols > 0:
            print("Total symbols: ", num_symbols)
        else:
            print("Symbols not found.")
        return num_symbols

    def get_symbols(self, group=None):
        """
        :param group: https://www.mql5.com/en/docs/integration/python_metatrader5/mt5symbolsget_py, refer to this website for usage of group
        :return: tuple(symbolInfo), there are several property
        """
        if group:
            symbols = mt5.symbols_get(group)
        else:
            symbols = mt5.symbols_get()
        return symbols