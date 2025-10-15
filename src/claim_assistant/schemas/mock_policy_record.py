from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field

from claim_assistant import PROJECT_DIR


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
    policy_file_name: str | None = Field(
        ...,
        description="Name of the policy document PDF stored locally.",
    )

    def get_policy_path(self) -> Path | None:
        if not self.policy_file_name:
            return None
        return Path(PROJECT_DIR) / "data" / "policies" / self.policy_file_name

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "policy_number": "POL123456789",
                "policy_holder_name": "John Doe",
                "start_date": "2023-01-12",
                "end_data": "2025-01-12",
                "policy_file_name": "policy1.pdf",
            },
        }
