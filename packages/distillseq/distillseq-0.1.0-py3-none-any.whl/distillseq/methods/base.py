"""
Base class for all distillation methods
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Union
import torch
from torch.utils.data import Dataset, Subset
import numpy as np


class BaseDistiller(ABC):
    """
    Abstract base class for all dataset distillation methods.
    
    All distillation methods should inherit from this class and implement
    the `_distill_indices` method.
    
    Args:
        dataset: PyTorch dataset to distill
        ratio: Proportion of data to keep (0 < ratio < 1)
        seed: Random seed for reproducibility
        device: Device to use ('cuda' or 'cpu')
        verbose: Whether to print progress information
    """
    
    def __init__(
        self,
        dataset: Dataset,
        ratio: float = 0.1,
        seed: int = 42,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        verbose: bool = True
    ):
        assert 0 < ratio < 1, "Ratio must be between 0 and 1"
        
        self.dataset = dataset
        self.ratio = ratio
        self.seed = seed
        self.device = device
        self.verbose = verbose
        
        # Calculate target size
        self.target_size = int(len(dataset) * ratio)
        
        # Set random seeds
        torch.manual_seed(seed)
        np.random.seed(seed)
        
        # Store distilled indices
        self._distilled_indices: Optional[List[int]] = None
        
    @abstractmethod
    def _distill_indices(self) -> List[int]:
        """
        Core distillation logic - must be implemented by subclasses.
        
        Returns:
            List of indices representing the distilled dataset
        """
        pass
    
    def distill(self) -> Union[List[int], Subset]:
        """
        Perform distillation and return the result.
        
        Returns:
            List of distilled indices or a Subset dataset
        """
        if self._distilled_indices is None:
            if self.verbose:
                print(f"Distilling dataset from {len(self.dataset)} to {self.target_size} samples...")
            self._distilled_indices = self._distill_indices()
            if self.verbose:
                print(f"Distillation complete! Selected {len(self._distilled_indices)} samples.")
        
        return self._distilled_indices
    
    def create_subset(self) -> Subset:
        """
        Create a PyTorch Subset from the distilled indices.
        
        Returns:
            PyTorch Subset containing the distilled data
        """
        indices = self.distill()
        return Subset(self.dataset, indices)
    
    def get_statistics(self) -> dict:
        """
        Get statistics about the distillation process.
        
        Returns:
            Dictionary containing distillation statistics
        """
        if self._distilled_indices is None:
            self.distill()
            
        return {
            'original_size': len(self.dataset),
            'distilled_size': len(self._distilled_indices),
            'ratio': len(self._distilled_indices) / len(self.dataset),
            'reduction': 1 - (len(self._distilled_indices) / len(self.dataset)),
            'method': self.__class__.__name__
        }
    
    def save_indices(self, filepath: str):
        """
        Save distilled indices to file.
        
        Args:
            filepath: Path to save the indices
        """
        if self._distilled_indices is None:
            self.distill()
            
        torch.save(self._distilled_indices, filepath)
        if self.verbose:
            print(f"Saved distilled indices to {filepath}")
    
    @classmethod
    def load_indices(cls, filepath: str) -> List[int]:
        """
        Load distilled indices from file.
        
        Args:
            filepath: Path to load the indices from
            
        Returns:
            List of indices
        """
        return torch.load(filepath)

