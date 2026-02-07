"""LangGraph state machine definition.

Flow: JDAnalysis -> ResumeRetrieval -> BulletRewriting ->
ATSScoring -> ScoreCheck -> GapAnalysis -> ResultAggregation.
"""

# TODO: Implement LangGraph state machine
#   - Define State class with all required fields
#   - Nodes: jd_analysis, resume_retrieval, bullet_rewriting,
#     ats_scoring, score_check, gap_analysis, result_aggregation
#   - Edges: define flow between nodes based on conditions
#   - Conditional edges: score_check -> gap_analysis
#     (if score < threshold) or result_aggregation
#     (if score >= threshold)
#   - Error handling: catch node failures, route to error state
