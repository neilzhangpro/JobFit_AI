"""Optimization Domain Layer — public API for the bounded context.

Re-exports value objects, entities, repository interface, factory,
and domain service so that other layers can import from
``optimization.domain`` directly.
"""

from optimization.domain.entities import OptimizationResult, OptimizationSession
from optimization.domain.factories import OptimizationSessionFactory
from optimization.domain.repository import IOptimizationRepository
from optimization.domain.services import OptimizationDomainService
from optimization.domain.value_objects import (
    ATSScore,
    GapReport,
    JDAnalysis,
    ScoreBreakdown,
    SessionStatus,
)

__all__ = [
    # Value objects
    "SessionStatus",
    "ScoreBreakdown",
    "JDAnalysis",
    "ATSScore",
    "GapReport",
    # Entities
    "OptimizationSession",
    "OptimizationResult",
    # Repository interface
    "IOptimizationRepository",
    # Factory
    "OptimizationSessionFactory",
    # Domain service
    "OptimizationDomainService",
]
