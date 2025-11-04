"""
K-mer analysis utilities
"""

import torch
import numpy as np
from itertools import product
from multiprocessing import Pool, cpu_count
from functools import partial
from typing import List, Union
from .sequence import one_hot_to_sequence, batch_one_hot_to_sequence


def compute_kmer_spectra(
    seq: Union[torch.Tensor, np.ndarray],
    kmer_length: int,
    alphabet: List[str] = ['A', 'C', 'G', 'T']
) -> np.ndarray:
    """
    Compute k-mer spectrum for a sequence or batch of sequences.
    
    Args:
        seq: One-hot encoded sequence(s)
        kmer_length: Length of k-mers
        alphabet: DNA alphabet
        
    Returns:
        Normalized k-mer frequency distribution
    """
    # Convert to sequences
    if len(seq.shape) == 3 and seq.shape[0] > 1:
        seq_char = batch_one_hot_to_sequence(seq)
    else:
        seq_char = one_hot_to_sequence(seq)
    
    if isinstance(seq_char, str):
        seq_char = [seq_char]
    
    # Create k-mer dictionary
    kmer_dict = {''.join(p): i for i, p in enumerate(product(alphabet, repeat=kmer_length))}
    n_kmers = len(kmer_dict)
    
    # Count k-mers
    kmer_counts = np.zeros((len(seq_char), n_kmers))
    
    for i, sequence in enumerate(seq_char):
        # Rolling window approach
        for j in range(len(sequence) - kmer_length + 1):
            kmer = sequence[j:j + kmer_length]
            if 'N' not in kmer:
                kmer_counts[i, kmer_dict[kmer]] += 1
    
    # Normalize
    global_counts = np.sum(kmer_counts, axis=0)
    global_counts_normalized = global_counts / (np.sum(global_counts) + 1e-10)
    
    return global_counts_normalized


def _process_single_sequence(
    seq: str,
    kmer_length: int,
    kmer_dict: dict
) -> np.ndarray:
    """
    Process a single sequence to count k-mers (for parallel processing).
    
    Args:
        seq: DNA sequence string
        kmer_length: Length of k-mers
        kmer_dict: Dictionary mapping k-mers to indices
        
    Returns:
        K-mer count array
    """
    n_kmers = len(kmer_dict)
    kmer_counts = np.zeros(n_kmers)
    
    # Rolling window
    for j in range(len(seq) - kmer_length + 1):
        kmer = seq[j:j + kmer_length]
        if 'N' not in kmer:
            kmer_counts[kmer_dict[kmer]] += 1
            
    return kmer_counts


def compute_kmer_spectra_parallel(
    seq: Union[torch.Tensor, np.ndarray],
    kmer_length: int,
    alphabet: List[str] = ['A', 'C', 'G', 'T'],
    n_cores: int = None
) -> np.ndarray:
    """
    Parallelized version of compute_kmer_spectra.
    
    Args:
        seq: One-hot encoded sequence(s)
        kmer_length: Length of k-mers
        alphabet: DNA alphabet
        n_cores: Number of CPU cores to use
        
    Returns:
        Normalized k-mer frequency distribution
    """
    if n_cores is None:
        n_cores = max(1, cpu_count() - 2)
    
    # Convert to sequences
    if len(seq.shape) == 3 and seq.shape[0] > 1:
        seq_char = batch_one_hot_to_sequence(seq)
    else:
        seq_char = one_hot_to_sequence(seq)
    
    if isinstance(seq_char, str):
        seq_char = [seq_char]
    
    # Create k-mer dictionary
    kmer_dict = {''.join(p): i for i, p in enumerate(product(alphabet, repeat=kmer_length))}
    
    # Create partial function
    process_func = partial(
        _process_single_sequence,
        kmer_length=kmer_length,
        kmer_dict=kmer_dict
    )
    
    # Parallel processing
    with Pool(processes=n_cores) as pool:
        kmer_counts = pool.map(process_func, seq_char)
    
    # Convert to array
    kmer_counts = np.array(kmer_counts)
    
    # Normalize
    global_counts = np.sum(kmer_counts, axis=0)
    global_counts_normalized = global_counts / (np.sum(global_counts) + 1e-10)
    
    return global_counts_normalized


class kmer_featurization:
    """
    Class for converting DNA sequences to k-mer feature vectors.
    
    Args:
        k: The k in k-mer
        alphabet: DNA alphabet
    """
    
    def __init__(self, k: int, alphabet: List[str] = ['A', 'C', 'G', 'T']):
        self.k = k
        self.alphabet = alphabet
        self.multiplyBy = 4 ** np.arange(k-1, -1, -1)
        self.n = 4 ** k
    
    def obtain_kmer_feature_for_sequences(
        self,
        seqs: List[str],
        write_number_of_occurrences: bool = False
    ) -> np.ndarray:
        """
        Convert list of sequences to k-mer feature matrix.
        
        Args:
            seqs: List of DNA sequences
            write_number_of_occurrences: If True, use counts; if False, use frequencies
            
        Returns:
            Feature matrix of shape (n_sequences, 4**k)
        """
        kmer_features = []
        for seq in seqs:
            feature = self.obtain_kmer_feature_for_one_sequence(
                seq.upper(),
                write_number_of_occurrences=write_number_of_occurrences
            )
            kmer_features.append(feature)
        
        return np.array(kmer_features)
    
    def obtain_kmer_feature_for_one_sequence(
        self,
        seq: str,
        write_number_of_occurrences: bool = False
    ) -> np.ndarray:
        """
        Convert single sequence to k-mer feature vector.
        
        Args:
            seq: DNA sequence
            write_number_of_occurrences: If True, use counts; if False, use frequencies
            
        Returns:
            Feature vector of length 4**k
        """
        number_of_kmers = len(seq) - self.k + 1
        kmer_feature = np.zeros(self.n)
        
        for i in range(number_of_kmers):
            this_kmer = seq[i:(i + self.k)]
            if 'N' in this_kmer:
                number_of_kmers -= 1
            else:
                this_numbering = self.kmer_numbering_for_one_kmer(this_kmer)
                kmer_feature[this_numbering] += 1
        
        if not write_number_of_occurrences and number_of_kmers > 0:
            kmer_feature = kmer_feature / number_of_kmers
        
        return kmer_feature
    
    def kmer_numbering_for_one_kmer(self, kmer: str) -> int:
        """
        Get the index of a k-mer in the feature vector.
        
        Args:
            kmer: K-mer string
            
        Returns:
            Index in feature vector
        """
        digits = [self.alphabet.index(letter) for letter in kmer]
        digits = np.array(digits)
        numbering = (digits * self.multiplyBy).sum()
        return int(numbering)

