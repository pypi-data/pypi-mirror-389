"""
Teacher distillation utilities

This module provides functionality for self-distillation by replacing ground truth
labels with predictions from a teacher model. Applied AFTER distillation method
selects samples for maximum efficiency.
"""

import torch
from torch.utils.data import Dataset, DataLoader, Subset
from typing import Optional, Union, List
from tqdm import tqdm


def apply_teacher_predictions(
    dataset: Dataset,
    indices: List[int],
    teacher_models: Union[torch.nn.Module, List[torch.nn.Module]],
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
    batch_size: int = 64,
    keep_original_labels: bool = False,
    verbose: bool = True,
    mc_dropout: int = 0
) -> 'TeacherDistilledDataset':
    """
    Apply teacher model predictions to a distilled subset of data.
    
    This function is designed to be used AFTER a distillation method has selected
    samples, making it much more efficient than computing predictions for the
    entire dataset. Handles ensemble of teachers with mean prediction.
    
    Args:
        dataset: Original PyTorch dataset with 'x' and 'y' keys
        indices: List of indices selected by distillation method
        teacher_models: Single model or list of models for ensemble
        device: Device to run models on
        batch_size: Batch size for prediction
        keep_original_labels: If True, keep original labels as 'y_true'
        verbose: Whether to print progress
        mc_dropout: Number of MC dropout samples (0 = disabled)
        
    Returns:
        TeacherDistilledDataset with soft labels
        
    Example:
        >>> # First, distill to select important samples
        >>> distiller = KmerDiversity(dataset=dataset, ratio=0.1)
        >>> indices = distiller.distill()
        >>> 
        >>> # Then apply teacher predictions only to selected samples
        >>> teacher_dataset = apply_teacher_predictions(
        ...     dataset=dataset,
        ...     indices=indices,
        ...     teacher_models=[model1, model2, model3],  # Ensemble
        ...     device='cuda'
        ... )
        >>> 
        >>> # Now train on distilled data with soft labels
        >>> train_loader = DataLoader(teacher_dataset, batch_size=32)
    """
    # Ensure teacher_models is a list
    if not isinstance(teacher_models, list):
        teacher_models = [teacher_models]
    
    # Move models to device and set mode
    for model in teacher_models:
        model.to(device)
        if mc_dropout == 0:
            model.eval()
        else:
            from ..utils.uncertainty import enable_mc_dropout
            enable_mc_dropout(model)
    
    if verbose:
        print(f"Computing teacher predictions for {len(indices)} samples...")
        if len(teacher_models) > 1:
            print(f"  Using ensemble of {len(teacher_models)} models")
        if mc_dropout > 0:
            print(f"  Using {mc_dropout} MC dropout samples per model")
    
    # Create subset of selected indices
    subset = Subset(dataset, indices)
    dataloader = DataLoader(
        subset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,  # Avoid issues with multiprocessing
        pin_memory=(device == 'cuda')
    )
    
    # Compute predictions for selected samples only
    all_predictions = []
    all_sequences = []
    all_original_labels = []
    all_metadata = []
    
    with torch.no_grad():
        for batch in tqdm(dataloader, disable=not verbose, desc="Teacher predictions"):
            # Get sequences
            if 'x' in batch:
                sequences = batch['x'].to(device)
            elif 'seq' in batch:
                sequences = batch['seq'].to(device)
            else:
                raise KeyError("Batch must contain 'x' or 'seq' key")
            
            # Collect predictions from all models
            batch_predictions = []
            
            for model in teacher_models:
                if mc_dropout > 0:
                    for _ in range(mc_dropout):
                        pred = model(sequences)
                        batch_predictions.append(pred)
                else:
                    pred = model(sequences)
                    batch_predictions.append(pred)
            
            # Compute mean prediction across ensemble
            if len(batch_predictions) > 1:
                stacked_preds = torch.stack(batch_predictions)
                mean_pred = torch.mean(stacked_preds, dim=0)
            else:
                mean_pred = batch_predictions[0]
            
            all_predictions.append(mean_pred.cpu())
            all_sequences.append(sequences.cpu())
            
            # Store original labels if requested
            if keep_original_labels:
                if 'y' in batch:
                    all_original_labels.append(batch['y'])
                elif 'target' in batch:
                    all_original_labels.append(batch['target'])
                elif 'targets' in batch:
                    all_original_labels.append(batch['targets'])
            
            # Store other metadata
            metadata = {k: v for k, v in batch.items() 
                       if k not in ['x', 'seq', 'y', 'target', 'targets']}
            if metadata:
                all_metadata.append(metadata)
    
    # Concatenate all batches
    predictions = torch.cat(all_predictions, dim=0)
    sequences = torch.cat(all_sequences, dim=0)
    
    if verbose:
        print(f"Computed predictions shape: {predictions.shape}")
        print(f"Stats - mean: {predictions.mean():.4f}, "
              f"std: {predictions.std():.4f}, "
              f"min: {predictions.min():.4f}, "
              f"max: {predictions.max():.4f}")
    
    # Create and return dataset
    original_labels = torch.cat(all_original_labels, dim=0) if all_original_labels else None
    
    return TeacherDistilledDataset(
        sequences=sequences,
        predictions=predictions,
        original_labels=original_labels,
        indices=indices,
        metadata=all_metadata if all_metadata else None
    )


