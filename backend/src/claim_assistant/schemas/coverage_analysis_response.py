from pydantic import Field

from claim_assistant.schemas.coverage_analysis_llm import CoverageAnalysisLLM
from claim_assistant.schemas.form_field import FormField
from claim_assistant.schemas.mock_policy_record import MockPolicyRecord


class CoverageAnalysisResponse(CoverageAnalysisLLM):
    """Final processor output: LLM analysis + attached context (not produced by LLM)."""

    form: list[FormField] = Field(default_factory=list)
    policy: MockPolicyRecord | None = None
