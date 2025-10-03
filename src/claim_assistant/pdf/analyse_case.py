import json
from datetime import datetime
from typing import Any, Optional

from openai import OpenAI

from claim_assistant.pdf.settings import OpenAISettings


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date safely in ISO format (YYYY-MM-DD)."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return None


def llm_coverage_analysis(
    claim_injury_desc: str,
    claim_injury_place: str,
    policy_coverage: str,
) -> str:
    """
    Use OpenAI LLM to analyze whether the reported case
    appears covered by the policy. The output is advisory,
    highlighting possible coverage and potential reasons for denial.
    """
    settings = OpenAISettings()
    client = OpenAI(api_key=settings.openai_api_key)
    prompt = f"""
    You are an insurance adjuster assistant.
    Analyze the insurance policy coverage and the reported injury.

    Policy coverage description:
    {policy_coverage}

    Claim injury description:
    {claim_injury_desc}

    Claim injury location:
    {claim_injury_place}

    Task:
    - Explain whether the injury and place plausibly fall under the policy coverage.
    - Identify possible reasons for denial (e.g., location mismatch, type of injury not covered).
    - Keep the response advisory in tone, not a final decision.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # you can swap model name if needed
        messages=[
            {
                "role": "system",
                "content": "You are a helpful insurance coverage analyst.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=1000,
    )

    return response.choices[0].message.content.strip()


def validate_claim(
    claim: dict[str, Any],
    policies: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Validate a claim dict against policies from JSON database.
    Enrich claim dict with policy data and adjuster advice.
    """

    # Step 1: Policy Lookup
    matching_policies = [
        p for p in policies if p["policy_number"] == claim["insurance_policy_number"]
    ]

    if not matching_policies:
        claim["adjuster_advice"] = "Policy not found in database."
        return claim

    # If multiple policies with same number, pick latest end_date
    policy = max(
        matching_policies,
        key=lambda p: parse_date(p.get("end_date", "1900-01-01")) or datetime.min,
    )

    # Add policy details to claim
    claim["policy_holder_name"] = policy["policy_holder_name"]
    claim["start_date"] = policy["start_date"]
    claim["end_date"] = policy["end_date"]
    claim["policy_coverage"] = policy["policy_coverage"]

    # Step 2: Name Verification
    if (
        claim["employee_name"].strip().lower()
        != policy["policy_holder_name"].strip().lower()
    ):
        claim["adjuster_advice"] = (
            "Policy number found, but employee name differs from policy holder."
        )
        return claim

    # Step 3: Date Coverage Check
    date_of_injury = parse_date(claim["date_of_injury"])
    start_date = parse_date(policy["start_date"])
    end_date = parse_date(policy["end_date"])

    if not (date_of_injury and start_date and end_date):
        claim["adjuster_advice"] = "Date parsing error in claim or policy."
        return claim

    if not (start_date <= date_of_injury <= end_date):
        claim["adjuster_advice"] = (
            "Incident date not covered by policy validity period."
        )
        return claim

    # Step 4: Coverage Analysis
    analysis = llm_coverage_analysis(
        claim.get("describe_injury_and_part_of_body_affected", ""),
        claim.get("address_and_description_of_where_injury_happened", ""),
        policy["policy_coverage"],
    )
    claim["adjuster_advice"] = analysis

    return claim


# ------------------------------
if __name__ == "__main__":
    import json

    policies_json = """
    [
      {
        "policy_number": "SIC123456789",
        "policy_holder_name": "John Smith",
        "start_date": "2023-05-15",
        "end_date": "2024-05-15",
        "policy_coverage": "Workplace injury compensation including medical expenses, rehabilitation services, and wage replacement."
      },
      {
        "policy_number": "POL123456789",
        "policy_holder_name": "John Doe",
        "start_date": "2022-03-20",
        "end_date": "2024-03-20",
        "policy_coverage": "Occupational accident insurance covering hospital bills, temporary disability payments, and emergency treatment costs."
      }
    ]
    """
    policies = json.loads(policies_json)

    # 1. Valid claim
    claim_valid = {
        "employee_name": "John Doe",
        "todays_date": "2024-05-16",
        "home_address": "123 Main St",
        "city": "Los Angeles",
        "state": "CA",
        "zip_code": "90001",
        "date_of_injury": "2023-09-01",
        "time_of_injury": "AM",
        "address_and_description_of_where_injury_happened": "On-site warehouse accident",
        "describe_injury_and_part_of_body_affected": "Back injury from lifting",
        "social_security_number": "123-45-6789",
        "employees_email": "johndoe@email.com",
        "consent_to_receive_claim_notices_by_email_only": True,
        "signature_of_employee": "John Doe",
        "employer_name": "ABC Corp",
        "employer_address": "456 Business Rd",
        "date_employer_first_knew_of_injury": "2023-09-02",
        "date_claim_form_was_provided_to_employee": "2023-09-03",
        "date_employer_received_claim_form": "2023-09-03",
        "name_and_address_of_insurance_carrier_or_adjusting_agency": "Best Insurance Co.",
        "insurance_policy_number": "POL123456789",
        "signature_of_employer_representative": "Jane Smith",
        "title_of_employer_representative": "HR Manager",
        "telephone_number_of_employer_representative": "555-123-4567",
    }

    # 2. Policy not found
    claim_policy_not_found = dict(claim_valid)
    claim_policy_not_found["insurance_policy_number"] = "NONEXISTENT123"

    # 3. Name mismatch
    claim_name_mismatch = dict(claim_valid)
    claim_name_mismatch["employee_name"] = "Jane Doe"

    # 4. Date outside coverage
    claim_date_outside = dict(claim_valid)
    claim_date_outside["date_of_injury"] = "2025-01-01"

    # 5. Valid policy but possibly outside coverage (off-site accident vs. workplace only)
    claim_offsite = dict(claim_valid)
    claim_offsite["address_and_description_of_where_injury_happened"] = (
        "Off-site company retreat"
    )
    claim_offsite["describe_injury_and_part_of_body_affected"] = (
        "Slip and fall, leg injury"
    )

    claims_to_test = {
        "Valid claim": claim_valid,
        "Policy not found": claim_policy_not_found,
        "Name mismatch": claim_name_mismatch,
        "Date outside coverage": claim_date_outside,
        "Off-site accident": claim_offsite,
    }

    for label, claim in claims_to_test.items():
        print("=" * 40)
        print(f"Test case: {label}")
        enriched_claim = validate_claim(claim, policies)
        print(json.dumps(enriched_claim, indent=2))
