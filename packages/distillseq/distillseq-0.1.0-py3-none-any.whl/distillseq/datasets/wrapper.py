"""
Dataset wrapper utilities
"""

import torch
from torch.utils.data import Dataset
from typing import Tuple, Optional


class DistilledDataset(Dataset):
    """
    Wrapper for distilled datasets.
    
    This class wraps distilled synthetic data (from GradientMatching) or
    creates a view of selected indices from the original dataset.
    
    Args:
        sequences: Tensor of sequences (synthetic or subset)
        targets: Tensor of targets
        original_dataset: Optional reference to original dataset
        indices: Optional list of indices if this is a subset
        
    Example:
        >>> # From synthetic data
        >>> syn_seqs, syn_targets = distiller.create_synthetic_dataset()
        >>> distilled_ds = DistilledDataset(syn_seqs, syn_targets)
        
        >>> # From indices
        >>> indices = distiller.distill()
        >>> distilled_ds = DistilledDataset.from_indices(
        ...     original_dataset, indices
        ... )
    """
    
    def __init__(
        self,
        sequences: torch.Tensor,
        targets: torch.Tensor,
        original_dataset: Optional[Dataset] = None,
        indices: Optional[list] = None
    ):
        self.sequences = sequences
        self.targets = targets
        self.original_dataset = original_dataset
        self.indices = indices
    
    def __len__(self) -> int:
        return len(self.sequences)
    
    def __getitem__(self, idx: int) -> dict:
        return {
            'seq': self.sequences[idx],
            'y': self.targets[idx]
        }
    
    @classmethod
    def from_indices(
        cls,
        dataset: Dataset,
        indices: list
    ) -> 'DistilledDataset':
        """
        Create DistilledDataset from original dataset and indices.
        
        Args:
            dataset: Original dataset
            indices: List of indices to include
            
        Returns:
            DistilledDataset instance
        """
        sequences = []
        targets = []
        
        for idx in indices:
            sample = dataset[idx]
            sequences.append(sample['seq'])
            targets.append(sample['y'])
        
        sequences = torch.stack(sequences)
        targets = torch.stack(targets)
        
        return cls(sequences, targets, original_dataset=dataset, indices=indices)
    
    def get_statistics(self) -> dict:
        """Get statistics about the distilled dataset."""
        stats = {
            'size': len(self),
            'seq_shape': tuple(self.sequences.shape[1:]),
            'target_shape': tuple(self.targets.shape[1:]) if self.targets.dim() > 1 else (1,),
        }
        
        if self.original_dataset is not None:
            stats['original_size'] = len(self.original_dataset)
            stats['ratio'] = len(self) / len(self.original_dataset)
            stats['reduction'] = 1 - stats['ratio']
        
        return stats
    
    def save(self, filepath: str):
        """Save the distilled dataset to file."""
        torch.save({
            'sequences': self.sequences,
            'targets': self.targets,
            'indices': self.indices
        }, filepath)
    
    @classmethod
    def load(cls, filepath: str) -> 'DistilledDataset':
        """Load a distilled dataset from file."""
        data = torch.load(filepath)
        return cls(
            sequences=data['sequences'],
            targets=data['targets'],
            indices=data.get('indices')
        )

