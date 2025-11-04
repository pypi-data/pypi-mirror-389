"""
K-mer diversity sampling method
"""

import torch
import numpy as np
from torch.utils.data import DataLoader
from typing import List
import heapq
from tqdm import tqdm

from .base import BaseDistiller
from ..utils.divergence import kmer_statistics


class KmerDiversity(BaseDistiller):
    """
    K-mer diversity sampling for dataset distillation.
    
    Maximizes sequence diversity using Jensen-Shannon Divergence on k-mer distributions.
    Uses an iterative approach to select the most diverse sequences.
    
    Algorithm:
        1. Calculate diversity against all training samples, pick top 10%
        2. Calculate diversity of remaining samples against picked pool
        3. Add top 10% to picked pool and recalculate
        4. Repeat until target size reached
    
    Args:
        dataset: PyTorch dataset to distill with DNA sequences in 'x' and, optionally, region indices in 'reg' keys
        ratio: Proportion of data to keep (0 < ratio < 1)
        kmer_length: Length of k-mers (default: 6)
        seed: Random seed for reproducibility
        batch_size: Batch size for data loading
        num_workers: Number of workers for data loading
        n_cores: Number of CPU cores for k-mer calculations
        verbose: Whether to print progress
        
    Example:
        >>> distiller = KmerDiversity(
        ...     dataset=my_dataset,
        ...     ratio=0.1,
        ...     kmer_length=6,
        ...     n_cores=20
        ... )
        >>> diverse_indices = distiller.distill()
    """
    
    def __init__(
        self,
        dataset,
        ratio: float = 0.1,
        kmer_length: int = 6,
        seed: int = 42,
        batch_size: int = 1024,
        num_workers: int = 16,
        n_cores: int = 14,
        verbose: bool = True
    ):
        super().__init__(
            dataset=dataset,
            ratio=ratio,
            seed=seed,
            device='cpu',  # K-mer diversity uses CPU
            verbose=verbose
        )
        
        self.kmer_length = kmer_length
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.n_cores = n_cores
    
    def _load_sequences_and_indices(self) -> tuple:
        """Load all sequences and their indices from the dataset."""
        if self.verbose:
            print("Loading sequences from dataset...")
        
        dataloader = DataLoader(
            self.dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=False
        )
        
        seqs = []
        ids = []
        
        for batch in tqdm(dataloader, disable=not self.verbose, desc="Loading data"):
            seqs.append(batch['x'])
            # Get indices - either from 'reg_i' or generate them
            if 'reg_i' in batch:
                ids.append(batch['reg'])
            else:
                # Generate indices based on current batch position
                start_idx = len(ids) * self.batch_size
                batch_ids = torch.arange(start_idx, start_idx + len(batch['x']))
                ids.append(batch_ids)
        
        # Concatenate all batches
        seqs = torch.cat(seqs)
        ids = torch.cat(ids)
        
        # Ensure sequences are in correct format for k-mer analysis
        # Expected: (batch, seq_len, alphabet_size) or (batch, alphabet_size, seq_len)
        if seqs.dim() == 3 and seqs.shape[1] < seqs.shape[2]:
            # Shape is (batch, alphabet, seq_len), need (batch, seq_len, alphabet)
            seqs = seqs.transpose(1, 2)
        
        return seqs, ids.numpy()
    
    def _distill_indices(self) -> List[int]:
        """
        Perform k-mer diversity sampling.
        
        Returns:
            List of selected diverse indices
        """
        # Load sequences
        seqs, ids = self._load_sequences_and_indices()
        
        # Calculate number to pick in each round (10% of target)
        num_per_round = int(self.target_size * 0.1)
        
        # Round 1: Calculate diversity against all training samples
        if self.verbose:
            print("Round 1: Computing diversity against full dataset...")
        
        all_changes = kmer_statistics(
            seqs, seq2=seqs,
            calc_seq1='MULTI',
            kmer_length=self.kmer_length,
            n_cores=self.n_cores
        )
        
        # Get highest diversity cases
        id_div = dict(zip(ids, all_changes['jsd']))
        picked_samples = heapq.nlargest(num_per_round, id_div, key=id_div.get)
        down_sample_ids = picked_samples.copy()
        
        # Get sequences for picked samples
        picked_indices = np.where(np.isin(ids, picked_samples))[0]
        picked_seqs = seqs[picked_indices]
        
        # Rounds 2-10: Iteratively add most diverse samples
        for round_num in range(2, 11):
            if self.verbose:
                print(f"Round {round_num}: Computing diversity...")
            
            # Remove picked samples
            remaining_mask = ~np.isin(ids, picked_samples)
            seqs = seqs[remaining_mask]
            ids = ids[remaining_mask]
            
            if len(ids) == 0:
                break
            
            # Compute diversity against picked pool
            all_changes = kmer_statistics(
                seqs, seq2=picked_seqs,
                calc_seq1='MULTI',
                kmer_length=self.kmer_length,
                n_cores=self.n_cores
            )
            
            # Pick top diverse samples
            id_div = dict(zip(ids.tolist(), all_changes['jsd']))
            picked_samples = heapq.nlargest(num_per_round, id_div, key=id_div.get)
            down_sample_ids.extend(picked_samples)
            
            # Add to picked pool
            picked_indices = np.where(np.isin(ids, picked_samples))[0]
            new_seqs = seqs[picked_indices]
            picked_seqs = torch.cat([picked_seqs, new_seqs])
        
        return down_sample_ids

