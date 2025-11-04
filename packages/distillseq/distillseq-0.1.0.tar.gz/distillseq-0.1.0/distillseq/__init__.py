"""
distillseq: Data distillation methods for genomic sequence-to-function models
"""

__version__ = "0.1.0"

from .methods.gradient_matching import GradientMatching
from .methods.kmer_diversity import KmerDiversity
from .methods.glm_diversity import GLMDiversity
from .methods.random_sampling import RandomSampling
from .methods.model_confidence_diversity import ModelConfidenceDiversity
from .datasets.teacher import (
    apply_teacher_predictions,
    TeacherDistilledDataset,
)
from .datasets.wrapper import DistilledDataset

__all__ = [
    "GradientMatching",
    "KmerDiversity",
    "GLMDiversity",
    "RandomSampling",
    "ModelConfidenceDiversity",
    "apply_teacher_predictions",
    "TeacherDistilledDataset",
    "DistilledDataset",
]