class TeacherDistilledDataset(Dataset):
    """
    Dataset containing sequences with teacher predictions as labels.
    
    This is the output of apply_teacher_predictions() and contains only
    the distilled samples with soft labels from teacher model(s).
    """
    
    def __init__(
        self,
        sequences: torch.Tensor,
        predictions: torch.Tensor,
        original_labels: Optional[torch.Tensor] = None,
        indices: Optional[List[int]] = None,
        metadata: Optional[List[dict]] = None
    ):
        self.sequences = sequences
        self.predictions = predictions
        self.original_labels = original_labels
        self.indices = indices
        self.metadata = metadata
    
    def __len__(self) -> int:
        return len(self.sequences)
    
    def __getitem__(self, idx: int) -> dict:
        output = {
            'x': self.sequences[idx],
            'y': self.predictions[idx]
        }
        
        if self.original_labels is not None:
            output['y_true'] = self.original_labels[idx]
        
        if self.metadata and idx < len(self.metadata):
            # Add metadata if available
            batch_idx = idx
            for batch_meta in self.metadata:
                if batch_idx < len(list(batch_meta.values())[0]):
                    for key, value in batch_meta.items():
                        output[key] = value[batch_idx]
                    break
                batch_idx -= len(list(batch_meta.values())[0])
        
        return output
    
    def get_statistics(self) -> dict:
        """Get statistics about the distilled dataset."""
        return {
            'size': len(self),
            'sequence_shape': tuple(self.sequences.shape[1:]),
            'prediction_shape': tuple(self.predictions.shape[1:]),
            'prediction_mean': self.predictions.mean().item(),
            'prediction_std': self.predictions.std().item(),
            'prediction_min': self.predictions.min().item(),
            'prediction_max': self.predictions.max().item(),
            'has_original_labels': self.original_labels is not None
        }
    
    def save(self, filepath: str):
        """Save the distilled dataset to file."""
        torch.save({
            'sequences': self.sequences,
            'predictions': self.predictions,
            'original_labels': self.original_labels,
            'indices': self.indices,
            'metadata': self.metadata
        }, filepath)
    
    @classmethod
    def load(cls, filepath: str) -> 'TeacherDistilledDataset':
        """Load a distilled dataset from file."""
        data = torch.load(filepath)
        return cls(
            sequences=data['sequences'],
            predictions=data['predictions'],
            original_labels=data.get('original_labels'),
            indices=data.get('indices'),
            metadata=data.get('metadata')
        )
