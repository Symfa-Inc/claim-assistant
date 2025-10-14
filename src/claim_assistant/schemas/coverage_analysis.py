from pydantic import BaseModel, Field


class CoverageAnalysis(BaseModel):
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
        pattern="^(positive|negative)$",
        description=(
            "Binary conclusion: 'positive' if coverage likely applies, "
            "'negative' if it likely does not."
        ),
    )

    @classmethod
    def openai_schema(cls) -> dict:
        """Return the OpenAI-compatible JSON schema definition."""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "coverage_analysis",
                "schema": cls.model_json_schema(),
            },
        }
