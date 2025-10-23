import json
import logging
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel, Field

from claim_assistant import PROJECT_DIR
from claim_assistant.data.settings import OpenAISettings



# ----------------------------------------------------------------------
# Pydantic schema for structured LLM output
# ----------------------------------------------------------------------
class FieldAnswer(BaseModel):
    order: int = Field(..., description="Order index from form definition.")
    text: str = Field(..., description="Field text label.")
    answer: str | bool | None = Field(..., description="Generated answer content.")

class GeneratedFormAnswers(BaseModel):
    answers: list[FieldAnswer]

    @classmethod
    def openai_schema(cls) -> dict:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "generated_form_answers",
                "schema": cls.model_json_schema(),
            },
        }

# ----------------------------------------------------------------------
# Script configuration
# ----------------------------------------------------------------------
SAMPLES_DIR = Path(PROJECT_DIR) / "data/samples"
FORMS_DIR = Path(PROJECT_DIR) / "data/forms_tmp"  # Adjust if forms live elsewhere

logger = logging.getLogger("sample_generator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

client = OpenAI(api_key=OpenAISettings().openai_api_key)

# ----------------------------------------------------------------------
# Main generator
# ----------------------------------------------------------------------
def generate_sample(form_path: Path, policy: dict) -> list[dict]:
    """Ask LLM to generate realistic filled answers for a form/policy pair."""
    with form_path.open("r", encoding="utf-8") as f:
        form_def = json.load(f)

    form_name = form_path.parent.name
    logger.info(f"Generating filled form for {form_name} and policy {policy['policy_number']}")

    # Prompt
    prompt = (
        "You are generating a realistic **filled insurance claim form** for synthetic evaluation.\n"
        "You are given:\n"
        "1. A blank form definition describing the structure of fields.\n"
        "2. An insurance policy record with coverage details and holder identity.\n\n"
        "Your task:\n"
        "- Fill in **every important field** with consistent, plausible, and complete information.\n"
        "- The resulting form must represent a **coherent and valid claim scenario**.\n\n"
        "Filling rules:\n"
        "- Always include a meaningful value for the following critical fields: first name, last name, date(s), "
        "policy number, description of injury, and location of incident.\n"
        "- Do not leave any critical fields blank. Use realistic placeholder data (addresses, emails, etc.) "
        "for less critical fields.\n"
        "- Dates must be valid and consistent (e.g., injury date within policy coverage period, "
        "employer notification after injury date, claim form received later).\n"
        "- If a boolean field is unclear, assign the most probable value (e.g., False by default).\n"
        "- Maintain linguistic and contextual consistency throughout (names, locations, etc.).\n"
        "- Preserve the field 'order' and 'text' exactly as in the form definition.\n\n"
        "Return strictly a JSON object with one key 'answers' — a list of objects with:\n"
        "{ order, text, answer } for each field.\n\n"
        f"Policy info:\n"
        f"Policy Number: {policy['policy_number']}\n"
        f"Holder: {policy['policy_holder_first_name']} {policy['policy_holder_last_name']}\n"
        f"Coverage: {policy['start_date']} to {policy['end_data']}\n\n"
        f"Form definition:\n{json.dumps(form_def, indent=2)}\n\n"
        "Rules:\n"
        "- Ensure the generated date_of_incident lies within the coverage period.\n"
        "- Use the policy holder name and policy number where relevant.\n"
    )

    response = client.responses.parse(
        model="gpt-5-nano-2025-08-07",
        input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        text_format=GeneratedFormAnswers,
    )

    parsed = response.output_parsed
    if isinstance(parsed, GeneratedFormAnswers):
        return [item.dict() for item in parsed.answers]
    else:
        logger.error("Unexpected model output structure.")
        return []

# ----------------------------------------------------------------------
# Execution entry
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Explicit policy examples
    policies = [
        {
            "policy_number": "SIC123456789",
            "policy_holder_first_name": "John",
            "policy_holder_last_name": "Smith",
            "start_date": "2023-05-15",
            "end_data": "2024-05-15",
            "policy_coverage": "POLICYHOLDER NOTICE  \nPursuant to the California Insurance Code, this document provides an explanation of workers’ compensation rating laws.  \nInsurers establish their own rates, file them with the commissioner, and are subject to review. The commissioner may disapprove rates or classifications that threaten solvency or create a monopoly.  \nPure premium rates developed by rating organizations are advisory only.  \nA uniform experience rating plan applies to all eligible policyholders, adjusting premiums based on claim history.  \nStandard classification systems group policyholders by industry similarities, subject to commissioner approval.  \nRates and classifications must not be unfairly discriminatory or violate civil rights statutes.  \nAn appeal process exists for disputes over policy rating; the insurer must respond within 30 days, and unsatisfied parties may appeal to the insurance commissioner.\n\n**Notice of Nonrenewal**  \nInsurers must provide written notice of nonrenewal between 30 and 120 days before the policy period ends.  \nExceptions include transfers within the same insurance group, short-term extensions, or minimal premium increases.  \n\n**California Insurance Guarantee Association (CIGA)**  \nProperty and casualty insurers participate in this association, which settles unpaid claims of insolvent insurers.  \nA surcharge may appear on premium notices to recover assessments.\n\n**Your Right to Rating and Dividend Information**  \nPolicyholders are entitled to information on loss experience, classification, rating plans, and claims data held by the Workers’ Compensation Insurance Rating Bureau (WCIRB).  \nDisputes regarding classification or rating applications can be made to the insurer, WCIRB, or the Insurance Commissioner.  \nPolicyholders may appeal unresolved issues within statutory time limits.  \nA policyholder ombudsman is available to assist with inquiries and disputes.\n\n---\n\n### WORKERS COMPENSATION AND EMPLOYERS LIABILITY INSURANCE POLICY  \n**General Section**  \nDefines the policy as a contract between the employer and the insurer. Specifies that only written endorsements can modify it.  \nCovers all workplaces listed in the information page and others in covered states unless separately insured.  \n\n**Part One: Workers Compensation Insurance**  \nApplies to bodily injury by accident or disease arising from employment.  \nInsurer agrees to pay benefits required by law, defend claims, and cover related costs.  \nEmployers are responsible for penalties due to misconduct, safety violations, or discrimination.  \nInsurer retains rights of recovery against liable third parties.\n\n**Part Two: Employers Liability Insurance**  \nCovers damages employers are legally obligated to pay to employees not covered under workers’ compensation laws.  \nIncludes consequential injuries to family members and third-party claims.  \nLists exclusions such as intentional injury, violation of law, federal acts, maritime duties, punitive damages, and fines.\n\n**Part Three: Other States Insurance**  \nApplies if additional states are listed in the policy. Employers must notify the insurer upon beginning work in those states.\n\n**Part Four: Duties if Injury Occurs**  \nOutlines employer duties to provide medical care, notify the insurer, cooperate with investigation, and preserve recovery rights.\n\n**Part Five: Premium**  \nPremiums are determined by classification and remuneration.  \nEmployers must maintain accurate records for audit; final premiums are based on actual payroll and exposure.\n\n**Part Six: Conditions**  \nGrants inspection rights, outlines policy transfer and cancellation terms, and designates the first named insured as sole representative.\n\n---\n\n### STATE-SPECIFIC ENDORSEMENTS (California)\n\n**Premium Due Date Endorsement**  \nSpecifies the due date for audit and retrospective premiums as the billing date.\n\n**Catastrophe (Other Than Certified Acts of Terrorism)**  \nAdds premium for catastrophic loss events exceeding a defined threshold across states.\n\n**Terrorism Risk Insurance Program Reauthorization Act Disclosure**  \nExplains federal limitations on insurer liability and partial government reimbursement for certified acts of terrorism.\n\n**Policy Amendatory Endorsement – California**  \nClarifies exclusions for illegally employed minors, punitive damages, and reimbursement for late indemnity payments.  \nStates that premium rates may be adjusted by order of the Insurance Commissioner.  \nRestates that the policy and its endorsements constitute the entire insurance contract.\n\n**Duty to Defend – California**  \nAmends defense obligations to cover claims before the Workers’ Compensation Appeals Board and similar authorities.\n\n**Employers’ Liability Coverage Amendatory Endorsement – California**  \nAdjusts exclusions, definitions, and scope of employer liability coverage within California.\n\n**Optional Premium Increase Endorsement – California**  \nAllows the insurer to impose an increased premium and cost recovery if the insured fails to permit payroll audit access within prescribed timeframes.\n\n**California Cancellation Endorsement**  \nReplaces general cancellation terms, listing specific reasons and required notice periods for insurer-initiated cancellations.  \nSpecifies mailing and timing rules for notice delivery based on location.\n\n---\n\n_All copyright references and formatting from the National Council on Compensation Insurance (NCCI) and the Workers’ Compensation Insurance Rating Bureau of California (WCIRB) have been preserved where applicable._",
        },
        {
            "policy_number": "POL123456789",
            "policy_holder_first_name": "John",
            "policy_holder_last_name": "Doe",
            "start_date": "2022-03-20",
            "end_data": "2024-03-20",
            "policy_coverage": "**WORKERS COMPENSATION AND EMPLOYERS LIABILITY INSURANCE POLICY**\n\n### General Section\nDefines the policy as a contract between the employer and insurer.  \nCoverage extends to all workplaces listed in the information page and other states listed unless separately insured.  \nSpecifies that only written endorsements may modify the policy.  \n\n### Part One – Workers Compensation Insurance\nApplies to bodily injury by accident or disease arising out of employment, including death.  \nInsurer agrees to:\n- Pay all benefits required by workers’ compensation law.  \n- Defend claims, proceedings, or suits against the insured for covered benefits.  \n- Pay certain additional costs, including litigation expenses, bonds, and interest on judgments.  \n\nExcludes coverage for penalties, intentional misconduct, or violations of law.  \nProvides for insurer recovery from liable third parties and clarifies statutory provisions relating to insolvency, jurisdiction, and compliance with applicable laws.  \n\n### Part Two – Employers Liability Insurance\nCovers sums the insured must pay as damages to employees for work-related bodily injury outside the scope of workers’ compensation law.  \nIncludes consequential injuries to family members or third parties.  \nExclusions include:\n- Contractual liability.  \n- Punitive damages.  \n- Injuries to employees knowingly employed in violation of law.  \n- Obligations under other federal acts (e.g., maritime, defense, or occupational disease laws).  \n- Intentional injuries, discrimination, and claims arising outside the U.S. or Canada.  \n\nDefines insurer’s duty to defend, limits liability per accident or disease, and prohibits joining the insurer as a co-defendant in employer suits.  \n\n### Part Three – Other States Insurance\nExtends coverage to additional states listed in the policy when work begins after issuance, provided the insurer is notified.  \nRequires prompt notice of new operations in any state not previously listed.  \n\n### Part Four – Duties if Injury Occurs\nEmployer must:\n- Provide immediate medical care and other required services.  \n- Notify the insurer promptly of injury details, witnesses, and any legal proceedings.  \n- Cooperate with investigations and refrain from voluntary payments or settlements without insurer consent.  \n\n### Part Five – Premium\nPremiums are determined by insurer manuals, classifications, and remuneration.  \nEmployers must:\n- Maintain accurate payroll and exposure records.  \n- Allow audits to determine final premium based on actual data.  \nOutlines procedures for estimated, final, and short-rate premium calculations, as well as minimum premium obligations.  \n\n### Part Six – Conditions\n- **Inspection:** Insurer may inspect workplaces for rating and underwriting purposes but assumes no safety duty.  \n- **Long-Term Policy:** Treats multi-year policies as renewed annually.  \n- **Transfer of Rights:** Rights and duties cannot be transferred without written consent.  \n- **Cancellation:** Specifies notice requirements for cancellation by either party and adjusts terms to conform with state laws.  \n- **Representative:** The first named insured may act on behalf of all insureds for policy changes or returns.\n\n---\n\n### Endorsements\n\n**Pending Law Change (Terrorism Risk Insurance Program Reauthorization Act)**  \nExplains federal participation in covering terrorism-related losses and notes potential expiration effects if the act is not renewed.\n\n**Pending Rate Change Endorsement**  \nAlerts that rate filings under state authority may result in future premium adjustments.\n\n**Premium Discount Endorsement**  \nEstablishes tiered premium discounts based on total eligible premium, with final amounts determined after audit.\n\n**90-Day Reporting Requirement – Change in Ownership**  \nRequires written notification within 90 days of ownership changes such as sales, mergers, or consolidations, as these may affect experience rating.\n\n**Premium Due Date Endorsement**  \nClarifies that audit and retrospective premiums are due as of the billing date.\n\n**Catastrophe (Other Than Certified Acts of Terrorism) Premium Endorsement**  \nDefines catastrophic events such as earthquakes or industrial accidents exceeding a $50 million loss threshold and applies a specified premium charge.\n\n**Terrorism Risk Insurance Program Reauthorization Act Disclosure**  \nDescribes federal and insurer obligations for terrorism-related losses, definitions of certified acts, federal reimbursement percentages, and liability caps.\n\n**Audit Noncompliance Charge Endorsement**  \nAllows the insurer to impose additional charges or cancel coverage if audit access is denied, with potential eligibility impact in assigned risk plans.\n\n**Experience Rating Modification Factor Revision**  \nPermits retroactive revision of experience rating factors once recalculated.\n\n**State-Specific Endorsement – Georgia**  \nReplaces general cancellation terms with Georgia-specific rules on cancellation, nonrenewal, and changes.  \nRequires notice periods for cancellation or reduction of coverage, notification of premium increases, and compliance with audit requests.\n\n---\n\nAll language, structure, and terminology have been preserved in line with the original document’s clauses, omitting identifying data while maintaining fidelity to the legal and procedural text [oai_citation:0‡policy_example_3.pdf](sediment://file_00000000219061f4a6445056891f4824).",
        },
        {
            "policy_number": "POL987654321",
            "policy_holder_first_name": "Emily",
            "policy_holder_last_name": "Johnson",
            "start_date": "2023-01-12",
            "end_data": "2025-01-12",
            "policy_coverage": "**WORKERS COMPENSATION AND EMPLOYERS LIABILITY INSURANCE POLICY**\n\n### General Section\nDefines the policy as a contract between the employer and insurer.  \nCoverage extends to all workplaces listed in the information page and other states listed unless separately insured.  \nSpecifies that only written endorsements may modify the policy.  \n\n### Part One – Workers Compensation Insurance\nApplies to bodily injury by accident or disease arising out of employment, including death.  \nInsurer agrees to:\n- Pay all benefits required by workers’ compensation law.  \n- Defend claims, proceedings, or suits against the insured for covered benefits.  \n- Pay certain additional costs, including litigation expenses, bonds, and interest on judgments.  \n\nExcludes coverage for penalties, intentional misconduct, or violations of law.  \nProvides for insurer recovery from liable third parties and clarifies statutory provisions relating to insolvency, jurisdiction, and compliance with applicable laws.  \n\n### Part Two – Employers Liability Insurance\nCovers sums the insured must pay as damages to employees for work-related bodily injury outside the scope of workers’ compensation law.  \nIncludes consequential injuries to family members or third parties.  \nExclusions include:\n- Contractual liability.  \n- Punitive damages.  \n- Injuries to employees knowingly employed in violation of law.  \n- Obligations under other federal acts (e.g., maritime, defense, or occupational disease laws).  \n- Intentional injuries, discrimination, and claims arising outside the U.S. or Canada.  \n\nDefines insurer’s duty to defend, limits liability per accident or disease, and prohibits joining the insurer as a co-defendant in employer suits.  \n\n### Part Three – Other States Insurance\nExtends coverage to additional states listed in the policy when work begins after issuance, provided the insurer is notified.  \nRequires prompt notice of new operations in any state not previously listed.  \n\n### Part Four – Duties if Injury Occurs\nEmployer must:\n- Provide immediate medical care and other required services.  \n- Notify the insurer promptly of injury details, witnesses, and any legal proceedings.  \n- Cooperate with investigations and refrain from voluntary payments or settlements without insurer consent.  \n\n### Part Five – Premium\nPremiums are determined by insurer manuals, classifications, and remuneration.  \nEmployers must:\n- Maintain accurate payroll and exposure records.  \n- Allow audits to determine final premium based on actual data.  \nOutlines procedures for estimated, final, and short-rate premium calculations, as well as minimum premium obligations.  \n\n### Part Six – Conditions\n- **Inspection:** Insurer may inspect workplaces for rating and underwriting purposes but assumes no safety duty.  \n- **Long-Term Policy:** Treats multi-year policies as renewed annually.  \n- **Transfer of Rights:** Rights and duties cannot be transferred without written consent.  \n- **Cancellation:** Specifies notice requirements for cancellation by either party and adjusts terms to conform with state laws.  \n- **Representative:** The first named insured may act on behalf of all insureds for policy changes or returns.\n\n---\n\n### Endorsements\n\n**Pending Law Change (Terrorism Risk Insurance Program Reauthorization Act)**  \nExplains federal participation in covering terrorism-related losses and notes potential expiration effects if the act is not renewed.\n\n**Pending Rate Change Endorsement**  \nAlerts that rate filings under state authority may result in future premium adjustments.\n\n**Premium Discount Endorsement**  \nEstablishes tiered premium discounts based on total eligible premium, with final amounts determined after audit.\n\n**90-Day Reporting Requirement – Change in Ownership**  \nRequires written notification within 90 days of ownership changes such as sales, mergers, or consolidations, as these may affect experience rating.\n\n**Premium Due Date Endorsement**  \nClarifies that audit and retrospective premiums are due as of the billing date.\n\n**Catastrophe (Other Than Certified Acts of Terrorism) Premium Endorsement**  \nDefines catastrophic events such as earthquakes or industrial accidents exceeding a $50 million loss threshold and applies a specified premium charge.\n\n**Terrorism Risk Insurance Program Reauthorization Act Disclosure**  \nDescribes federal and insurer obligations for terrorism-related losses, definitions of certified acts, federal reimbursement percentages, and liability caps.\n\n**Audit Noncompliance Charge Endorsement**  \nAllows the insurer to impose additional charges or cancel coverage if audit access is denied, with potential eligibility impact in assigned risk plans.\n\n**Experience Rating Modification Factor Revision**  \nPermits retroactive revision of experience rating factors once recalculated.\n\n**State-Specific Endorsement – Georgia**  \nReplaces general cancellation terms with Georgia-specific rules on cancellation, nonrenewal, and changes.  \nRequires notice periods for cancellation or reduction of coverage, notification of premium increases, and compliance with audit requests.\n\n---\n\nAll language, structure, and terminology have been preserved in line with the original document’s clauses, omitting identifying data while maintaining fidelity to the legal and procedural text [oai_citation:0‡policy_example_3.pdf](sediment://file_00000000219061f4a6445056891f4824).",
        },
    ]
    found = list(FORMS_DIR.rglob("form_model.json"))
    if not found:
        logger.warning(f"No form_model.json files found under {FORMS_DIR.resolve()}")
    else:
        logger.info(f"Found {len(found)} form models: {[p.name for p in found]}")

    # Iterate through all form_model.json files and generate samples
    for form_model in FORMS_DIR.rglob("form_model.json"):
        for policy in policies:
            answers = generate_sample(form_model, policy)
            out_dir = SAMPLES_DIR / form_model.parent.name
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"answers_{policy['policy_number']}.json"
            # --- Skip if already exists ---
            if out_file.exists():
                logger.info(f"Skipping {out_file} (already exists).")
                continue
            with out_file.open("w", encoding="utf-8") as f:
                json.dump(answers, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved generated sample to {out_file}")