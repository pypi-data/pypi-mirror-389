"""
Dataset utilities for distillseq
"""

from .wrapper import DistilledDataset
from .teacher import (
    apply_teacher_predictions,
    TeacherDistilledDataset,
)

__all__ = [
    "DistilledDataset",
    "apply_teacher_predictions",
    "TeacherDistilledDataset",
]

