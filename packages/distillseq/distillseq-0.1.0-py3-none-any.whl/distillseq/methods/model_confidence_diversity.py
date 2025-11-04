"""
Model confidence diversity sampling method using ensemble uncertainty
"""

import torch
import numpy as np
from torch.utils.data import DataLoader
from typing import List, Optional
from tqdm import tqdm
import os

from .base import BaseDistiller
from ..utils.uncertainty import enable_mc_dropout


class ModelConfidenceDiversity(BaseDistiller):
    """
    Model confidence diversity sampling using stratified epistemic uncertainty sampling.
    
    This method uses epistemic (model) uncertainty - quantified through ensemble prediction 
    variability - to perform stratified sampling across different confidence levels. 
    
    **Epistemic Uncertainty:**
    Epistemic uncertainty represents model uncertainty due to limited knowledge about the
    best model parameters. Unlike aleatoric (data) uncertainty which is irreducible, 
    epistemic uncertainty can be reduced with more training data or better models. This
    implementation captures epistemic uncertainty by:
    - Using Monte Carlo (MC) dropout to sample different model configurations
    - Using model ensembles to capture disagreement between independently trained models
    - Computing standard deviation across predictions to quantify model disagreement
    
    The method performs stratified sampling across uncertainty bins, ensuring the distilled 
    dataset includes samples from all epistemic uncertainty levels - from confident predictions
    (low model disagreement) to uncertain predictions (high model disagreement).
    
    Args:
        dataset: PyTorch dataset to distill with DNA sequences in 'x' and, optionally, region indices in 'reg' keys
        model: PyTorch model or list of models to use for epistemic uncertainty estimation
        ratio: Proportion of data to keep (0 < ratio < 1)
        mc_dropout: Number of MC dropout samples per model (must be > 0 if single model provided)
        seed: Random seed for reproducibility
        device: Device to run the model on ('cuda' or 'cpu')
        batch_size: Batch size for model inference
        num_workers: Number of workers for data loading
        n_bins: Number of uncertainty bins for stratified sampling (default: 100)
        verbose: Whether to print progress
        plt_save_path: Path to save uncertainty distribution plot
        dpi: DPI for saved plots
        
    Example:
        >>> # Using MC dropout with single model (captures epistemic uncertainty)
        >>> distiller = ModelConfidenceDiversity(
        ...     dataset=my_dataset,
        ...     model=model,
        ...     ratio=0.1,
        ...     mc_dropout=10,
        ...     n_bins=100,
        ... )
        >>> diverse_indices = distiller.distill()
        
        >>> # Using model ensemble (captures epistemic uncertainty)
        >>> distiller = ModelConfidenceDiversity(
        ...     dataset=my_dataset,
        ...     model=[model1, model2, model3],
        ...     ratio=0.1,
        ...     mc_dropout=1,
        ...     n_bins=100,
        ... )
        >>> diverse_indices = distiller.distill()
        
    Note:
        - At least 3 total predictions (ensemble models * MC dropout samples) are required
        - Epistemic uncertainty is computed as the standard deviation across model predictions
        - Stratified sampling ensures representation across all epistemic uncertainty levels
        - MC dropout approximates Bayesian inference (Gal & Ghahramani, 2016)
        
    References:
        Gal, Y., & Ghahramani, Z. (2016). Dropout as a Bayesian approximation: 
        Representing model uncertainty in deep learning. ICML.
    """
    
    def __init__(
        self,
        dataset,
        ratio: float = 0.1,
        model: torch.nn.Module or list[torch.nn.Module] = None,
        mc_dropout: int = 0,
        seed: int = 42,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        batch_size: int = 16,
        num_workers: int = 16,
        n_bins: int = 100,
        verbose: bool = True,
        plt_save_path: str = "./results/uncertainty_distributions/uncertainty_distribution.png",
        dpi: int = 1000
    ):
        super().__init__(
            dataset=dataset,
            ratio=ratio,
            seed=seed,
            device=device,
            verbose=verbose
        )
        
        self.batch_size = batch_size
        self.num_workers = num_workers
        
        # Set number of bins for confidence scoring
        self.n_bins = n_bins
        self.plt_save_path = plt_save_path
        self.dpi = dpi
        # Check if ensembl of models is provided
        self.mc_dropout = mc_dropout
        if isinstance(model, list):
            self.models = model
        else:
            assert model is not None, "Model must be provided"
            assert mc_dropout > 0, "MC dropout must be greater than 0 if only one model is provided"
            self.models = [model]
        self.num_model_preds = max(mc_dropout,1)*len(self.models)
        assert self.num_model_preds > 2, "Number of model predictions (number of ensemble models * number of MC dropout samples) must be greater than 2 to get a meaningful uncertainty estimate"
    
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
            # Get indices - fix key name consistency
            if 'reg' in batch:
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
    
    def _compute_uncertainty_predictions(self, seqs: torch.Tensor) -> torch.Tensor:
        """
        Compute epistemic uncertainty predictions for sequences.
        
        Epistemic uncertainty is quantified as the standard deviation of predictions
        across the ensemble (multiple models and/or MC dropout samples).
        
        Args:
            seqs: Tensor of sequences
            
        Returns:
            Tensor of epistemic uncertainty values (one per sequence)
        """
        if self.verbose:
            print("Computing epistemic uncertainty predictions...")
        all_uncertainties = []
        #for seq in seqs:
        for i in tqdm(
            range(0, len(seqs), self.batch_size),
            disable=not self.verbose,
            desc="Computing epistemic uncertainty"
        ):
            # Get batch
            batch_seqs = seqs[i:i + self.batch_size]
            #for each batch get the emsembl predictions
            seq_pred = []
            for model in self.models:
                if self.mc_dropout > 1:
                    #ensure model is not in evaluation mode
                    enable_mc_dropout(model)
                    for _ in range(self.mc_dropout):
                        with torch.no_grad():
                            seq_pred.append(model(batch_seqs))
                else:
                    #ensure model is in evaluation mode
                    model.eval()
                    with torch.no_grad():
                        seq_pred.append(model(batch_seqs))
            #stack predictions and calculate uncertainty
            predictions = torch.stack(seq_pred)
            #check shape - could be (num_models, batch_size, seq_len, num_tracks) or 
            # (num_models, batch_size, seq_len/num_tracks) or (num_models, batch_size)
            # convert to (num_models, batch_size, seq_len, num_tracks)
            if len(predictions.shape) == 3:
                predictions = predictions.unsqueeze(2)
            elif len(predictions.shape) == 2:
                predictions = predictions.unsqueeze(2).unsqueeze(2)
            uncertainty = torch.std(predictions, dim=0)
            #average across the tracks and seq length dimensions
            uncertainty = torch.mean(uncertainty, dim=(1, 2))
            all_uncertainties.append(uncertainty)
        all_uncertainties = torch.cat(all_uncertainties, dim=0)
        return all_uncertainties
    
    def _distill_indices(self) -> List[int]:
        """
        Perform model confidence diversity sampling using stratified epistemic 
        uncertainty sampling.
        
        This method:
        1. Computes epistemic uncertainty (standard deviation across ensemble predictions)
        2. Creates bins spanning the actual uncertainty range
        3. Assigns each sample to a bin based on its epistemic uncertainty
        4. Samples proportionally from each bin (stratified sampling)
        
        This ensures the distilled dataset maintains representation across all levels
        of model confidence, from highly confident predictions (low epistemic uncertainty)
        to highly uncertain predictions (high epistemic uncertainty/model disagreement).
        
        Returns:
            List of selected diverse indices
        """
        # Load sequences
        seqs, ids = self._load_sequences_and_indices()
        
        # Compute uncertainty predictions
        uncertainty = self._compute_uncertainty_predictions(seqs)
        uncertainty_np = uncertainty.cpu().numpy()
        
        # Create bins based on actual uncertainty range (not assuming 0-1 normalization)
        min_unc = uncertainty_np.min()
        max_unc = uncertainty_np.max()
        bins = np.linspace(min_unc, max_unc, self.n_bins + 1)
        
        # Assign each sample to a bin
        bin_assignments = np.digitize(uncertainty_np, bins) - 1
        # Clip to valid range (last bin edge can cause index = n_bins)
        bin_assignments = np.clip(bin_assignments, 0, self.n_bins - 1)
        
        # Plot uncertainty distribution if verbose
        if self.verbose:
            from matplotlib import pyplot as plt
            # Create dir if it doesn't exist
            os.makedirs(os.path.dirname(self.plt_save_path), exist_ok=True)
            # Create a figure and axes with the desired figsize and dpi
            fig, ax = plt.subplots(figsize=(10, 5), dpi=self.dpi)
            ax.hist(uncertainty_np, bins=bins, edgecolor='black', alpha=0.7)
            ax.set_title("Epistemic Uncertainty Distribution")
            ax.set_xlabel("Epistemic Uncertainty (Std Dev)")
            ax.set_ylabel("Frequency")
            ax.axvline(np.median(uncertainty_np), color='r', linestyle='--', 
                       label=f'Median: {np.median(uncertainty_np):.4f}')
            ax.axvline(np.mean(uncertainty_np), color='b', linestyle='--',
                       label=f'Mean: {np.mean(uncertainty_np):.4f}')
            ax.legend()
            plt.savefig(self.plt_save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            print(f"Epistemic uncertainty distribution saved to {self.plt_save_path}")
        
        # Perform stratified sampling from each bin
        if self.verbose:
            print(f"\nSampling {self.target_size} samples from {self.n_bins} epistemic uncertainty bins...")
            print(f"Epistemic uncertainty range: [{min_unc:.4f}, {max_unc:.4f}]")
        
        sampled_ids = []
        samples_per_bin = self.target_size // self.n_bins
        remainder = self.target_size % self.n_bins
        
        # Track bin statistics
        empty_bins = 0
        bins_with_replacement = 0
        
        for bin_idx in range(self.n_bins):
            # Get samples in this bin
            bin_mask = bin_assignments == bin_idx
            bin_sample_ids = np.where(bin_mask)[0]
            
            if len(bin_sample_ids) == 0:
                empty_bins += 1
                if self.verbose:
                    print(f"  Warning: Bin {bin_idx} is empty, skipping...")
                continue
            
            # Determine number of samples for this bin (distribute remainder evenly)
            n_samples = samples_per_bin + (1 if bin_idx < remainder else 0)
            
            # Sample from this bin (with replacement if bin is smaller than needed)
            replace = len(bin_sample_ids) < n_samples
            if replace:
                bins_with_replacement += 1
            
            sampled = np.random.choice(
                bin_sample_ids,
                size=min(n_samples, len(bin_sample_ids)) if not replace else n_samples,
                replace=replace
            )
            sampled_ids.extend(sampled.tolist())
        
        if self.verbose:
            # Print bin distribution statistics
            unique, counts = np.unique(bin_assignments, return_counts=True)
            print(f"\nEpistemic uncertainty bin statistics:")
            print(f"  Total bins: {self.n_bins}")
            print(f"  Non-empty bins: {len(unique)}")
            print(f"  Empty bins: {empty_bins}")
            print(f"  Bins requiring replacement sampling: {bins_with_replacement}")
            print(f"\nBin distribution:")
            for bin_i, count in zip(unique[:5], counts[:5]):
                bin_range_start = bins[bin_i]
                bin_range_end = bins[bin_i + 1]
                print(f"    Bin {bin_i} [{bin_range_start:.4f}, {bin_range_end:.4f}]: {count} samples")
            if len(unique) > 5:
                print(f"    ... ({len(unique) - 5} more bins)")
            print(f"\nTotal selected: {len(sampled_ids)} samples (target: {self.target_size})")
        
        # Validation: ensure we have the correct number of samples
        if len(sampled_ids) != self.target_size:
            if self.verbose:
                print(f"  Warning: Selected {len(sampled_ids)} samples, expected {self.target_size}")
                print(f"  This can happen when bins are empty. Sampling additional samples to reach target...")
            
            # If we're short, sample randomly from remaining indices to reach target
            while len(sampled_ids) < self.target_size:
                additional_needed = self.target_size - len(sampled_ids)
                additional_samples = np.random.choice(
                    len(ids),
                    size=min(additional_needed, len(ids)),
                    replace=False
                )
                sampled_ids.extend(additional_samples.tolist())
        
        return sampled_ids
