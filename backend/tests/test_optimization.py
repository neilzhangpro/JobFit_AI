"""Tests for the Optimization bounded context — A1 Domain Models.

Covers:
    - Value object immutability and validation (SessionStatus, ScoreBreakdown,
      JDAnalysis, ATSScore, GapReport)
    - Entity status transitions (PENDING → PROCESSING → COMPLETED / FAILED)
    - Domain event emission on transitions
    - Factory default initialization
    - Domain service scoring logic and retry policy
    - AgentExecutionError attributes
    - Multi-tenant ID propagation at domain level
    - A2 BaseAgent, score_check_router, result_aggregator_node
    - A3 JDAnalyzerAgent and jd_analyzer_node
"""

import uuid
from unittest.mock import patch

import pytest

from optimization.domain.entities import OptimizationResult, OptimizationSession
from optimization.domain.factories import OptimizationSessionFactory
from optimization.domain.services import OptimizationDomainService
from optimization.domain.value_objects import (
    ATSScore,
    GapReport,
    JDAnalysis,
    ScoreBreakdown,
    SessionStatus,
)
from shared.domain.exceptions import AgentExecutionError, ValidationError

# ---------------------------------------------------------------------------
# Shared test constants and helpers
# ---------------------------------------------------------------------------

TENANT_A_ID = uuid.uuid4()
TENANT_B_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
RESUME_ID = uuid.uuid4()
SAMPLE_JD = (
    "We are looking for a Python backend engineer with 5+ years of "
    "experience in AWS, Docker, and microservices architecture."
)


def _make_session(
    tenant_id: uuid.UUID = TENANT_A_ID,
    user_id: uuid.UUID = USER_ID,
    resume_id: uuid.UUID = RESUME_ID,
    jd_text: str = SAMPLE_JD,
) -> OptimizationSession:
    """Helper — create a valid session via the factory."""
    return OptimizationSessionFactory.create_session(
        tenant_id=tenant_id,
        user_id=user_id,
        resume_id=resume_id,
        jd_text=jd_text,
    )


def _make_breakdown(
    keywords: float = 0.85,
    skills: float = 0.80,
    experience: float = 0.75,
    formatting: float = 0.90,
) -> ScoreBreakdown:
    return ScoreBreakdown(
        keywords=keywords,
        skills=skills,
        experience=experience,
        formatting=formatting,
    )


def _make_jd_analysis() -> JDAnalysis:
    return JDAnalysis(
        hard_skills=("Python", "AWS", "Docker"),
        soft_skills=("leadership", "communication"),
        responsibilities=("Design microservices", "Lead code reviews"),
        qualifications=("5+ years backend", "BS Computer Science"),
        keyword_weights=(("Python", 0.95), ("AWS", 0.85), ("Docker", 0.70)),
    )


def _make_gap_report() -> GapReport:
    return GapReport(
        missing_skills=("Kubernetes", "Terraform"),
        recommendations=(
            "Add Kubernetes experience from side projects",
            "Highlight infrastructure-as-code experience",
        ),
        transferable_skills=("Docker", "AWS CloudFormation"),
        priority=(("Kubernetes", "high"), ("Terraform", "medium")),
    )


def _make_result(session_id: uuid.UUID) -> OptimizationResult:
    breakdown = _make_breakdown()
    return OptimizationResult(
        session_id=session_id,
        tenant_id=TENANT_A_ID,
        jd_analysis=_make_jd_analysis(),
        optimized_sections={
            "experience": [
                "Built microservices on AWS ECS, reducing deploy time by 40%",
            ],
            "skills_summary": [
                "Python | AWS | Docker | FastAPI | Microservices",
            ],
        },
        ats_score=ATSScore(overall=0.82, breakdown=breakdown),
        gap_report=_make_gap_report(),
        rewrite_attempts=1,
        total_tokens_used=4500,
    )


# ===================================================================
# SessionStatus
# ===================================================================


