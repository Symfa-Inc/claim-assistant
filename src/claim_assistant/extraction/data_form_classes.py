from datetime import date, time

from pydantic import BaseModel, Field


class AllianzForm(BaseModel):
    policy_number: str = Field(..., description="Policy number")
    incident_number: str = Field(..., description="Incident number")
    employer_name: str = Field(..., description="Employer name")
    full_name_of_worker: str = Field(..., description="Full name of worker")
    gender: str = Field(..., description="Gender")
    address: str = Field(..., description="Address")
    state: str = Field(..., description="State")
    postcode: str = Field(..., description="Postcode")
    telephone_work: str = Field(..., description="Telephone work")
    telephone_home: str = Field(..., description="Telephone home")
    telephone_mobile: str = Field(..., description="Telephone mobile")
    email: str = Field(..., description="Email")
    date_of_birth: str = Field(..., description="Date of birth")
    country_of_birth: str = Field(..., description="Country of birth")
    language: str = Field(..., description="Language")
    is_an_interpreter_required: bool = Field(
        ...,
        description="Is an interpreter required?",
    )
    are_you_temporarily_in_australia_on_a_visa: bool = Field(
        ...,
        description="Are you temporarily in Australia on a visa?",
    )
    if_yes_expiry_date_of_visa: str = Field(
        ...,
        description="Expiry date of visa if applicable",
    )
    visa_type: str = Field(..., description="Visa type")
    marital_status: str = Field(..., description="Marital status")
    dependent_details: list[dict[str, str | date]] = Field(
        ...,
        description="Dependent details",
    )
    how_did_the_injury_occur: str = Field(..., description="How did the injury occur?")
    what_were_you_doing_when_the_injury_happened: str = Field(
        ...,
        description="What were you doing when the injury happened? (e.g., slipped when climbing a ladder)",
    )
    parts_of_body_injured: str = Field(..., description="Part(s) of body injured")
    was_this_part_of_your_body_fully_functional_before_the_injury: bool = Field(
        ...,
        description="Was this part of your body fully functional before the injury?",
    )
    if_no_please_give_details: str = Field(..., description="If no, provide details")
    address_where_the_injury_happened: str = Field(
        ...,
        description="Address where the injury happened (if different to work address)",
    )
    address_where_the_injury_happened_state: str = Field(
        ...,
        description="State where the injury happened (if different to work address)",
    )
    address_where_the_injury_happened_postcode: str = Field(
        ...,
        description="Postcode where the injury happened (if different to work address)",
    )
    date_of_injury: date = Field(..., description="Date of injury")
    time_of_injury: time = Field(..., description="Time of injury")
    did_anyone_see_your_injury_occur: bool = Field(
        ...,
        description="Did anyone see your injury occur?",
    )
    if_yes_please_provide_their_names: list[str] = Field(
        ...,
        description="If someone has seen you injury occured, please provide their names",
    )
    person_at_workplace_you_reported_the_injury_to_name: str = Field(
        ...,
        description="Name of the person at workplace you reported the injury to",
    )
    person_at_workplace_you_reported_the_injury_to_job_title: str = Field(
        ...,
        description="Job title of the person at workplace you reported the injury to",
    )
    person_at_workplace_you_reported_the_injury_to_date_reported: str = Field(
        ...,
        description="The date when you reported the injury to the person",
    )
    nominated_treating_doctor_name: str = Field(
        ...,
        description="Name of nominated treating doctor",
    )
    nominated_treating_doctor_telephone: str = Field(
        ...,
        description="Telephone of nominated treating doctor",
    )
    have_you_previously_suffered_any_similar_injuries_or_conditions: bool = Field(
        ...,
        description="Previous similar injuries",
    )
    if_yes_please_give_details: str = Field(
        ...,
        description="If yes, provide details (e.g. when this happened)",
    )
    do_you_have_a_second_job_with_another_employer: bool = Field(
        ...,
        description="Do you have a second job?",
    )
    name_of_second_employer: str = Field(
        ...,
        description="Name of second employer, if applicable",
    )
    contact_name: str = Field(
        ...,
        description="Contact name of second employer, if applicable",
    )
    telephone: str = Field(..., "Contact telephone of second employer, if applicable")
    average_weekly_earnings_from_this_job: str = Field(
        ...,
        description="Average weekly earnings from this job",
    )
    average_weekly_hours_from_this_job: int = Field(
        ...,
        description="Average weekly hours from this job",
    )
    declaration_name: str = Field(..., description="Worker's name for declaration")
    declaration_date: str = Field(
        ...,
        description="The date when the declaration was signed",
    )
    authority_name: str = Field(..., description="Authority name")
    authority_injury_sustained_on: date = Field(
        ...,
        description="The date when the injury occured for authority",
    )
    date_this_form_was_provided_to_employer: str = Field(
        ...,
        description="Date form was provided to employer",
    )
    received_by_employer_name: str = Field(
        ...,
        description="Received by employer name of the employer",
    )
    received_by_employer_job_title: str = Field(
        ...,
        description="Received by employer job title of the emploer",
    )
    received_by_employer_date: str = Field(..., description="Received by employer date")
    additional_information: str = Field(..., description="Additional information")


