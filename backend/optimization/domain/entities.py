"""Domain entities for optimization.

OptimizationSession (Aggregate Root) with status transitions,
OptimizationResult (Entity).
"""

# TODO: Implement OptimizationSession aggregate root
#   - Status transitions: pending -> processing -> completed/failed
#   - Business invariants: cannot modify completed sessions
#   - Methods: start_processing(), complete(), fail()
# TODO: Implement OptimizationResult entity
#   - Contains final scores, gap analysis, recommendations
#   - Immutable once created
