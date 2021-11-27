import numpy as np
import pandas as pd

class validator:
    def __init__(self, env, net, save_path, comission):
        self.env = env
        self.net = net
        self.save_path = save_path
        self.comission = comission

    def preparation(self, step_idx):
        self._total_count = 0
        self.stats = {
            'episode_reward': [],
            'episode_steps': [],
            'order_profits': [],
            'order_steps': []
        }
        columns_list = ['episode', 'open_date', 'open_position_price', 'close_date', 'close_position_price', 'order_steps', 'order_profits']
        self.df = pd.DataFrame(columns=columns_list)
        self.path_csv = self.save_path + "/record_" + str(step_idx) + ".csv"
        # date for that env
        self.date = self.env._state.date

    def update_df_open(self):
        self.df.loc[self._total_count, 'open_date'] = self.date[self.env._state._offset]
        self.df.loc[self._total_count, 'open_position_price'] = self.openPos_price

    def update_df_close(self, episode):
        self.df.loc[self._total_count, 'episode'] = episode
        self.df.loc[self._total_count, 'close_date'] = self.date[self.env._state._offset]
        self.df.loc[self._total_count, 'close_position_price'] = self.curr_action_price
        self.df.loc[self._total_count, 'order_steps'] = self.order_steps
        self.df.loc[self._total_count, 'order_profits'] = self.order_profits
        self._total_count += 1

    def run(self, episodes, step_idx, epsilon):
        self.preparation(step_idx)

        for episode in range(episodes):
            obs = self.env.reset()

            self.episode_reward = 0.0
            self.openPos_price = 0.0
            self.order_steps = 0
            self.have_position = False
            self.episode_steps = 0

            while True:
                obs_v = [obs]
                out_v = self.net(obs_v)

                action_idx = out_v.max(dim=1)[1].item()
                if np.random.random() < epsilon:
                    action_idx = np.random.randint(len(self.env._state.actions))

                self.curr_action_price = self.env._state.action_price[self.env._state._offset]  # base_offset = 8308

                if (action_idx == self.env._state.actions['open']) and not self.have_position:
                    self.openPos_price = self.curr_action_price
                    # store the data
                    self.update_df_open()

                elif (action_idx == self.env._state.actions['close']) and self.have_position:
                    self.order_profits = self.env._state.cal_profit(self.openPos_price, self.env._state.quote_exchg[self.env._state._offset])
                    self.stats['order_profits'].append(self.order_profits)
                    self.stats['order_steps'].append(self.order_steps)
                    # store the data
                    self.update_df_close(episode)

                    # reset the value
                    self.order_steps = 0
                    self.have_position = False

                obs, reward, done, _ = self.env.step(action_idx)
                self.episode_reward += reward
                self.episode_steps += 1
                if self.have_position: self.order_steps += 1
                if done:
                    if self.have_position:
                        self.order_profits = self.env._state.cal_profit(self.openPos_price, self.env._state.quote_exchg[self.env._state._offset])
                        self.stats['order_profits'].append(self.order_profits)
                        self.stats['order_steps'].append(self.order_steps)

                        # store the data (have not sell yet but reached end-date)
                        self.update_df_close(episode)
                    break
            self.stats['episode_reward'].append(self.episode_reward)
            self.stats['episode_steps'].append(self.episode_steps)

            # export the csv files
        self.df.to_csv(self.path_csv, index=False)
        return self.stats