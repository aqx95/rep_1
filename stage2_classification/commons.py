import os
import logging
import torch
import sklearn
import math
import random
import numpy as np
from scipy.stats import beta
from sklearn.metrics import roc_auc_score



def rand_bbox(size, lam):
    W = size[2]
    H = size[3]
    cut_rat = np.sqrt(1. - lam)
    cut_w = np.int(W * cut_rat)
    cut_h = np.int(H * cut_rat)

    # uniform
    cx = np.random.randint(W)
    cy = np.random.randint(H)

    bbx1 = np.clip(cx - cut_w // 2, 0, W)
    bby1 = np.clip(cy - cut_h // 2, 0, H)
    bbx2 = np.clip(cx + cut_w // 2, 0, W)
    bby2 = np.clip(cy + cut_h // 2, 0, H)
    return bbx1, bby1, bbx2, bby2

### Cutmix
def cutmix(data, target, alpha):
    indices = torch.randperm(data.size(0))
    shuffled_data = data[indices]
    shuffled_target = target[indices]

    lam = np.clip(np.random.beta(alpha, alpha),0.3,0.4)
    bbx1, bby1, bbx2, bby2 = rand_bbox(data.size(), lam)
    new_data = data.clone()
    new_data[:, :, bby1:bby2, bbx1:bbx2] = data[indices, :, bby1:bby2, bbx1:bbx2]
    # adjust lambda to exactly match pixel ratio
    lam = 1 - ((bbx2 - bbx1) * (bby2 - bby1) / (data.size()[-1] * data.size()[-2]))
    targets = (target, shuffled_target, lam)

    return new_data, targets


def log(config, name):
    if not os.path.exists(config.LOG_PATH):
        os.makedirs(config.LOG_PATH)
    log_file = os.path.join(config.LOG_PATH, 'log.txt')
    open(log_file, "w+").close()

    console_log_format = "%(levelname)s %(message)s"
    file_log_format = "%(levelname)s: %(asctime)s: %(message)s"

    #Configure logger
    logging.basicConfig(level=logging.INFO, format=console_log_format)
    logger = logging.getLogger(name)

    #File handler
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(file_log_format)
    handler.setFormatter(formatter)

    #Stream handler
    s_handler = logging.StreamHandler()
    s_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(file_log_format)
    s_handler.setFormatter(formatter)

    #Add handler to logger
    logger.addHandler(handler)
    logger.addHandler(s_handler)

    return logger


class Meter:
    def __init__(self):
        self.reset()

    def reset(self):
        self.loss = 0
        self.count = 0

    def update(self, batch_loss, batch_size):
        self.loss += batch_loss*batch_size
        self.count += batch_size

    @property
    def avg(self):
        return self.loss/self.count


class AucMeter:
    def __init__(self):
        self.reset()

    def reset(self):
        self.pred = []
        self.target = []

    def update(self, pred, target):
        self.pred += [pred.sigmoid().cpu()]
        self.target += [target.detach().cpu()]

    def macro_auc(self, pred, label):
        aucs = []
        for i in range(label.shape[1]):
            aucs.append(roc_auc_score(label[:, i], pred[:, i]))
        return np.mean(aucs)

    @property
    def get_auc(self):
        self.pred = torch.cat(self.pred).numpy()
        self.target = torch.cat(self.target).numpy()
        return self.macro_auc(self.pred, self.target)
