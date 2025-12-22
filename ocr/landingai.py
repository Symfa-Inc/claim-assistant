from __future__ import annotations

from pydantic import BaseModel, Field
from agentic_doc.parse import parse


class SampleExtractionSchema(BaseModel):
    accountHolder: str = Field(
        ...,
        description='The full name of the person who holds the bank account.',
        title='Account Holder Name',
    )
    accountNumber: str = Field(
        ...,
        description='The bank account number associated with the account holder.',
        title='Bank Account Number',
    )

# Parse a file and extract the fields
results = parse("estatement.pdf", extraction_model=SampleExtractionSchema)
fields = results[0].extraction

# Return the value of the extracted fields
print("Extracted Fields:")
print(fields)    

# Return the value of the extracted field metadata
print("\nExtraction Metadata:")
print(results[0].extraction_metadata)