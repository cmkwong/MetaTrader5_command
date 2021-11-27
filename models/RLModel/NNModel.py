import torch
import torch.nn as nn

class SimpleFFDQN(nn.Module):
    def __init__(self, obs_len, actions_n):
        super(SimpleFFDQN, self).__init__()
        self.device = torch.device("cuda")

        self.fc_val = nn.Sequential(
            nn.Linear(obs_len, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 1)
        ).to(self.device)

        self.fc_adv = nn.Sequential(
            nn.Linear(obs_len, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, actions_n)
        ).to(self.device)

    def forward(self, x):
        x = x.to(self.device)
        val = self.fc_val(x)
        adv = self.fc_adv(x)
        return val + adv - adv.mean(dim=1, keepdim=True)