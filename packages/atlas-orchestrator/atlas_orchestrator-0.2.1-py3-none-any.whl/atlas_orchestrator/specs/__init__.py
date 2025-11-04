"""Specification service exports."""

from .generator import SpecificationGenerator
from .models import (
    ModuleCoverage,
    RequirementTrace,
    SpecificationArtifact,
    SpecificationDocument,
    SpecificationMetadata,
    SpecModule,
)
from .repository import SpecificationRepository
from .requirements import Requirement, RequirementsCatalog
from .service import SpecificationCoverageError, SpecificationService

__all__ = [
    "ModuleCoverage",
    "Requirement",
    "RequirementTrace",
    "RequirementsCatalog",
    "SpecModule",
    "SpecificationArtifact",
    "SpecificationCoverageError",
    "SpecificationDocument",
    "SpecificationMetadata",
    "SpecificationRepository",
    "SpecificationService",
    "SpecificationGenerator",
]
