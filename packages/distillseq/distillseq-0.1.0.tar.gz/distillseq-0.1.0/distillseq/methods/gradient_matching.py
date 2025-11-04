"""
Gradient matching dataset condensation method

Based on "Dataset Condensation with Gradient Matching" (Zhao et al., 2020)
https://arxiv.org/abs/2006.05929
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import Dataset, DataLoader
from typing import Optional, Tuple
from tqdm import tqdm
import time
import copy

from .base import BaseDistiller


class GradientMatching(BaseDistiller):
    """
    Dataset condensation using gradient matching.
    
    Creates a synthetic dataset that matches the gradient distributions of
    the full dataset when training the model.
    
    Args:
        model: PyTorch model to use for gradient matching
        dataset: PyTorch dataset to distill with DNA sequences in 'x' and targets in 'y'
        ratio: Proportion of data to generate (0 < ratio < 1)
        device: Device to use ('cuda' or 'cpu')
        lr_syn: Learning rate for synthetic data optimization
        lr_net: Learning rate for network optimization  
        batch_size: Batch size for training
        iterations: Number of condensation iterations
        eval_interval: Interval for evaluation (0 to skip)
        num_eval: Number of evaluation runs
        num_workers: Number of workers for data loading
        prefetch_factor: Number of batches to prefetch per worker
        use_wandb: Whether to use W&B for tracking
        wandb_project: W&B project name
        wandb_name: W&B run name
        loss_fn: Loss function ('poisson' or 'mse')
        eval_epochs: Number of epochs for evaluation
        gradient_accumulation_steps: Gradient accumulation steps
        verbose: Whether to print progress
        
    Example:
        >>> distiller = GradientMatching(
        ...     model=my_model,
        ...     dataset=my_dataset,
        ...     ratio=0.1,
        ...     iterations=1000
        ... )
        >>> synthetic_data = distiller.create_synthetic_dataset()
    """
    
    def __init__(
        self,
        model: nn.Module,
        dataset: Dataset,
        ratio: float = 0.1,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        seed: int = 42,
        lr_syn: float = 0.1,
        lr_net: float = 0.01,
        batch_size: int = 1024,
        iterations: int = 100,
        eval_interval: int = 0,  # 0 means skip evaluation
        num_eval: int = 5,
        num_workers: int = 16,
        prefetch_factor: int = 8,
        use_wandb: bool = False,
        wandb_project: str = "distillseq",
        wandb_name: Optional[str] = None,
        loss_fn: str = "poisson",
        eval_epochs: int = 100,
        gradient_accumulation_steps: int = 1,
        verbose: bool = True
    ):
        super().__init__(
            dataset=dataset,
            ratio=ratio,
            seed=seed,
            device=device,
            verbose=verbose
        )
        
        self.model = model.to(device)
        self.lr_syn = lr_syn
        self.lr_net = lr_net
        self.batch_size = batch_size
        self.iterations = iterations
        self.eval_interval = eval_interval
        self.num_eval = num_eval
        self.eval_epochs = eval_epochs
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.use_wandb = use_wandb
        
        # Ensure model parameters have gradients
        for param in self.model.parameters():
            param.requires_grad = True
        self.model.train()
        
        # Initialize loss function
        if loss_fn.lower() == "poisson":
            self.criterion = nn.PoissonNLLLoss(log_input=False).to(device)
        elif loss_fn.lower() == "mse":
            self.criterion = nn.MSELoss().to(device)
        else:
            raise ValueError(f"Unknown loss function: {loss_fn}")
        
        # Initialize W&B if enabled
        if use_wandb:
            import wandb
            wandb.init(
                project=wandb_project,
                name=wandb_name,
                config={
                    'ratio': ratio,
                    'lr_syn': lr_syn,
                    'lr_net': lr_net,
                    'batch_size': batch_size,
                    'iterations': iterations,
                    'loss_fn': loss_fn,
                }
            )
        
        # Create DataLoader
        self.real_dataloader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            prefetch_factor=prefetch_factor,
            pin_memory=(device == 'cuda')
        )
        
        # Synthetic data (will be initialized in _distill_indices)
        self.syn_sequences = None
        self.syn_targets = None
    
    def _initialize_synthetic_data(self):
        """Initialize synthetic data from random samples."""
        if self.verbose:
            print(f"Initializing {self.target_size} synthetic samples...")
        start_time = time.time()
        
        indices = np.random.choice(len(self.dataset), self.target_size, replace=False)
        samples = [self.dataset[i] for i in indices]
        
        # Initialize sequences and targets
        self.syn_sequences = torch.stack([s['x'] for s in samples]).to(self.device)
        self.syn_sequences.requires_grad_(True)
        self.syn_targets = torch.stack([s['y'] for s in samples]).to(self.device)
        
        if self.verbose:
            print(f"Initialized in {time.time() - start_time:.2f}s")
    
    def _get_real_batch(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get a batch from the real dataset."""
        try:
            batch = next(self.real_iter)
        except (StopIteration, AttributeError):
            self.real_iter = iter(self.real_dataloader)
            batch = next(self.real_iter)
        
        sequences = batch['x'].to(self.device)
        sequences.requires_grad_(True)
        targets = batch['y'].to(self.device)
        return sequences, targets
    
    def _distill_indices(self):
        """
        Perform gradient matching condensation.
        Note: Returns empty list as this method creates synthetic data.
        """
        # Initialize synthetic data
        self._initialize_synthetic_data()
        
        # Optimizer for synthetic sequences
        optimizer_syn = optim.SGD([self.syn_sequences], lr=self.lr_syn, momentum=0.5)
        
        if self.verbose:
            print(f"Starting gradient matching on {self.device}...")
        
        pbar = tqdm(range(self.iterations + 1), desc="Condensing", disable=not self.verbose)
        
        for it in pbar:
            # Evaluation (if enabled)
            if self.eval_interval > 0 and it % self.eval_interval == 0:
                self._evaluate_synthetic_data(it)
            
            optimizer_syn.zero_grad()
            
            # Get real batch
            real_sequences, real_targets = self._get_real_batch()
            
            # Forward pass with real data
            real_output = self.model(real_sequences)
            real_loss = self.criterion(real_output, real_targets)
            
            # Get model parameters
            params = [p for p in self.model.parameters() if p.requires_grad]
            
            # Compute real gradients
            real_grads = torch.autograd.grad(
                real_loss, params,
                create_graph=False,
                retain_graph=False,
                allow_unused=True
            )
            real_grads = [g.detach().clone() if g is not None else None for g in real_grads]
            real_grads = [g for g in real_grads if g is not None]
            
            # Forward pass with synthetic data
            total_loss = torch.tensor(0.0, device=self.device)
            
            for i in range(0, len(self.syn_sequences), self.batch_size):
                batch_seq = self.syn_sequences[i:i + self.batch_size]
                batch_tgt = self.syn_targets[i:i + self.batch_size]
                
                syn_output = self.model(batch_seq)
                syn_loss = self.criterion(syn_output, batch_tgt)
                syn_loss = syn_loss / self.gradient_accumulation_steps
                
                # Compute synthetic gradients
                syn_grads = torch.autograd.grad(
                    syn_loss, params,
                    create_graph=True,
                    retain_graph=True,
                    allow_unused=True
                )
                syn_grads = [g for g in syn_grads if g is not None]
                
                # Gradient matching loss
                batch_loss = torch.tensor(0.0, device=self.device)
                for syn_g, real_g in zip(syn_grads, real_grads):
                    batch_loss += torch.mean((syn_g - real_g) ** 2)
                batch_loss = batch_loss / self.gradient_accumulation_steps
                
                # Compute gradients for synthetic sequences
                grad_syn = torch.autograd.grad(
                    batch_loss, batch_seq,
                    create_graph=False,
                    retain_graph=False
                )[0]
                
                # Accumulate gradients
                if i == 0:
                    self.syn_sequences.grad = torch.zeros_like(self.syn_sequences)
                self.syn_sequences.grad[i:i + self.batch_size] = grad_syn
                
                total_loss += batch_loss.detach()
            
            # Update synthetic data
            optimizer_syn.step()
            
            # Update progress bar
            pbar.set_postfix({'loss': f'{total_loss.item():.4f}'})
            
            if self.use_wandb:
                import wandb
                wandb.log({'train/loss': total_loss.item(), 'iteration': it})
        
        if self.use_wandb:
            import wandb
            wandb.finish()
        
        # Return empty list (not index-based)
        return []
    
    def _evaluate_synthetic_data(self, iteration: int):
        """Evaluate quality of synthetic data."""
        losses = []
        
        for _ in range(self.num_eval):
            eval_model = copy.deepcopy(self.model).to(self.device)
            eval_model.train()
            
            optimizer = optim.SGD(eval_model.parameters(), lr=self.lr_net)
            for _ in range(self.eval_epochs):
                optimizer.zero_grad()
                
                for i in range(0, len(self.syn_sequences), self.batch_size):
                    batch_seq = self.syn_sequences[i:i + self.batch_size].detach().clone()
                    batch_tgt = self.syn_targets[i:i + self.batch_size]
                    
                    output = eval_model(batch_seq)
                    loss = self.criterion(output, batch_tgt)
                    loss.backward()
                
                optimizer.step()
            
            # Evaluate on real data
            eval_model.eval()
            real_seq, real_tgt = self._get_real_batch()
            with torch.no_grad():
                output = eval_model(real_seq)
                eval_loss = self.criterion(output, real_tgt)
                losses.append(eval_loss.item())
        
        mean_loss = np.mean(losses)
        if self.verbose:
            print(f"Iteration {iteration}: Eval Loss = {mean_loss:.4f}")
        
        if self.use_wandb:
            import wandb
            wandb.log({'eval/loss': mean_loss, 'iteration': iteration})
    
    def create_synthetic_dataset(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Create and return the synthetic dataset.
        
        Returns:
            Tuple of (synthetic_sequences, synthetic_targets)
        """
        if self.syn_sequences is None:
            self.distill()
        
        return self.syn_sequences.detach(), self.syn_targets.detach()
    
    def save_synthetic_data(self, filepath: str):
        """Save synthetic data to file."""
        if self.syn_sequences is None:
            self.distill()
        
        torch.save({
            'x': self.syn_sequences.detach(),
            'y': self.syn_targets.detach()
        }, filepath)
        
        if self.verbose:
            print(f"Saved synthetic data to {filepath}")

