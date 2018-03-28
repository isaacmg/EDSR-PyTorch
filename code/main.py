import torch

import utils
from option import args
from data_loader import DataCreator
from trainer import Trainer

torch.manual_seed(args.seed)
checkpoint = utils.checkpoint(args)

if checkpoint.ok:
    my_loader = data(args).get_loader()
    t = Trainer(my_loader, checkpoint, args)
    while not t.terminate():
        t.train()
        t.test()

    checkpoint.done()