class TestSessionStatus:
    """Tests for SessionStatus enum transition rules."""

    def test_pending_to_processing_allowed(self) -> None:
        assert SessionStatus.PENDING.can_transition_to(SessionStatus.PROCESSING)

    def test_processing_to_completed_allowed(self) -> None:
        assert SessionStatus.PROCESSING.can_transition_to(SessionStatus.COMPLETED)

    def test_processing_to_failed_allowed(self) -> None:
        assert SessionStatus.PROCESSING.can_transition_to(SessionStatus.FAILED)

    def test_pending_to_completed_forbidden(self) -> None:
        assert not SessionStatus.PENDING.can_transition_to(SessionStatus.COMPLETED)

    def test_pending_to_failed_forbidden(self) -> None:
        assert not SessionStatus.PENDING.can_transition_to(SessionStatus.FAILED)

    def test_completed_is_terminal(self) -> None:
        for target in SessionStatus:
            assert not SessionStatus.COMPLETED.can_transition_to(target)

    def test_failed_is_terminal(self) -> None:
        for target in SessionStatus:
            assert not SessionStatus.FAILED.can_transition_to(target)


# ===================================================================
# ScoreBreakdown
# ===================================================================


class TestScoreBreakdown:
    """Tests for ScoreBreakdown value object."""

    def test_valid_creation(self) -> None:
        bd = _make_breakdown()
        assert bd.keywords == 0.85
        assert bd.formatting == 0.90

    def test_immutability(self) -> None:
        bd = _make_breakdown()
        with pytest.raises(AttributeError):
            bd.keywords = 0.99  # type: ignore[misc]

    def test_weighted_overall_all_ones(self) -> None:
        bd = ScoreBreakdown(keywords=1.0, skills=1.0, experience=1.0, formatting=1.0)
        assert bd.weighted_overall() == pytest.approx(1.0)

    def test_weighted_overall_correct_weights(self) -> None:
        bd = ScoreBreakdown(keywords=0.8, skills=0.6, experience=0.4, formatting=1.0)
        expected = 0.8 * 0.35 + 0.6 * 0.30 + 0.4 * 0.25 + 1.0 * 0.10
        assert bd.weighted_overall() == pytest.approx(expected)

    def test_score_below_zero_raises(self) -> None:
        with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
            ScoreBreakdown(keywords=-0.1, skills=0.8, experience=0.7, formatting=0.9)

    def test_score_above_one_raises(self) -> None:
        with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
            ScoreBreakdown(keywords=1.1, skills=0.8, experience=0.7, formatting=0.9)

    def test_equality_by_value(self) -> None:
        a = _make_breakdown(0.8, 0.7, 0.6, 0.9)
        b = _make_breakdown(0.8, 0.7, 0.6, 0.9)
        assert a == b


# ===================================================================
# JDAnalysis
# ===================================================================


class TestJDAnalysis:
    """Tests for JDAnalysis value object."""

    def test_valid_creation(self) -> None:
        jd = _make_jd_analysis()
        assert "Python" in jd.hard_skills
        assert len(jd.keyword_weights) == 3

    def test_immutability(self) -> None:
        jd = _make_jd_analysis()
        with pytest.raises(AttributeError):
            jd.hard_skills = ("Java",)  # type: ignore[misc]

    def test_empty_hard_skills_raises(self) -> None:
        with pytest.raises(ValidationError, match="hard_skills must not be empty"):
            JDAnalysis(
                hard_skills=(),
                soft_skills=("leadership",),
                responsibilities=("Design",),
                qualifications=("5+ years",),
                keyword_weights=(),
            )

    def test_empty_soft_skills_raises(self) -> None:
        with pytest.raises(ValidationError, match="soft_skills must not be empty"):
            JDAnalysis(
                hard_skills=("Python",),
                soft_skills=(),
                responsibilities=("Design",),
                qualifications=("5+ years",),
                keyword_weights=(),
            )

    def test_invalid_keyword_weight_raises(self) -> None:
        with pytest.raises(ValidationError, match="keyword weight"):
            JDAnalysis(
                hard_skills=("Python",),
                soft_skills=("leadership",),
                responsibilities=("Design",),
                qualifications=("5+ years",),
                keyword_weights=(("Python", 1.5),),
            )


# ===================================================================
# ATSScore
# ===================================================================


