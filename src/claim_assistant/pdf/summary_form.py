from pydantic import BaseModel, Field


class SummaryForm(BaseModel):
    employee_name: str = Field(..., description="Employee name")
    todays_date: str = Field(..., description="Today's date")
    home_address: str = Field(..., description="Street address of employee")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    zip_code: str = Field(..., description="Zip code")
    date_of_injury: str = Field(
        ...,
        description="Date when accident or illness occurred",
    )
    time_of_injury: str = Field(..., description="AM or PM")
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
    # signature_of_employee: str = Field(..., description="Signature of employee")
    employer_name: str = Field(..., description="Name of employer")
    employer_address: str = Field(..., description="Employer address")
    date_employer_first_knew_of_injury: str = Field(
        ...,
        description="Date employer first knew of injury",
    )
    date_claim_form_was_provided_to_employee: str = Field(
        ...,
        description="Date claim form was provided to employee",
    )
    date_employer_received_claim_form: str = Field(
        ...,
        description="Date employer received claim form",
    )
    name_and_address_of_insurance_carrier_or_adjusting_agency: str = Field(
        ...,
        description="Name and address of insurance carrier or adjusting agency",
    )
    insurance_policy_number: str = Field(..., description="Insurance policy number")
    # signature_of_employer_representative: str = Field(
    #     ...,
    #     description="Signature of employer representative",
    # )
    title_of_employer_representative: str = Field(
        ...,
        description="Title of employer representative",
    )
    telephone_number_of_employer_representative: str = Field(
        ...,
        description="Telephone number of employer representative",
    )
