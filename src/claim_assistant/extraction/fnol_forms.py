from datetime import date

from pydantic import BaseModel, Field


class HDIForm(BaseModel):
    named_insured: str = Field(..., description="Named insured on the policy")
    policy_number: str = Field(..., description="Policy number")
    policy_effective_date: date = Field(..., description="Policy effective date")
    line_of_business: str = Field(..., description="Line of business")
    insured_contact_information_name: str = Field(
        ...,
        description="Insured contact information - name",
    )
    insured_contact_information_email: str = Field(
        ...,
        description="Insured contact information - email",
    )
    insured_contact_information_phone: str = Field(
        ...,
        description="Insured contact information - phone",
    )
    insured_contact_information_extension: str = Field(
        ...,
        description="Insured contact information - extension",
    )
    report_type: str = Field(..., description="Report type")
    claimant: str = Field(..., description="Claimant information")
    date_of_loss: date = Field(..., description="Date of loss")
    loss_location: str = Field(..., description="Loss location")
    loss_description: str = Field(..., description="Loss description")
    other_details: str = Field(..., description="Other details")
    claim_submitted_by_company_name: str = Field(
        ...,
        description="Claim submitted by - company name",
    )
    claim_submitted_by_name: str = Field(..., description="Claim submitted by - name")
    claim_submitted_by_email: str = Field(..., description="Claim submitted by - email")
    claim_submitted_by_number: str = Field(
        ...,
        description="Claim submitted by - phone number",
    )
    claim_submitted_by_extension: str = Field(
        ...,
        description="Claim submitted by - extension",
    )


class CIDForm(BaseModel):
    insured_name: str = Field(..., description="Insured name")
    policy_number: str = Field(..., description="Policy number")
    contact_person: str = Field(..., description="Contact person")
    primary_phone: str = Field(..., description="Primary phone number")
    secondary_phone: str = Field(..., description="Secondary phone number")
    email: str = Field(..., description="Email address")
    address_line_1: str = Field(..., description="Address line 1")
    address_line_2: str = Field(..., description="Address line 2")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    zip_code: str = Field(..., description="ZIP code")
    brief_description_of_incident: str = Field(
        ...,
        description="Brief description of incident",
    )
