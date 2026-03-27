from pydantic import BaseModel, Field


class CoverageAnalysisLLM(BaseModel):
    """Structured output for policy coverage analysis."""

    executive_summary: str = Field(
        ...,
        description=(
            "A concise analytical summary explaining whether "
            "the claim appears covered under the policy terms."
        ),
    )
    conclusion: str = Field(
        ...,
        pattern="^(positive|negative|uncertain)$",
        description=(
            "Result of analysis: 'positive', 'negative', or 'uncertain' if validation "
            "confidence is too low due to name/OCR ambiguity."
        ),
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0–1) reflecting certainty of claimant-policy match.",
    )
