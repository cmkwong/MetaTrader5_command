import os
import numpy as np
import torch
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter

from strategies.baseStrategy import BaseStrategy
from strategies.nnStrategy import NNStrategy
from models.RLModel import NNModel, environModel, common

from nn.rl import Agents, Actions, Experiences, Validations, Rewards, Losses
from utils.paramType import SymbolList, Tech_Dict, InputBoolean

class SimpleRL(BaseStrategy, NNStrategy):
    def __init__(self, dataLoader, strategy_id, *,
                 symbols:SymbolList, timeframe:str, local:InputBoolean, start:str, end:str, tech_params:Tech_Dict, lr:float, batch_size:int, epsilon_start:float, epsilon_end:float,
                 gamma:float, reward_steps:int, replay_size:int, monitor_buffer_size:int, replay_start:int, epsilon_step:int, target_net_sync:int, validation_step:int,
                 checkpoint_step:int, weight_visualize_step:int, buffer_monitor_step:int, validation_episodes:int, long_mode:InputBoolean,
                 percentage=0.8,
                 net_saved_path='', net_file = '', debug=False):
        BaseStrategy.__init__(self, strategy_id, symbols, timeframe, start, end, dataLoader, debug, local, percentage, long_mode)
        NNStrategy.__init__(self, strategy_id)

        # training
        self.step_idx = 0
        self.tech_params = tech_params
        self.lr = lr
        self.batch_size = batch_size
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.gamma = gamma
        self.reward_steps = reward_steps
        self.replay_size = replay_size
        self.monitor_buffer_size = monitor_buffer_size
        self.replay_start = replay_start
        self.epsilon_step = epsilon_step
        self.target_net_sync = target_net_sync
        self.validation_step = validation_step
        self.checkpoint_step = checkpoint_step
        self.weight_visualize_step = weight_visualize_step
        self.buffer_monitor_step = buffer_monitor_step
        self.validation_episodes = validation_episodes

        # load net file, if existed
        self.net_saved_path = net_saved_path
        self.net_file = net_file

        # build the env (long)
        self.env = environModel.TechicalForexEnv(symbols, self.train_Prices, tech_params, True, dataLoader.mt5Controller.all_symbols_info, 0.05, 8, 15, 1, random_ofs_on_reset=True, reset_on_close=True)
        self.env_val = environModel.TechicalForexEnv(symbols, self.test_Prices, tech_params, True, dataLoader.mt5Controller.all_symbols_info, 0.05, 8, 15, 1, random_ofs_on_reset=False, reset_on_close=False)

        self.net = NNModel.SimpleFFDQN(self.env.get_obs_len(), self.env.get_action_space_size())

        # create buffer
        self.selector = Actions.EpsilonGreedyActionSelector(self.epsilon_start)
        self.agent = Agents.DQNAgent(self.net, self.selector)
        self.exp_source = Experiences.ExperienceSourceFirstLast(self.env, self.agent, self.gamma, steps_count=self.reward_steps)
        self.buffer = Experiences.ExperienceReplayBuffer(self.exp_source, self.replay_size)

        # create optimizer
        self.optimizer = optim.Adam(self.net.parameters(), lr=lr)

        # create net pre-processor
        self.net_processor = common.netPreprocessor(self.net, self.agent.target_model)

        # validator
        self.validator = Validations.StockValidator(self.env_val, self.net, save_path=self.test_save_path, comission=0.1)

        # create the monitor
        self.monitor = common.monitor(self.buffer, self.buffer_save_path)

        # writer
        self.writer = SummaryWriter(log_dir=self.runs_save_path, comment="ForexRL")

        # loss tracker
        self.loss_tracker = Losses.Tracker(self.writer, group_losses=100)

        # reward tracker
        self.reward_tracker = Rewards.Tracker(self.writer, np.inf, group_rewards=100)

    def load_net(self):
        with open(os.path.join(self.net_saved_path, self.net_file), "rb") as f:
            checkpoint = torch.load(f)
        self.net = NNModel.SimpleFFDQN(self.env.get_obs_len(), self.env.get_action_space_size())
        self.net.load_state_dict(checkpoint['state_dict'])
        self.step_idx = common.find_stepidx(self.net_file, "-", "\.")

    def train(self):
        while True:
            self.step_idx += 1
            self.net_processor.populate_mode(batch_size=1)
            self.buffer.populate(1)
            self.selector.epsilon = max(self.epsilon_end, self.epsilon_start - self.step_idx * 0.75 / self.epsilon_step)

            new_rewards = self.exp_source.pop_rewards_steps()
            if new_rewards:
                self.reward_tracker.reward(new_rewards, self.step_idx, self.selector.epsilon)
            if len(self.buffer) < self.replay_start:
                continue

            self.optimizer.zero_grad()
            batch = self.buffer.sample(self.batch_size)

            # init the hidden both in network and tgt network
            self.net_processor.train_mode(batch_size=self.batch_size)
            loss_v = common.calc_loss(batch, self.agent, self.gamma ** self.reward_steps, train_on_gpu=True)
            loss_v.backward()
            self.optimizer.step()
            loss_value = loss_v.item()
            self.loss_tracker.loss(loss_value, self.step_idx)

            if self.step_idx % self.target_net_sync == 0:
                self.agent.sync()

            if self.step_idx % self.checkpoint_step == 0:
                # idx = step_idx // CHECKPOINT_EVERY_STEP
                checkpoint = {
                    "state_dict": self.net.state_dict()
                }
                with open(os.path.join(self.net_saved_path, "checkpoint-{}.data".format(self.step_idx)), "wb") as f:
                    torch.save(checkpoint, f)

            # TODO: validation has something to changed
            if self.step_idx % self.validation_step == 0:
                self.net_processor.eval_mode(batch_size=1)
                # writer.add_scalar("validation_episodes", validation_episodes, step_idx)
                val_epsilon = max(0, self.epsilon_start - self.step_idx * 0.75 / self.epsilon_step)
                stats = self.validator.run(episodes=self.validation_episodes, step_idx=self.step_idx, epsilon=val_epsilon)
                common.valid_result_visualize(stats, self.writer, self.step_idx)

            # TODO: how to visialize the weight better? eigenvector and eigenvalues?
            if self.step_idx % self.weight_visualize_step == 0:
                self.net_processor.eval_mode(batch_size=1)
                common.weight_visualize(self.net, self.writer)

            if self.step_idx % self.buffer_monitor_step == 0:
                self.monitor.out_csv(self.monitor_buffer_size, self.step_idx)

    def run(self):
        pass