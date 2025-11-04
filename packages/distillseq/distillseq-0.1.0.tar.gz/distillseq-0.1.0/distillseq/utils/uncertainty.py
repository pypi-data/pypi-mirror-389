"""
Uncertainty utility functions
"""

import torch

def enable_mc_dropout(model: torch.nn.Module) -> None:
    """ Function to enable the dropout layers (MC dropout) during test-time """
    model.eval()
    for m in model.modules():
        if isinstance(m, torch.nn.Dropout):
            m.train()