"""
Random sampling baseline method
"""

import numpy as np
from typing import List
from .base import BaseDistiller


class RandomSampling(BaseDistiller):
    """
    Random sampling baseline for dataset distillation.
    
    This method randomly samples a subset of the dataset without any
    intelligent selection criteria. Useful as a baseline for comparison.
    
    Args:
        dataset: PyTorch dataset to distill
        ratio: Proportion of data to keep (0 < ratio < 1)
        seed: Random seed for reproducibility
        replace: Whether to sample with replacement
        verbose: Whether to print progress information
        
    Example:
        >>> sampler = RandomSampling(dataset=my_dataset, ratio=0.1, seed=42)
        >>> distilled_indices = sampler.distill()
        >>> distilled_dataset = sampler.create_subset()
    """
    
    def __init__(
        self,
        dataset,
        ratio: float = 0.1,
        seed: int = 42,
        replace: bool = False,
        verbose: bool = True
    ):
        super().__init__(
            dataset=dataset,
            ratio=ratio,
            seed=seed,
            device='cpu',  # Random sampling doesn't need GPU
            verbose=verbose
        )
        self.replace = replace
    
    def _distill_indices(self) -> List[int]:
        """
        Randomly sample indices from the dataset.
        
        Returns:
            List of randomly sampled indices
        """
        indices = np.random.choice(
            len(self.dataset),
            size=self.target_size,
            replace=self.replace
        )
        return indices.tolist()

