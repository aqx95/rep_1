import torch
import math
import torch.nn as nn
import torch.nn.functional as F

### Loss factory
def loss_fn(loss_name, config):
    if loss_name == "bce":
        return nn.BCEWithLogitsLoss()
    if loss_name == 'labelsmoothloss':
        return LabelSmoothLoss(**config.criterion_params[config.criterion])

### Label Smoothing Loss
class LabelSmoothLoss(nn.Module):
    def __init__(self, num_class, smoothing=0.1, dim=-1):
        super().__init__()
        self.conf = 1.0 - smoothing
        self.classes = num_class
        self.smoothing = smoothing
        self.dim = dim

    def forward(self, input, target):
        log_probs = nn.LogSigmoid()(input)
        with torch.no_grad():
            true_dist = torch.zeros_like(log_probs)
            true_dist.fill_(self.smoothing / (self.classes - 1))
            true_dist.scatter_(1, target.data.unsqueeze(1), self.conf)
        return torch.mean(torch.sum(-true_dist * log_probs, dim=self.dim))