class TestATSScore:
    """Tests for ATSScore value object."""

    def test_valid_creation(self) -> None:
        bd = _make_breakdown()
        score = ATSScore(overall=0.82, breakdown=bd)
        assert score.overall == 0.82

    def test_meets_threshold_above(self) -> None:
        bd = _make_breakdown()
        assert ATSScore(overall=0.85, breakdown=bd).meets_threshold(0.75)

    def test_meets_threshold_below(self) -> None:
        bd = _make_breakdown()
        assert not ATSScore(overall=0.60, breakdown=bd).meets_threshold(0.75)

    def test_meets_threshold_exact(self) -> None:
        bd = _make_breakdown()
        assert ATSScore(overall=0.75, breakdown=bd).meets_threshold(0.75)

    def test_overall_out_of_range_raises(self) -> None:
        bd = _make_breakdown()
        with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
            ATSScore(overall=1.5, breakdown=bd)


# ===================================================================
# GapReport
# ===================================================================


class TestGapReport:
    """Tests for GapReport value object."""

    def test_valid_creation(self) -> None:
        gr = _make_gap_report()
        assert "Kubernetes" in gr.missing_skills
        assert len(gr.recommendations) == 2

    def test_high_priority_skills(self) -> None:
        gr = _make_gap_report()
        assert "Kubernetes" in gr.high_priority_skills()
        assert "Terraform" not in gr.high_priority_skills()

    def test_invalid_priority_level_raises(self) -> None:
        with pytest.raises(ValidationError, match="'high', 'medium', or 'low'"):
            GapReport(
                missing_skills=("Go",),
                recommendations=("Learn Go",),
                transferable_skills=(),
                priority=(("Go", "critical"),),
            )


# ===================================================================
# OptimizationSession (Aggregate Root)
# ===================================================================


class TestOptimizationSession:
    """Tests for session status transitions and domain events."""

    def test_new_session_is_pending(self) -> None:
        session = _make_session()
        assert session.status == SessionStatus.PENDING
        assert session.tenant_id == TENANT_A_ID

    def test_session_has_uuid_id(self) -> None:
        assert isinstance(_make_session().id, uuid.UUID)

    def test_start_processing(self) -> None:
        session = _make_session()
        session.start_processing()
        assert session.status == SessionStatus.PROCESSING
        assert session.updated_at is not None

    def test_complete_with_result(self) -> None:
        session = _make_session()
        session.start_processing()
        result = _make_result(session.id)
        session.complete(result)
        assert session.status == SessionStatus.COMPLETED
        assert session.result is result

    def test_fail_with_message(self) -> None:
        session = _make_session()
        session.start_processing()
        session.fail("LLM timeout")
        assert session.status == SessionStatus.FAILED
        assert session.error_message == "LLM timeout"

    def test_pending_to_completed_raises(self) -> None:
        session = _make_session()
        with pytest.raises(ValidationError, match="Cannot transition"):
            session.complete(_make_result(session.id))

    def test_completed_to_processing_raises(self) -> None:
        session = _make_session()
        session.start_processing()
        session.complete(_make_result(session.id))
        with pytest.raises(ValidationError, match="Cannot transition"):
            session.start_processing()

    def test_failed_is_terminal(self) -> None:
        session = _make_session()
        session.start_processing()
        session.fail("Error")
        assert session.is_terminal is True
        with pytest.raises(ValidationError):
            session.start_processing()

    def test_short_jd_text_raises(self) -> None:
        with pytest.raises(ValidationError, match="at least 50 characters"):
            _make_session(jd_text="Too short")

    def test_domain_events_emitted_on_transitions(self) -> None:
        session = _make_session()
        session.start_processing()
        session.complete(_make_result(session.id))
        events = session.collect_events()
        assert len(events) == 2
        assert events[0].event_type == "optimization.session.processing_started"
        assert events[1].event_type == "optimization.session.completed"

    def test_collect_events_clears_list(self) -> None:
        session = _make_session()
        session.start_processing()
        assert len(session.collect_events()) == 1
        assert len(session.collect_events()) == 0

    def test_identity_equality(self) -> None:
        a, b = _make_session(), _make_session()
        assert a != b  # different UUIDs


# ===================================================================
# OptimizationResult
# ===================================================================


class TestOptimizationResult:
    """Tests for OptimizationResult entity."""

    def test_create_result(self) -> None:
        sid = uuid.uuid4()
        result = _make_result(sid)
        assert result.session_id == sid
        assert result.total_tokens_used == 4500
        assert "experience" in result.optimized_sections

    def test_default_empty_sections(self) -> None:
        result = OptimizationResult(session_id=uuid.uuid4(), tenant_id=TENANT_A_ID)
        assert result.optimized_sections == {}
        assert result.total_tokens_used == 0


