"""
Genomic Language Model (gLM) diversity sampling method
"""

import torch
import numpy as np
from torch.utils.data import DataLoader
from typing import List, Optional
from tqdm import tqdm

from .base import BaseDistiller


class GLMDiversity(BaseDistiller):
    """
    gLM diversity sampling using genomic language model embeddings.
    
    Maximizes diversity using embeddings from a genomic language model
    (e.g., DNABERT-S). Uses K-means clustering on embeddings and samples
    evenly from each cluster.
    
    Args:
        dataset: PyTorch dataset to distill with DNA sequences in 'x' and, optionally, region indices in 'reg' keys
        ratio: Proportion of data to keep (0 < ratio < 1)
        model_name: Name of the genomic language model (default: "zhihan1996/DNABERT-S")
        seed: Random seed for reproducibility
        batch_size: Batch size for model inference & data loading
        num_workers: Number of workers for data loading
        min_clusters: Minimum number of clusters to try
        max_clusters: Maximum number of clusters to try
        random_state: Random state for K-means
        verbose: Whether to print progress
        
    Example:
        >>> distiller = GLMDiversity(
        ...     dataset=my_dataset,
        ...     ratio=0.1,
        ...     model_name="zhihan1996/DNABERT-S"
        ... )
        >>> diverse_indices = distiller.distill()
        
    Note:
        Requires transformers to be installed:
        pip install distillseq[glm]
    """
    
    def __init__(
        self,
        dataset,
        ratio: float = 0.1,
        model_name: str = "zhihan1996/DNABERT-S",
        seed: int = 42,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        batch_size: int = 16,
        num_workers: int = 16,
        min_clusters: Optional[int] = None,
        max_clusters: Optional[int] = None,
        random_state: int = 0,
        verbose: bool = True
    ):
        super().__init__(
            dataset=dataset,
            ratio=ratio,
            seed=seed,
            device=device,
            verbose=verbose
        )
        
        self.model_name = model_name
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.random_state = random_state
        
        # Set default cluster ranges
        self.min_clusters = min_clusters or 6
        self.max_clusters = max_clusters or 16
        
        # Load model and tokenizer
        self._load_glm()
    
    def _load_glm(self):
        """Load the genomic language model."""
        try:
            from transformers import AutoTokenizer, AutoModel
        except ImportError:
            raise ImportError(
                "transformers is required for GLMDiversity. "
                "Install with: pip install distillseq[glm]"
            )
        
        if self.verbose:
            print(f"Loading {self.model_name}...")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        self.glm_model = AutoModel.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        self.glm_model.to(self.device)
        self.glm_model.eval()
    
    def _sequence_to_string(self, one_hot: torch.Tensor) -> str:
        """Convert one-hot encoded sequence to DNA string."""
        from ..utils.sequence import one_hot_to_sequence
        return one_hot_to_sequence(one_hot)
    
    def _load_sequences_and_indices(self) -> tuple:
        """Load all sequences and their indices."""
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
            # Get indices
            if 'reg_i' in batch:
                ids.append(batch['reg'])
            else:
                start_idx = len(ids) * self.batch_size
                batch_ids = torch.arange(start_idx, start_idx + len(batch['x']))
                ids.append(batch_ids)
        
        seqs = torch.cat(seqs)
        ids = torch.cat(ids)
        
        # Ensure correct shape
        if seqs.dim() == 3 and seqs.shape[1] < seqs.shape[2]:
            seqs = seqs.transpose(1, 2)
        
        return seqs, ids.numpy()
    
    def _compute_embeddings(self, seqs: torch.Tensor) -> torch.Tensor:
        """Compute gLM embeddings for sequences."""
        if self.verbose:
            print("Computing gLM embeddings...")
        
        embeddings = []
        
        for i in tqdm(
            range(0, len(seqs), self.batch_size),
            disable=not self.verbose,
            desc="Computing embeddings"
        ):
            # Get batch
            batch_seqs = seqs[i:i + self.batch_size]
            
            # Convert to DNA strings
            batch_dna = [self._sequence_to_string(seq) for seq in batch_seqs]
            
            # Tokenize
            inputs = self.tokenizer(
                batch_dna,
                return_tensors='pt',
                padding=True,
                truncation=True,
                max_length=512  # Adjust based on model
            )["input_ids"].to(self.device)
            
            # Get embeddings
            with torch.no_grad():
                hidden_states = self.glm_model(inputs)[0]
                # Mean pooling
                batch_embeddings = torch.mean(hidden_states, dim=1)
                embeddings.append(batch_embeddings.cpu())
        
        return torch.cat(embeddings, dim=0)
    
    def _find_optimal_clusters(self, embeddings_np: np.ndarray) -> int:
        """Find optimal number of clusters using elbow method."""
        from sklearn.cluster import KMeans
        
        if self.verbose:
            print("Finding optimal number of clusters...")
        
        n_clusters_range = range(self.min_clusters, self.max_clusters + 1)
        inertias = []
        
        for n_clusters in tqdm(
            n_clusters_range,
            disable=not self.verbose,
            desc="Testing clusters"
        ):
            kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=self.random_state,
                n_init=10
            )
            kmeans.fit(embeddings_np)
            inertias.append(kmeans.inertia_)
        
        # Find elbow point
        inertias = np.array(inertias)
        inertia_diff = np.diff(inertias)
        inertia_diff_r = np.diff(inertia_diff)
        optimal_clusters = n_clusters_range[np.argmax(inertia_diff_r) + 1]
        
        if self.verbose:
            print(f"Optimal number of clusters: {optimal_clusters}")
        
        return optimal_clusters
    
    def _distill_indices(self) -> List[int]:
        """
        Perform gLM diversity sampling.
        
        Returns:
            List of selected diverse indices
        """
        from sklearn.cluster import KMeans
        
        # Load sequences
        seqs, ids = self._load_sequences_and_indices()
        
        # Compute embeddings
        embeddings = self._compute_embeddings(seqs)
        embeddings_np = embeddings.numpy()
        
        # Find optimal number of clusters
        optimal_n_clusters = self._find_optimal_clusters(embeddings_np)
        
        # Final clustering
        if self.verbose:
            print(f"Clustering with {optimal_n_clusters} clusters...")
        
        final_kmeans = KMeans(
            n_clusters=optimal_n_clusters,
            random_state=self.random_state,
            n_init=10
        )
        cluster_labels = final_kmeans.fit_predict(embeddings_np)
        
        # Print cluster sizes
        if self.verbose:
            unique, counts = np.unique(cluster_labels, return_counts=True)
            print("\nCluster sizes:")
            for cluster, count in zip(unique, counts):
                print(f"  Cluster {cluster}: {count} sequences")
        
        # Sample from each cluster
        num_sample_per_cluster = int(self.target_size // optimal_n_clusters)
        sampled_ids = []
        
        for i in range(optimal_n_clusters):
            cluster_ids = ids[cluster_labels == i]
            # Sample with replacement to handle small clusters
            sampled = np.random.choice(
                cluster_ids,
                num_sample_per_cluster,
                replace=True
            )
            sampled_ids.extend(sampled.tolist())
        
        return sampled_ids

