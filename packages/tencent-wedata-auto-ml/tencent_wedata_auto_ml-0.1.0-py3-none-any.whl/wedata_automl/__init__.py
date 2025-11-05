# -*- coding: utf-8 -*-
"""WeData AutoML SDK (FLAML + MLflow).

Public API:
- run_pipeline: end-to-end training + logging + registry
- train_and_select: training/selection only
- safe_print, silence_third_party_logs, mute_external_io: utilities
"""
from .pipeline import run_pipeline
from .training import train_and_select
from .logging_utils import safe_print, silence_third_party_logs, mute_external_io

__all__ = [
    "run_pipeline",
    "train_and_select",
    "safe_print",
    "silence_third_party_logs",
    "mute_external_io",
]

__version__ = "0.1.0"