# ===================================================================
# OptimizationSessionFactory
# ===================================================================


class TestOptimizationSessionFactory:
    """Tests for factory creation logic."""

    def test_creates_pending_session(self) -> None:
        session = OptimizationSessionFactory.create_session(
            tenant_id=TENANT_A_ID,
            user_id=USER_ID,
            resume_id=RESUME_ID,
            jd_text=SAMPLE_JD,
        )
        assert session.status == SessionStatus.PENDING
        assert session.result is None
        assert session.error_message is None

    def test_preserves_ids(self) -> None:
        session = OptimizationSessionFactory.create_session(
            tenant_id=TENANT_A_ID,
            user_id=USER_ID,
            resume_id=RESUME_ID,
            jd_text=SAMPLE_JD,
        )
        assert session.tenant_id == TENANT_A_ID
        assert session.user_id == USER_ID
        assert session.resume_id == RESUME_ID

    def test_none_tenant_id_raises(self) -> None:
        with pytest.raises(ValidationError, match="tenant_id is required"):
            OptimizationSessionFactory.create_session(
                tenant_id=None,  # type: ignore[arg-type]
                user_id=USER_ID,
                resume_id=RESUME_ID,
                jd_text=SAMPLE_JD,
            )


# ===================================================================
# OptimizationDomainService
# ===================================================================


class TestOptimizationDomainService:
    """Tests for domain service scoring and retry logic."""

    def test_validate_score_valid(self) -> None:
        for val in (0.0, 0.5, 1.0):
            OptimizationDomainService.validate_score(val)

    def test_validate_score_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            OptimizationDomainService.validate_score(1.5)
        with pytest.raises(ValidationError):
            OptimizationDomainService.validate_score(-0.1)

    def test_validate_status_transition_valid(self) -> None:
        OptimizationDomainService.validate_status_transition(
            SessionStatus.PENDING,
            SessionStatus.PROCESSING,
        )

    def test_validate_status_transition_invalid(self) -> None:
        with pytest.raises(ValidationError, match="Invalid status transition"):
            OptimizationDomainService.validate_status_transition(
                SessionStatus.PENDING,
                SessionStatus.COMPLETED,
            )

    def test_calculate_overall_score(self) -> None:
        bd = ScoreBreakdown(keywords=0.8, skills=0.6, experience=0.4, formatting=1.0)
        expected = round(0.8 * 0.35 + 0.6 * 0.30 + 0.4 * 0.25 + 1.0 * 0.10, 4)
        result = OptimizationDomainService.calculate_overall_score(bd)
        assert result == pytest.approx(expected)

    def test_create_ats_score(self) -> None:
        bd = _make_breakdown()
        score = OptimizationDomainService.create_ats_score(bd)
        assert isinstance(score, ATSScore)
        assert score.breakdown == bd

    def test_should_retry_below_threshold(self) -> None:
        assert (
            OptimizationDomainService.should_retry_rewrite(
                ats_score=0.60,
                rewrite_attempts=0,
            )
            is True
        )

    def test_should_not_retry_above_threshold(self) -> None:
        assert (
            OptimizationDomainService.should_retry_rewrite(
                ats_score=0.80,
                rewrite_attempts=0,
            )
            is False
        )

    def test_should_not_retry_max_attempts(self) -> None:
        assert (
            OptimizationDomainService.should_retry_rewrite(
                ats_score=0.60,
                rewrite_attempts=2,
                max_attempts=2,
            )
            is False
        )


# ===================================================================
# AgentExecutionError
# ===================================================================


class TestAgentExecutionError:
    """Tests for the shared AgentExecutionError exception."""

    def test_error_attributes(self) -> None:
        err = AgentExecutionError("JDAnalyzer", "LLM timeout", recoverable=False)
        assert err.agent_name == "JDAnalyzer"
        assert err.recoverable is False
        assert "JDAnalyzer" in str(err)
        assert "LLM timeout" in str(err)

    def test_recoverable_flag(self) -> None:
        err = AgentExecutionError("ATSScorer", "Bad JSON", recoverable=True)
        assert err.recoverable is True


# ===================================================================
# Multi-Tenant Isolation (domain-level ID propagation)
# ===================================================================


