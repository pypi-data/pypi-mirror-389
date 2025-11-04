"""
Sequence utility functions
"""

import torch
import numpy as np
from typing import Union


def one_hot_to_sequence(
    one_hot: Union[torch.Tensor, np.ndarray],
    alphabet: list = ['A', 'C', 'G', 'T'],
    allow_N: bool = False
) -> str:
    """
    Convert one-hot encoded sequence to string sequence.
    
    Args:
        one_hot: One-hot encoded sequence of shape (alphabet_size, seq_len) or (seq_len, alphabet_size)
        alphabet: List of nucleotides
        allow_N: Whether to allow 'N' for positions with all zeros
        
    Returns:
        String DNA sequence
    """
    # Convert to torch if numpy
    if isinstance(one_hot, np.ndarray):
        one_hot = torch.from_numpy(one_hot)
    
    # Ensure correct shape (alphabet_size, seq_len)
    if one_hot.shape[0] > one_hot.shape[1]:
        one_hot = one_hot.T
    
    # Get indices of max values
    indices = torch.argmax(one_hot, dim=0)
    
    # Convert to sequence
    sequence = ''.join([alphabet[i] for i in indices])
    
    # Handle N's if allowed
    if allow_N:
        all_zeros = (one_hot.sum(dim=0) == 0)
        sequence_list = list(sequence)
        for i, is_zero in enumerate(all_zeros):
            if is_zero:
                sequence_list[i] = 'N'
        sequence = ''.join(sequence_list)
    
    return sequence


def validate_one_hot(
    seq: Union[torch.Tensor, np.ndarray],
    name: str = "sequence",
    ohe: bool = True,
    allow_N: bool = False
) -> torch.Tensor:
    """
    Validate input sequence format.
    
    Args:
        seq: Input sequence tensor
        name: Name for error messages
        ohe: Whether to expect one-hot encoding
        allow_N: Whether to allow N nucleotides
        
    Returns:
        Validated tensor
        
    Raises:
        ValueError: If sequence format is invalid
    """
    # Convert to tensor if numpy
    if isinstance(seq, np.ndarray):
        seq = torch.from_numpy(seq)
    
    # Check shape
    if len(seq.shape) not in [2, 3]:
        raise ValueError(
            f"{name} must be 2D (alphabet, seq_len) or 3D (batch, alphabet, seq_len), "
            f"got shape {seq.shape}"
        )
    
    # Check one-hot encoding if required
    if ohe:
        if len(seq.shape) == 2:
            if seq.shape[0] not in [4, 5]:  # 4 for ACGT, 5 for ACGTN
                raise ValueError(
                    f"One-hot {name} should have 4 or 5 channels for nucleotides, "
                    f"got {seq.shape[0]}"
                )
        elif len(seq.shape) == 3:
            if seq.shape[1] not in [4, 5]:
                raise ValueError(
                    f"One-hot {name} should have 4 or 5 channels for nucleotides, "
                    f"got {seq.shape[1]}"
                )
    
    return seq


def batch_one_hot_to_sequence(
    one_hot_batch: Union[torch.Tensor, np.ndarray],
    alphabet: list = ['A', 'C', 'G', 'T'],
    allow_N: bool = False
) -> list:
    """
    Convert batch of one-hot encoded sequences to string sequences.
    
    Args:
        one_hot_batch: Batch of one-hot encoded sequences (batch, alphabet_size, seq_len)
        alphabet: List of nucleotides
        allow_N: Whether to allow 'N' for positions with all zeros
        
    Returns:
        List of string DNA sequences
    """
    sequences = []
    for one_hot in one_hot_batch:
        sequences.append(one_hot_to_sequence(one_hot, alphabet, allow_N))
    return sequences

