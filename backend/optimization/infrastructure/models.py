"""SQLAlchemy ORM models for optimization_sessions and optimization_results tables."""

# TODO: Implement OptimizationSessionModel
#   - Table: optimization_sessions
#   - Columns: id, tenant_id (NOT NULL), resume_id, job_description_id, status, created_at, updated_at
#   - Indexes: tenant_id, resume_id, status
# TODO: Implement OptimizationResultModel
#   - Table: optimization_results
#   - Columns: id, session_id (FK), tenant_id (NOT NULL), ats_score, gap_report (JSON), created_at
#   - Relationship: belongs_to OptimizationSessionModel
#   - Indexes: tenant_id, session_id
