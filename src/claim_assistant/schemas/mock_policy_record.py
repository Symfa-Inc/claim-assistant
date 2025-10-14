from datetime import date

from pydantic import BaseModel, Field


class MockPolicyRecord(BaseModel):
    """
    Represents a single insurance policy record retrieved from the database.
    """

    policy_number: str = Field(
        ...,
        description="Unique policy identifier, typically alphanumeric (e.g., 'POL123456789').",
    )
    policy_holder_first_name: str = Field(
        ...,
        description="First name of the policyholder.",
    )
    policy_holder_last_name: str = Field(
        ...,
        description="Last name of the policyholder.",
    )
    start_date: date = Field(
        ...,
        description="Date when the policy coverage begins (ISO format: YYYY-MM-DD).",
    )
    end_date: date = Field(
        ...,
        alias="end_data",
        description="Date when the policy coverage ends (ISO format: YYYY-MM-DD).",
    )
    policy_coverage: str = Field(
        ...,
        description="Detailed description of what the policy covers.",
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "policy_number": "POL123456789",
                "policy_holder_name": "John Doe",
                "start_date": "2023-01-12",
                "end_data": "2025-01-12",
                "policy_coverage": (
                    "Work-related illness coverage including diagnostic tests, "
                    "prescribed medication, and return-to-work therapy sessions."
                ),
            },
        }