class TestTenantIsolation:
    """Verify tenant_id is set on domain entities at creation time."""

    def test_session_carries_tenant_id(self) -> None:
        assert _make_session(tenant_id=TENANT_A_ID).tenant_id == TENANT_A_ID

    def test_result_carries_tenant_id(self) -> None:
        result = OptimizationResult(session_id=uuid.uuid4(), tenant_id=TENANT_B_ID)
        assert result.tenant_id == TENANT_B_ID

    def test_different_tenants_get_different_sessions(self) -> None:
        sa = _make_session(tenant_id=TENANT_A_ID)
        sb = _make_session(tenant_id=TENANT_B_ID)
        assert sa.tenant_id != sb.tenant_id


# ===================================================================
# A2 — BaseAgent Template Method
# ===================================================================


class _StubAgent:
    """Minimal concrete agent for testing BaseAgent behaviour.

    Uses deferred import so the test module stays loadable even when
    ``langchain_openai`` is absent from the dev environment.
    """

    def __init__(
        self,
        prepare_result: str = "prompt",
        execute_result: str = "raw",
        parse_result: dict[str, object] | None = None,
        *,
        raise_in: str | None = None,
    ) -> None:
        from optimization.infrastructure.agents.base_agent import (
            BaseAgent,
        )

        outer = self  # capture for inner class

        class _Inner(BaseAgent):
            """Concrete stub for testing."""

            def prepare(self, state: dict[str, object]) -> str:
                if outer.raise_in == "prepare":
                    raise ValueError("prepare boom")
                return outer.prepare_result

            def execute(self, prompt: str) -> str:
                if outer.raise_in == "execute":
                    raise RuntimeError("execute boom")
                return outer.execute_result

            def parse_output(self, raw_output: str) -> dict[str, object]:
                if outer.raise_in == "parse":
                    raise KeyError("parse boom")
                return outer.parse_result or {}

        self.prepare_result = prepare_result
        self.execute_result = execute_result
        self.parse_result = parse_result or {}
        self.raise_in = raise_in
        self.agent = _Inner()


class TestBaseAgent:
    """Tests for BaseAgent template method, error wrapping, and helpers."""

    def test_run_happy_path(self) -> None:
        """run() returns parse_output result on success."""
        stub = _StubAgent(parse_result={"key": "value"})
        result = stub.agent.run({"input": "data"})
        assert result == {"key": "value"}

    def test_run_wraps_prepare_error(self) -> None:
        """run() wraps prepare errors in AgentExecutionError."""
        stub = _StubAgent(raise_in="prepare")
        with pytest.raises(AgentExecutionError, match="prepare boom"):
            stub.agent.run({})

    def test_run_wraps_execute_error(self) -> None:
        """run() wraps execute errors in AgentExecutionError."""
        stub = _StubAgent(raise_in="execute")
        with pytest.raises(AgentExecutionError, match="execute boom"):
            stub.agent.run({})

    def test_run_wraps_parse_error(self) -> None:
        """run() wraps parse_output errors in AgentExecutionError."""
        stub = _StubAgent(raise_in="parse")
        with pytest.raises(AgentExecutionError, match="parse boom"):
            stub.agent.run({})

    def test_track_tokens_extracts_total(self) -> None:
        """_track_tokens returns total from response metadata."""
        stub = _StubAgent()
        metadata: dict[str, object] = {
            "token_usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
        }
        total = stub.agent._track_tokens(metadata, "TestAgent")
        assert total == 150

    def test_track_tokens_missing_metadata(self) -> None:
        """_track_tokens returns 0 when metadata is empty."""
        stub = _StubAgent()
        assert stub.agent._track_tokens({}, "TestAgent") == 0

    def test_get_model_returns_openai_by_default(self) -> None:
        """_get_model returns ChatOpenAI with correct params."""
        stub = _StubAgent()
        model = stub.agent._get_model("gpt-4o-mini", temperature=0.0)
        assert model.model_name == "gpt-4o-mini"
        assert model.temperature == 0.0

    def test_get_model_respects_temperature(self) -> None:
        """_get_model passes temperature to the model."""
        stub = _StubAgent()
        model = stub.agent._get_model("gpt-4o", temperature=0.7)
        assert model.temperature == 0.7


# ===================================================================
# A2 — Score Check Router
# ===================================================================


