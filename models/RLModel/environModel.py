from models import pointsModel, returnModel, techModel
from selfUtils import tools

import numpy as np
import pandas as pd

class State:
    def __init__(self, symbol, close_price, quote_exchg, dependent_datas, date, time_cost_pt, commission_pt, spread_pt, lot_times, long_mode, all_symbols_info,
                 reset_on_close):
        self.symbol = symbol
        self.action_price = close_price  # close price (pd.DataFrame)
        self.quote_exchg = quote_exchg  # quote to deposit (pd.DataFrame)
        self.dependent_datas = dependent_datas  # should be shift 1 forward, because it takes action on next-day of open-price (pd.DataFrame)
        self.date = date
        self.time_cost_pt = time_cost_pt
        self.commission_pt = commission_pt
        self.spread_pt = spread_pt
        self.lot_times = lot_times  # normally it is 1
        self.long_mode = long_mode
        self.all_symbols_info = all_symbols_info
        self.reset_on_close = reset_on_close
        self._init_action_space()

        self.deal_step = 0.0  # step counter from buy to sell (buy date = step 1, if sell date = 4, time cost = 3)

    def reset(self, new_offset):
        self._offset = new_offset
        self.have_position = False

    def _init_action_space(self):
        self.actions = {}
        self.actions['skip'] = 0
        self.actions['open'] = 1
        self.actions['close'] = 2
        self.action_space = list(self.actions.values())
        self.action_space_size = len(self.action_space)

    def cal_profit(self, curr_action_price, q2d_at):
        modified_coefficient_vector = returnModel.get_modified_coefficient_vector(np.array([]), self.long_mode, self.lot_times)
        return returnModel.get_value_of_earning(self.symbol, curr_action_price, self._prev_action_price, q2d_at, self.all_symbols_info, modified_coefficient_vector)

    def encode(self):
        # encoded_data = collections.namedtuple('encoded_data', field_names=['date', 'open_price', 'dependent_datas'])
        # encoded_data.date = self.open_price.iloc[self._offset].index
        # encoded_data.open_price = self.open_price.iloc[self._offset].values
        # encoded_data.dependent_datas = self.dependent_datas.iloc[self._offset].values
        res = []
        earning = 0.0
        res.extend(list(self.dependent_datas.iloc[self._offset, :].values))
        if self.have_position:
            earning = self.cal_profit(self.action_price.iloc[self._offset, :].values, self.quote_exchg.iloc[self._offset, :].values)
        res.extend([earning, float(self.have_position)])  # earning, have_position (True = 1.0, False = 0.0)
        return np.array(res, dtype=np.float32)

    def step(self, action):
        """
        :param action: long/short * Open/Close/hold position: 6 actions
        :return: reward, done
        """
        done = False
        reward = 0.0  # in deposit USD
        curr_action_price = self.action_price.iloc[self._offset].values[0]
        q2d_at = self.quote_exchg.iloc[self._offset].values[0]

        if action == self.actions['open'] and not self.have_position:
            reward -= pointsModel.get_point_to_deposit(self.symbol, self.spread_pt, q2d_at, self.all_symbols_info)  # spread cost
            self.openPos_price = curr_action_price
            self.have_position = True

        elif action == self.actions['close'] and self.have_position:
            reward += self.cal_profit(curr_action_price, q2d_at)  # calculate the profit
            reward -= pointsModel.get_point_to_deposit(self.symbol, self.time_cost_pt, q2d_at, self.all_symbols_info)  # time cost
            reward -= pointsModel.get_point_to_deposit(self.symbol, self.spread_pt, q2d_at, self.all_symbols_info)  # spread cost
            reward -= pointsModel.get_point_to_deposit(self.symbol, self.commission_pt, q2d_at, self.all_symbols_info)  # commission cost
            self.have_position = False

        elif action == self.actions['skip'] and self.have_position:
            reward += self.cal_profit(curr_action_price, q2d_at)
            reward -= pointsModel.get_point_to_deposit(self.symbol, self.time_cost_pt, q2d_at, self.all_symbols_info)  # time cost
            self.deal_step += 1

        # update status
        self._prev_action_price = curr_action_price
        self._offset += 1
        if self._offset >= len(self.action_price) - 1:
            done = True

        return reward, done

class TechicalForexEnv:
    def __init__(self, symbol, Prices, tech_params, long_mode, all_symbols_info, time_cost_pt, commission_pt, spread_pt, lot_times, random_ofs_on_reset, reset_on_close):
        self.Prices = Prices
        self.tech_params = tech_params  # pd.DataFrame
        self.dependent_datas = pd.concat([self._get_tech_df(), Prices.o, Prices.h, Prices.l, Prices.c], axis=1, join='outer').fillna(0)
        self._state = State(symbol, Prices.c, Prices.quote_exchg, self.dependent_datas, Prices.c.index,
                            time_cost_pt, commission_pt, spread_pt, lot_times, long_mode, all_symbols_info, reset_on_close)
        self.random_ofs_on_reset = random_ofs_on_reset

    def _get_tech_df(self):
        tech_df = pd.DataFrame()
        for tech_name in self.tech_params.keys():
            data = techModel.get_tech_datas(self.Prices, self.tech_params[tech_name], tech_name)
            tech_df = tools.append_dict_df(data, tech_df, join='outer', filled=0)
        return tech_df

    def get_obs_len(self):
        obs = self.reset()
        return len(obs)

    def get_action_space_size(self):
        return self._state.action_space_size

    def reset(self):
        if not self.random_ofs_on_reset:
            self._state.reset(0)
        else:
            random_offset = np.random.randint(len(self.Prices.o))
            self._state.reset(random_offset)
        obs = self._state.encode()
        return obs

    def step(self, action):
        reward, done = self._state.step(action)
        obs = self._state.encode()
        return obs, reward, done
