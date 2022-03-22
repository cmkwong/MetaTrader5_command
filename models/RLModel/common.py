import sys
import os
import re
import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

def unpack_batch(batch):
    states, actions, rewards, dones, last_states = [], [], [], [], []
    for exp in batch:
        states.append(exp.state)
        actions.append(exp.action)
        rewards.append(exp.reward)
        dones.append(exp.last_state is None)
        if exp.last_state is None:
            last_states.append(exp.state)       # the result will be masked anyway
        else:
            last_states.append(exp.last_state)
    return states, np.array(actions), np.array(rewards, dtype=np.float32), \
           np.array(dones, dtype=np.uint8), last_states

def find_stepidx(text, open_str, end_str):
    regex_open = re.compile(open_str)
    regex_end = re.compile(end_str)
    matches_open = regex_open.search(text)
    matches_end = regex_end.search(text)
    return np.int(text[matches_open.span()[1]:matches_end.span()[0]])

class netPreprocessor:
    def __init__(self, net, tgt_net):
        self.net = net
        self.tgt_net = tgt_net

    def train_mode(self, batch_size):
        self.net.train()
        self.net.zero_grad()
        # self.net.init_hidden(batch_size)

        self.tgt_net.eval()
        # self.tgt_net.init_hidden(batch_size)

    def eval_mode(self, batch_size):
        self.net.eval()
        # self.net.init_hidden(batch_size)

    def populate_mode(self, batch_size):
        self.net.eval()
        # self.net.init_hidden(batch_size)

def weight_visualize(net, writer):
    for name, param in net.named_parameters():
        writer.add_histogram(name, param)

def valid_result_visualize(stats=None, writer=None, step_idx=None):

    # output the mean reward to the writer
    for key, vals in stats.items():
        if (len(vals) > 0):
            mean_value = np.mean(vals)
            std_value = np.std(vals, ddof=1)
            writer.add_scalar("val_" + key, mean_value, step_idx)
            writer.add_scalar("std_val_" + key, std_value, step_idx)
            if (key == 'order_profits') or (key == 'episode_reward'):
                writer.add_histogram("1_dist_val_" + key, np.array(vals))
        else:
            writer.add_scalar("val_" + key, 0, step_idx)
            writer.add_scalar("std_val_" + key, 0, step_idx)
            if (key == 'order_profits') or (key == 'episode_reward'):
                writer.add_histogram("1_dist_val_" + key, 0)

class monitor:
    def __init__(self, buffer, save_path):
        self.buffer = buffer
        self.save_path = save_path

    def unpack(self, exps):
        dates = []
        rewards = []
        actions = []
        for exp in exps:
            dates.append(exp.state.date)
            actions.append(exp.action)
            rewards.append(exp.reward)
        return dates, actions, rewards

    def generate_into_df(self, monitor_size):
        samples = self.buffer.sample(monitor_size)
        dates, actions, rewards = self.unpack(samples)
        dates_sr = pd.Series(dates, name="date")
        actions_sr = pd.Series(actions, name="action")
        rewards_sr = pd.Series(rewards, name="reward")
        df = pd.concat([dates_sr, actions_sr, rewards_sr], axis=1)
        return df

    def out_csv(self, monitor_size, step_idx):
        path_csv = os.path.join(self.save_path, "buffer_{}.csv".format(str(step_idx)))
        df = self.generate_into_df(monitor_size)
        df.to_csv(path_csv, index=False)