class TestScoreCheckRouter:
    """Tests for score_check_router routing logic."""

    def test_routes_to_gap_when_score_above_threshold(self) -> None:
        from optimization.infrastructure.agents.graph import (
            score_check_router,
        )

        state = {
            "ats_score": 0.80,
            "score_threshold": 0.75,
            "rewrite_attempts": 0,
            "max_rewrite_attempts": 2,
        }
        assert score_check_router(state) == "proceed_to_gap"

    def test_routes_to_retry_when_below_threshold(self) -> None:
        from optimization.infrastructure.agents.graph import (
            score_check_router,
        )

        state = {
            "ats_score": 0.60,
            "score_threshold": 0.75,
            "rewrite_attempts": 0,
            "max_rewrite_attempts": 2,
        }
        assert score_check_router(state) == "retry_rewrite"

    def test_routes_to_gap_when_retries_exhausted(self) -> None:
        from optimization.infrastructure.agents.graph import (
            score_check_router,
        )

        state = {
            "ats_score": 0.60,
            "score_threshold": 0.75,
            "rewrite_attempts": 2,
            "max_rewrite_attempts": 2,
        }
        assert score_check_router(state) == "proceed_to_gap"

    def test_routes_to_gap_at_exact_threshold(self) -> None:
        from optimization.infrastructure.agents.graph import (
            score_check_router,
        )

        state = {
            "ats_score": 0.75,
            "score_threshold": 0.75,
            "rewrite_attempts": 0,
            "max_rewrite_attempts": 2,
        }
        assert score_check_router(state) == "proceed_to_gap"

    def test_uses_defaults_for_missing_fields(self) -> None:
        """Router gracefully handles missing state fields."""
        from optimization.infrastructure.agents.graph import (
            score_check_router,
        )

        # Empty state → score=0.0, threshold=0.75, attempts=0, max=2
        assert score_check_router({}) == "retry_rewrite"


# ===================================================================
# A2 — Result Aggregator Node
# ===================================================================


class TestResultAggregatorNode:
    """Tests for result_aggregator_node data assembly."""

    def test_assembles_final_result(self) -> None:
        from typing import cast

        from optimization.infrastructure.agents.graph import (
            OptimizationState,
            result_aggregator_node,
        )

        state = cast(
            OptimizationState,
            {
                "jd_analysis": {"hard_skills": ["Python"]},
                "optimized_sections": {"experience": ["bullet"]},
                "ats_score": 0.82,
                "score_breakdown": {"keywords": 0.9},
                "gap_report": {"missing_skills": ["K8s"]},
                "rewrite_attempts": 1,
                "token_usage": {"jd_analyzer": 500, "rewriter": 1500},
                "total_tokens_used": 2000,
                "errors": [],
            },
        )
        result = result_aggregator_node(state)

        fr = result["final_result"]
        assert fr["ats_score"] == 0.82
        assert fr["rewrite_attempts"] == 1
        assert fr["jd_analysis"] == {"hard_skills": ["Python"]}
        assert fr["optimized_sections"] == {"experience": ["bullet"]}

    def test_computes_total_tokens_from_usage_dict(self) -> None:
        from typing import cast

        from optimization.infrastructure.agents.graph import (
            OptimizationState,
            result_aggregator_node,
        )

        state = cast(
            OptimizationState,
            {"token_usage": {"a": 100, "b": 200, "c": 300}},
        )
        result = result_aggregator_node(state)
        assert result["total_tokens_used"] == 600

    def test_handles_empty_state_gracefully(self) -> None:
        from typing import cast

        from optimization.infrastructure.agents.graph import (
            OptimizationState,
            result_aggregator_node,
        )

        state = cast(OptimizationState, {})
        result = result_aggregator_node(state)
        fr = result["final_result"]
        assert fr["ats_score"] == 0.0
        assert fr["optimized_sections"] == {}
        assert fr["errors"] == []
        assert result["total_tokens_used"] == 0


# ===================================================================
# A3 — JD Analyzer Agent
# ===================================================================

_VALID_JD_JSON = """{
  "hard_skills": ["Python", "AWS", "Docker"],
  "soft_skills": ["leadership", "communication"],
  "responsibilities": ["Design microservices", "Lead code reviews"],
  "qualifications": ["5+ years backend", "BS Computer Science"],
  "keyword_weights": { "Python": 0.95, "AWS": 0.85, "Docker": 0.70 }
}"""


