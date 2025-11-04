"""
NeuralkAI SDK main module.

This module provides the main interface for interacting with the Neuralk AI platform.
It handles authentication and provides access to various services through specialized handlers.
"""

import logging
from pathlib import Path

from .utils.docs import add_submodules_to_docstring
from .neuralk import Neuralk
from .model.analysis import Analysis
from .model.dataset import Dataset
from .model.organization import Organization
from .model.project import Project
from .model.project_file import ProjectFile
from .exceptions import NeuralkException
from ._classifier import Classifier

VERSION_PATH = Path(__file__).resolve().parent / "VERSION.txt"
__version__ = VERSION_PATH.read_text(encoding="utf-8").strip()


__all__ = [
    "Neuralk",
    "Analysis",
    "Dataset",
    "Organization",
    "Project",
    "ProjectFile",
    "NeuralkException",
    "Classifier",
    "logger",
]
