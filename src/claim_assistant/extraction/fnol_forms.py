from datetime import date, time

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


class DWCForm(BaseModel):
    employee_name: str = Field(..., description="Employee name")
    todays_date: date = Field(..., description="Today's date")
    home_address: str = Field(..., description="Street address of employee")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    zip_code: str = Field(..., description="Zip code")
    date_of_injury: date = Field(
        ...,
        description="Date when accident or illness occurred",
    )
    time_of_injury: time = Field(..., description="Specify AM or PM")
    address_and_description_of_where_injury_happened: str = Field(
        ...,
        description="Address and description of where injury happened",
    )
    describe_injury_and_part_of_body_affected: str = Field(
        ...,
        description="Describe injury and part of body affected",
    )
    social_security_number: str = Field(..., description="Employee's SSN")
    employees_email: str = Field(
        ...,
        description="Only required if notices are to be received electronically",
    )
    consent_to_receive_claim_notices_by_email_only: bool = Field(
        ...,
        description="Consent to receive claim notices by email only",
    )
    signature_of_employee: str = Field(..., description="Signature of employee")
    employer_name: str = Field(..., description="Name of employer")
    employer_address: str = Field(..., description="Employer address")
    date_employer_first_knew_of_injury: date = Field(
        ...,
        description="Date employer first knew of injury",
    )
    date_claim_form_was_provided_to_employee: date = Field(
        ...,
        description="Date claim form was provided to employee",
    )
    date_employer_received_claim_form: date = Field(
        ...,
        description="Date employer received claim form",
    )
    name_and_address_of_insurance_carrier_or_adjusting_agency: str = Field(
        ...,
        description="Name and address of insurance carrier or adjusting agency",
    )
    insurance_policy_number: str = Field(..., description="Insurance policy number")
    signature_of_employer_representative: str = Field(
        ...,
        description="Signature of employer representative",
    )
    title_of_employer_representative: str = Field(
        ...,
        description="Title of employer representative",
    )
    telephone_number_of_employer_representative: str = Field(
        ...,
        description="Telephone number of employer representative",
    )