class TestJDAnalyzerAgent:
    """Tests for JDAnalyzerAgent with mocked LLM."""

    def test_valid_jd_returns_jd_analysis_and_token_usage(self) -> None:
        """With valid JSON from LLM, run() returns jd_analysis and token_usage."""
        from optimization.infrastructure.agents.jd_analyzer import (
            JDAnalyzerAgent,
        )

        state = {"jd_text": "We need a Python backend engineer with 5+ years."}
        with patch.object(
            JDAnalyzerAgent,
            "execute",
            return_value=_VALID_JD_JSON,
        ):
            agent = JDAnalyzerAgent()
            result = agent.run(state)

        assert "jd_analysis" in result
        jd = result["jd_analysis"]
        assert jd["hard_skills"] == ["Python", "AWS", "Docker"]
        assert "Python" in jd["keyword_weights"]
        assert jd["keyword_weights"]["Python"] == 0.95
        assert "token_usage" in result
        assert "jd_analyzer" in result["token_usage"]

    def test_short_jd_raises_validation_error(self) -> None:
        """prepare() raises ValidationError when jd_text is too short."""
        from optimization.infrastructure.agents.jd_analyzer import (
            JDAnalyzerAgent,
        )

        agent = JDAnalyzerAgent()
        state = {"jd_text": "Short"}
        with pytest.raises(ValidationError, match="too short"):
            agent.run(state)

    def test_empty_jd_raises_validation_error(self) -> None:
        """prepare() raises ValidationError for empty jd_text."""
        from optimization.infrastructure.agents.jd_analyzer import (
            JDAnalyzerAgent,
        )

        agent = JDAnalyzerAgent()
        state = {"jd_text": ""}
        with pytest.raises(ValidationError, match="too short"):
            agent.run(state)

    def test_malformed_json_raises_agent_execution_error(self) -> None:
        """parse_output() raises AgentExecutionError when LLM returns invalid JSON."""
        from optimization.infrastructure.agents.jd_analyzer import (
            JDAnalyzerAgent,
        )

        state = {"jd_text": "A" * 60}
        with patch.object(
            JDAnalyzerAgent,
            "execute",
            return_value="not valid json {{{",
        ):
            agent = JDAnalyzerAgent()
            with pytest.raises(AgentExecutionError, match="Invalid JSON"):
                agent.run(state)

    def test_missing_required_key_raises_agent_execution_error(
        self,
    ) -> None:
        """parse_output() raises when a required key is missing."""
        from optimization.infrastructure.agents.jd_analyzer import (
            JDAnalyzerAgent,
        )

        state = {"jd_text": "B" * 60}
        bad_json = (
            '{"hard_skills": [], "soft_skills": [], '
            '"responsibilities": [], "qualifications": []}'
        )
        with patch.object(JDAnalyzerAgent, "execute", return_value=bad_json):
            agent = JDAnalyzerAgent()
            with pytest.raises(AgentExecutionError, match="keyword_weights"):
                agent.run(state)

    def test_prompt_includes_system_instructions(self) -> None:
        """prepare() returns jd_text; full prompt built in execute (arch doc §3.2)."""
        from optimization.infrastructure.agents.jd_analyzer import (
            JDAnalyzerAgent,
        )

        jd_text = "We are looking for a Python backend engineer with AWS."
        state = {"jd_text": jd_text}
        agent = JDAnalyzerAgent()
        prompt = agent.prepare(state)
        assert prompt == jd_text
        assert "Python" in prompt


class TestJDAnalyzerNode:
    """Tests for jd_analyzer_node as LangGraph node."""

    def test_node_returns_partial_state_with_jd_analysis(self) -> None:
        """jd_analyzer_node returns dict with jd_analysis and token_usage."""
        from optimization.infrastructure.agents.jd_analyzer import (
            jd_analyzer_node,
        )

        state = {"jd_text": "Python backend engineer with 5+ years experience."}
        with patch(
            "optimization.infrastructure.agents.jd_analyzer.JDAnalyzerAgent.execute",
            return_value=_VALID_JD_JSON,
        ):
            result = jd_analyzer_node(state)

        assert "jd_analysis" in result
        assert result["jd_analysis"]["hard_skills"] == [
            "Python",
            "AWS",
            "Docker",
        ]
        assert "token_usage" in result