class WorkSafeFormData(BaseModel):
    worker_title: str = Field(..., description="Mr, Mrs, Ms, Miss, Mx")
    worker_last_name: str = Field(..., description="Worker surname")
    worker_first_name: str = Field(..., description="Worker given name(s)")
    other_names_known_by: str = Field(..., description="e.g., maiden name")
    gender: str = Field(..., description="Male, Female, Gender diverse")
    date_of_birth: date = Field(..., description="Date of birth")
    age: int = Field(..., description="Age")
    home_address: str = Field(..., description="Street, city")
    suburb_home_address: str = Field(..., description="Suburb")
    postcode_home_address: str = Field(..., description="Postcode")
    postal_address: str = Field(..., description="If different from home address")
    suburb_postal_address: str = Field(..., description="Suburb")
    postcode_postal_address: str = Field(..., description="Postcode")
    contact_details_home_number: str = Field(..., description="Home number")
    contact_details_mobile_number: str = Field(..., description="Mobile number")
    contact_details_work_number: str = Field(..., description="Work number")
    contact_details_email: str = Field(..., description="Email")
    country_of_birth: str = Field(..., description="Country of birth")
    language_spoken_at_home: str = Field(..., description="Language spoken at home")
    marital_status: str = Field(..., description="Single, Married, De facto")
    dependants_spouse: bool = Field(..., description="Spouse (Y/N)")
    dependants_children: bool = Field(..., description="Children (Y/N)")
    number_of_children: int = Field(
        ...,
        description="Number of children, if applicable",
    )
    dates_of_birth_of_children: list[date] = Field(
        ...,
        description="Dates of birth of children, if applicable",
    )
    employer_name: str = Field(..., description="Employer at time of injury/disease")
    occupation_and_job_title: str = Field(
        ...,
        description="Worker's role at time of injury/disease",
    )
    employment_type: str = Field(
        ...,
        description="Direct employee, working director, contractor, sub-contractor, employee of contractor, visa worker, other",
    )
    apprentice_or_trainee: bool = Field(..., description="Apprentice or trainee")
    employment_status: str = Field(
        ...,
        description="Full time, part time, permanent, temporary, casual",
    )

    other_paid_employment: bool = Field(
        ...,
        description="If yes, provide employer details",
    )
    other_employer_name: str = Field(..., description="Employer name")
    other_employer_address: str = Field(..., description="Employer address")
    other_employer_suburb: str = Field(..., description="Employer suburb")
    other_employer_state: str = Field(..., description="Employer state")
    other_employer_postcode: str = Field(..., description="Employer postcode")

    where_did_injury_or_disease_occur: str = Field(
        ...,
        description="Options include workplace, elsewhere, break, travelling, training, working from home",
    )
    exact_location_of_occurrence: str = Field(
        ...,
        description="Exact location of occurrence",
    )
    date_injury_disease_occured: date = Field(..., description="Date")
    time_injury_disease_occurred: time = Field(..., description="Time with AM/PM")
    incident_description: str = Field(
        ...,
        description="What worker was doing, how injury happened, objects/substances involved",
    )

    part_of_body_affected: str = Field(..., description="Part of body affected")
    type_of_injury_disease: str = Field(..., description="e.g., fracture, burn")
    most_serious_injury_if_multiple: str = Field(
        ...,
        description="Most serious injury (if multiple)",
    )

    witness_name: str = Field(..., description="Name of witness")
    witness_address: str = Field(..., description="Address of witness")
    witness_suburb: str = Field(..., description="Suburb of witness")
    witness_state: str = Field(..., description="State of witness")
    witness_postcode: str = Field(..., description="Postcode of witness")
    witness_home_number: str = Field(..., description="Home number of witness")
    witness_mobile_number: str = Field(..., description="Mobile number of witness")
    witness_work_number: str = Field(..., description="Work number of witness")
    witness_email: str = Field(..., description="Email of witness")

    reported_to_employer: bool = Field(
        ...,
        description="Did you report the injury or disease to your employer",
    )
    reported_to_employer_no: str = Field(..., description="If no, why not")
    reported_to_employer_yes_date: date = Field(..., description="If yes, provide date")
    reported_to_employer_yes_time: time = Field(..., description="If yes, provide time")
    name_person_reported_to: str = Field(
        ...,
        description="Name of the person reported to",
    )
    position_person_reported_to: str = Field(
        ...,
        description="Position of the person reported to",
    )

    stopped_work_due_to_injury_disease: bool = Field(
        ...,
        description="Yes/No, if yes date/time, return to work details",
    )
    date_stopped_work: date = Field(..., description="If yes, provide date")
    time_stopped_work: time = Field(..., description="If yes, provide time")
    time_started_shift: time = Field(
        ...,
        description="If yes, provide time started shift",
    )
    started_back_at_work: bool = Field(..., description="If yes, provide date/time")
    date_started_back_at_work: date = Field(..., description="If yes, provide date")

    medical_treatment_received: bool = Field(..., description="Yes/No")
    medical_treatment_professional_name: str = Field(
        ...,
        description="Name of medical professional who provided treatment",
    )
    medical_treatment_professional_address: str = Field(
        ...,
        description="Address of medical professional who provided treatment",
    )
    medical_treatment_professional_suburb: str = Field(
        ...,
        description="Suburb of medical professional who provided treatment",
    )
    medical_treatment_professional_state: str = Field(
        ...,
        description="State of medical professional who provided treatment",
    )
    medical_treatment_professional_postcode: str = Field(
        ...,
        description="Postcode of medical professional who provided treatment",
    )
    dates_treated: list[date] = Field(..., description="Dates you were treated")

    hospital_admission: bool = Field(..., description="Yes/No")
    hospital_admission_name: str = Field(..., description="Name of hospital")
    hospital_admission_address: str = Field(..., description="Address of hospital")
    hospital_admission_suburb: str = Field(..., description="Suburb of hospital")
    hospital_admission_state: str = Field(..., description="State of hospital")
    hospital_admission_postcode: str = Field(..., description="Postcode of hospital")

    still_receiving_treatment: bool = Field(
        ...,
        description="Yes/No, if yes provide details",
    )
    still_receiving_treatment_person_name: str = Field(
        ...,
        description="Name of medical professional who is currently treating you",
    )
    still_receiving_treatment_person_address: str = Field(
        ...,
        description="Address of medical professional who is currently treating you",
    )
    still_receiving_treatment_person_suburb: str = Field(
        ...,
        description="Suburb of medical professional who is currently treating you",
    )
    still_receiving_treatment_person_state: str = Field(
        ...,
        description="State of medical professional who is currently treating you",
    )
    still_receiving_treatment_person_postcode: str = Field(
        ...,
        description="Postcode of medical professional who is currently treating you",
    )

    claiming_for: str = Field(
        ...,
        description="Time off work, medical expenses, rehab, hospital",
    )

    similar_injury_disease_before: bool = Field(
        ...,
        description="Yes/No, previous treatment details",
    )
    similar_injury_disease_before_professional_name: str = Field(
        ...,
        description="Name of medical professional who provided treatment",
    )
    similar_injury_disease_before_professional_address: str = Field(
        ...,
        description="Address of medical professional who provided treatment",
    )
    similar_injury_disease_before_professional_suburb: str = Field(
        ...,
        description="Suburb of medical professional who provided treatment",
    )
    similar_injury_disease_before_professional_state: str = Field(
        ...,
        description="State of medical professional who provided treatment",
    )
    similar_injury_disease_before_professional_postcode: str = Field(
        ...,
        description="Postcode of medical professional who provided treatment",
    )
    type_injury_disease_before: str = Field(
        ...,
        description="Type of injury/disease before",
    )
    date_injury_disease_before: date = Field(
        ...,
        description="Date of injury/disease before",
    )

    previous_workers_compensation_claims: bool = Field(..., description="Yes/No")
    previous_workers_compensation_claim_date: date = Field(
        ...,
        description="Date of previous claim",
    )
    previous_workers_compensation_claim_employers_name: str = Field(
        ...,
        description="The name of the employer for the previous claim",
    )
    previous_workers_compensation_claim_insurer_name: str = Field(
        ...,
        description="The name of the insurer for the previous claim, if known",
    )

    injury_in_previous_employment: bool = Field(..., description="Yes/No")
    injury_in_previous_employment_employer_name: str = Field(
        ...,
        description="Name of employer where injury occurred",
    )
    injury_in_previous_employment_employer_suburb_town: str = Field(
        ...,
        description="Suburb/Town of employer where injury occurred",
    )
    injury_in_previous_employment_period_of_employment: str = Field(
        ...,
        description="Period of employment with the employer where injury occurred",
    )
    injury_in_previous_employment_insurer_name: str = Field(
        ...,
        description="Name of insurer for the employer where injury occurred, if known",
    )

    workers_authority_and_declaration_name: str = Field(
        ...,
        description="Worker's name for consent for release of medical/personal information and declaration of truth. Requires signature, date, DOB, injury details.",
    )
    workers_authority_and_declaration_surname: str = Field(
        ...,
        description="Worker's surname for consent for release of medical/personal information and declaration of truth. Requires signature, date, DOB, injury details.",
    )
    workers_authority_and_declaration_date_of_birth: date = Field(
        ...,
        description="Worker's date of birth for consent for release of medical/personal information and declaration of truth. Requires signature, date, DOB, injury details.",
    )
    workers_authority_and_declaration_date_of_injury: date = Field(
        ...,
        description="Worker's date of injury for consent for release of medical/personal information and declaration of truth. Requires signature, date, DOB, injury details.",
    )
    workers_authority_and_declaration_type_injury_disease: str = Field(
        ...,
        description="Worker's type of injury/disease for consent for release of medical/personal information and declaration of truth. Requires signature, date, DOB, injury details.",
    )
    workers_authority_and_declaration_signature: str = Field(
        ...,
        description="Worker's signature for consent for release of medical/personal information and declaration of truth. Requires signature, date, DOB, injury details.",
    )
    workers_authority_and_declaration_date: date = Field(
        ...,
        description="Worker's date for consent for release of medical/personal information and declaration of truth. Requires signature, date, DOB, injury details.",
    )

    claim_forwarded_to_employer_date: date = Field(
        ...,
        description="Date claim form was forwarded to employer",
    )
    claim_forwarded_to_employer_type: str = Field(
        ...,
        description="Type of how claim was forwarded to employer (posted, by hand, email)",
    )

    worker_representative_name: str = Field(
        ...,
        description="Name of person completing form for the injured or diseased person",
    )
    worker_representative_address: str = Field(
        ...,
        description="Address of person completing form for the injured or diseased person",
    )
    worker_representative_suburb: str = Field(
        ...,
        description="Suburb of person completing form for the injured or diseased person",
    )
    worker_representative_state: str = Field(
        ...,
        description="State of person completing form for the injured or diseased person",
    )
    worker_representative_postcode: str = Field(
        ...,
        description="Postcode of person completing form for the injured or diseased person",
    )

    employer_report_notifiable_incident: bool = Field(
        ...,
        description="Is the injury/disease notifiable to NT WorkSafe? If yes, provide date and reference number",
    )
    employer_report_notifiable_incident_date: date = Field(
        ...,
        description="Date of employer report for notifiable incident",
    )
    employer_report_notifiable_incident_reference_number: str = Field(
        ...,
        description="Reference number for employer report of notifiable incident",
    )

    employer_business_entity_name: str = Field(..., description="Business entity name")
    employer_business_trading_name: str = Field(
        ...,
        description="Business trading name",
    )
    employer_abn: str = Field(..., description="Australian business number")
    employer_acn: str = Field(
        ...,
        description="Australian company number, if applicable",
    )
    employer_address: str = Field(..., description="Street address of employer")
    employer_suburb: str = Field(..., description="Suburb of employer")
    employer_state: str = Field(..., description="State of employer")
    employer_postcode: str = Field(..., description="Postcode of employer")
    employer_work_number: str = Field(..., description="Employer work number")
    employer_mobile_number: str = Field(..., description="Employer mobile number")
    employer_fax_number: str = Field(..., description="Employer fax number")
    employer_email: str = Field(..., description="Employer email")
    employer_contact_person_name: str = Field(..., description="Contact person name")
    employer_contact_person_position: str = Field(
        ...,
        description="Contact person position",
    )
    employer_date_claim_received: str = Field(..., description="Date claim received")

    workers_compensation_insurer_name: str = Field(..., description="Insurer name")
    workers_compensation_policy_number: str = Field(..., description="Policy number")
    workers_compensation_policy_expiry_date: date = Field(
        ...,
        description="Policy expiry date",
    )

    injured_worker_gross_weekly_remuneration_before_injury: float = Field(
        ...,
        description="Gross weekly remuneration before injury",
    )
    injured_worker_allowance_included: bool = Field(
        ...,
        description="Is allowance included in gross weekly remuneration?",
    )
    injured_worker_allowance_details: str = Field(
        ...,
        description="Type of allowance (e.g., travel, tool, clothing)",
    )
    injured_worker_work_hours_per_week: float = Field(
        ...,
        description="Number of work hours per week",
    )
    injured_worker_overtime: bool = Field(
        ...,
        description="Does the worker normally work overtime or shift work",
    )
    injured_worker_no_money_benefits: bool = Field(
        ...,
        description="Does the worker normally receive any non-monetary benefits?",
    )
    injured_worker_market_value: float = Field(
        ...,
        description="If yes, provide the market value of the worker",
    )
    injured_worker_section: str = Field(
        ...,
        description="Section of the business where the worker works",
    )
    injured_worker_section_address: str = Field(
        ...,
        description="Address of the section where the worker works",
    )
    injured_worker_section_suburb: str = Field(
        ...,
        description="Suburb of the section where the worker works",
    )
    injured_worker_section_state: str = Field(
        ...,
        description="State of the section where the worker works",
    )
    injured_worker_section_postcode: str = Field(
        ...,
        description="Postcode of the section where the worker works",
    )
    injured_worker_section_number_of_employed_people: str = Field(
        ...,
        description="Select range (1–4, 5–9, 10–19, etc.)",
    )
    injured_worker_start_date: date = Field(
        ...,
        description="Worker employment start date",
    )
    injured_worker_a_contractor: bool = Field(
        ...,
        description="Is the worker a contractor?",
    )
    injured_worker_on_a_visa: bool = Field(
        ...,
        description="Is the worker temporarily in Australia on a visa?",
    )
    injured_worker_visa_expiry_date: date = Field(..., description="Visa expiry date")
    injured_worker_industry_type: str = Field(
        ...,
        description="Industry type where the worker works",
    )

    declaration_employer_name: str = Field(..., description="Name")
    declaration_employer_signature: str = Field(..., description="Signature")
    declaration_employer_date: date = Field(..., description="Date")
    declaration_employer_position: str = Field(..., description="Position")
    declaration_employer_date_claim_forwarded_to_insurer: date = Field(
        ...,
        description="Date when claim was forwarded to insurer",
    )
    declaration_employer_type_forwarded: str = Field(
        ...,
        description="Type of how claim was forwarded to insurer (posted, by hand, email)",
    )

    additional_information: str = Field(
        ...,
        description="Additional information to workers compensation claim form ",
    )
