"""
Divergence metrics for comparing distributions
"""

import numpy as np
from scipy.special import kl_div
from scipy.spatial.distance import jensenshannon


def compute_divergence(
    dist1: np.ndarray,
    dist2: np.ndarray,
    divergence: str = 'JSD'
) -> float:
    """
    Compute divergence between two distributions.
    
    Args:
        dist1: First probability distribution
        dist2: Second probability distribution
        divergence: Type of divergence ('KLD' or 'JSD')
        
    Returns:
        Divergence value
    """
    assert divergence.upper() in ['KLD', 'JSD'], "divergence must be 'KLD' or 'JSD'"
    
    if divergence.upper() == 'KLD':
        return float(np.sum(kl_div(dist1, dist2)))
    else:  # JSD
        return float(jensenshannon(dist1, dist2))


def kmer_statistics(
    seq1: np.ndarray,
    seq2: np.ndarray,
    kmer_length: int,
    calc_seq1: str = 'ALL',
    n_cores: int = None
) -> dict:
    """
    Compute KLD and JSD between k-mer distributions of two sequence sets.
    
    Args:
        seq1: Test sequences (one-hot encoded)
        seq2: Reference sequences (one-hot encoded)
        kmer_length: Length of k-mers
        calc_seq1: 'ALL' for entire set, 'MULTI' for per-sequence
        n_cores: Number of CPU cores
        
    Returns:
        Dictionary with 'kld' and 'jsd' values
    """
    from .kmer import compute_kmer_spectra, compute_kmer_spectra_parallel
    import tqdm
    
    if n_cores is None:
        n_cores = max(1, __import__('multiprocessing').cpu_count() - 2)
    
    # Compute reference k-mer distribution
    print("Computing reference k-mer spectra...")
    kmer_dist_ref = compute_kmer_spectra_parallel(seq2, kmer_length=kmer_length, n_cores=n_cores)
    
    if calc_seq1.upper() == 'MULTI':
        # Compute per-sequence
        kld = []
        jsd = []
        print("Computing KLD and JSD for each test sequence...")
        for seq_i in tqdm.tqdm(seq1, total=seq1.shape[0]):
            kmer_dist_i = compute_kmer_spectra(seq_i, kmer_length=kmer_length)
            kld.append(compute_divergence(kmer_dist_i, kmer_dist_ref, divergence='KLD'))
            jsd.append(compute_divergence(kmer_dist_i, kmer_dist_ref, divergence='JSD'))
    else:  # ALL
        print("Computing KLD and JSD for entire test set...")
        kmer_dist_seq1 = compute_kmer_spectra(seq1, kmer_length=kmer_length)
        kld = compute_divergence(kmer_dist_seq1, kmer_dist_ref, divergence='KLD')
        jsd = compute_divergence(kmer_dist_seq1, kmer_dist_ref, divergence='JSD')
    
    return {'kld': kld, 'jsd': jsd}

