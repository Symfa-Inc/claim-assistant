from __future__ import annotations

from pydantic import BaseModel, Field
from agentic_doc.parse import parse


class FLExtractionSchema(BaseModel):
    first_name: str = Field(
        ...,
        description='The first name of the person who submits the insurance claim.',
        title='Claim Submitter First Name',
    )
    middle_name: str = Field(
        ...,
        description='The middle name of the person who submits the insurance claim.',
        title='Claim Submitter Middle Name',
    )
    last_name: str = Field(
        ...,
        description='The last name of the person who submits the insurance claim.',
        title='Claim Submitter Last Name',
    )
    social_security_number: str = Field(
        ...,
        description='The social security number of the person who submits the insurance claim.',
        title='Social Security Number',
    )
    date_of_birth: str = Field(
        ...,
        description='The date of birth of the person who submits the insurance claim.',
        title='Date of Birth',
    )

# Parse a file and extract the fields
results = parse("/home/maken/symfa/claim-assistant/data/forms/FL/form_hw_POL987654321.pdf", extraction_model=FLExtractionSchema)
print("Full Results:")
print(results)
fields = results[0].extraction

# Return the value of the extracted fields
print("Extracted Fields:")
print(fields)    

# Return the value of the extracted field metadata
print("\nExtraction Metadata:")
print(results[0].extraction_metadata)