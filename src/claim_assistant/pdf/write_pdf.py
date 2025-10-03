from datetime import datetime
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _yes_no(value: bool | None) -> str:
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return ""  # empty if missing/None


def _to_str(v) -> str:
    if isinstance(v, bool):
        return _yes_no(v)
    if v is None:
        return ""
    return str(v)


def _para(text: str, style_name: str = "BodyText") -> Paragraph:
    styles = getSampleStyleSheet()
    return Paragraph((text or "").replace("\n", "<br/>"), styles[style_name])


def _section_header(text: str) -> Paragraph:
    styles = getSampleStyleSheet()
    hdr = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.darkgreen,
        spaceBefore=12,
        spaceAfter=6,
    )
    return Paragraph(text, hdr)


def _title(text: str) -> Paragraph:
    styles = getSampleStyleSheet()
    ttl = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        textColor=colors.darkblue,
        fontSize=16,
        spaceAfter=16,
    )
    return Paragraph(text, ttl)


def _kv_table(
    rows: Iterable[tuple[str, str]],
    col_widths=(2.0 * inch, 4.5 * inch),
) -> Table:
    """
    Build a two-column key/value table with consistent styling and wrapping.
    Always renders all rows; empty values are shown as empty strings.
    """
    data = []
    for k, v in rows:
        key_p = _para(f"<b>{k}:</b>")
        val_p = _para(v or "")
        data.append([key_p, val_p])

    tbl = Table(data, colWidths=list(col_widths), hAlign="LEFT")
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ],
        ),
    )
    return tbl


def _page_number(canvas, doc):
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    text = f"Page {doc.page}"
    canvas.drawRightString(doc.pagesize[0] - 36, 20, text)


def _rows_all(data: dict, mapping: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """
    Build table rows from label->key mapping.
    Includes every mapped key; missing/None -> empty string.
    """
    rows: list[tuple[str, str]] = []
    for label, key in mapping:
        rows.append((label, _to_str(data.get(key))))
    return rows


def _label_from_key(key: str) -> str:
    return key.replace("_", " ").title()


def write_summary_pdf(data: dict, output_pdf: str | Path) -> Path:
    """
    Create a human-readable summary PDF from a dict.
    Prints all mapped fields; missing/empty -> empty string.
    Also adds an 'Other Fields' section for keys not in the mapping.
    """
    output_path = Path(output_pdf)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
        title="Workers' Compensation Claim Summary",
        author="Claim Assistant",
    )

    story: list = []
    story.append(_title("Workers’ Compensation Claim Summary"))

    # Define sections and field order
    claim_summary_map = [
        ("Case Number", "__generated_case_number__"),
        ("Submission Date", "todays_date"),
        ("Policy Number", "insurance_policy_number"),
    ]

    employee_info_map = [
        ("Name", "employee_name"),
        ("Email", "employees_email"),
        ("SSN", "social_security_number"),
        ("Home Address", "home_address"),
        ("City", "city"),
        ("State", "state"),
        ("Zip Code", "zip_code"),
        ("Consent to Email Notices", "consent_to_receive_claim_notices_by_email_only"),
        # ("Employee Signature", "signature_of_employee"),
    ]

    employer_info_map = [
        ("Employer Name", "employer_name"),
        ("Employer Address", "employer_address"),
        ("Representative Title", "title_of_employer_representative"),
        ("Representative Phone", "telephone_number_of_employer_representative"),
        ("Date Employer First Knew of Injury", "date_employer_first_knew_of_injury"),
        (
            "Date Claim Form Provided to Employee",
            "date_claim_form_was_provided_to_employee",
        ),
        ("Date Employer Received Claim Form", "date_employer_received_claim_form"),
        # ("Representative Signature", "signature_of_employer_representative"),
    ]

    incident_info_map = [
        ("Date of Injury", "date_of_injury"),
        ("Time of Injury", "time_of_injury"),
        ("Location / Address", "address_and_description_of_where_injury_happened"),
        ("Injury Description", "describe_injury_and_part_of_body_affected"),
    ]

    policy_info_map = [
        ("Policy Number", "insurance_policy_number"),
        (
            "Carrier / Adjuster",
            "name_and_address_of_insurance_carrier_or_adjusting_agency",
        ),
        ("Policy Holder Name", "policy_holder_name"),
        ("Policy Start Date", "start_date"),
        ("Policy End Date", "end_date"),
        ("Policy Coverage", "policy_coverage"),
        ("Adjuster advice", "adjuster_advice"),
    ]

    # Claim Summary
    story.append(_section_header("Claim Summary"))
    case_number = f"CASE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    # mapped_claim = dict(data)
    # mapped_claim["__generated_case_number__"] = case_number
    # story.append(_kv_table(_rows_all(mapped_claim, claim_summary_map)))
    data["__generated_case_number__"] = case_number
    story.append(_kv_table(_rows_all(data, claim_summary_map)))
    story.append(Spacer(1, 10))

    # Employee Information
    story.append(_section_header("Employee Information"))
    story.append(_kv_table(_rows_all(data, employee_info_map)))
    story.append(Spacer(1, 10))

    # Employer Information
    story.append(_section_header("Employer Information"))
    story.append(_kv_table(_rows_all(data, employer_info_map)))
    story.append(Spacer(1, 10))

    # Incident Information
    story.append(_section_header("Incident Information"))
    story.append(_kv_table(_rows_all(data, incident_info_map)))
    story.append(Spacer(1, 10))

    # Policy Information
    story.append(_section_header("Policy Information"))
    story.append(_kv_table(_rows_all(data, policy_info_map)))

    # Other fields not in the mapping
    mapped_keys = (
        {k for _, k in claim_summary_map}
        | {k for _, k in employee_info_map}
        | {k for _, k in employer_info_map}
        | {k for _, k in incident_info_map}
        | {k for _, k in policy_info_map}
    )

    extras = [k for k in data.keys() if k not in mapped_keys]
    if extras:
        story.append(Spacer(1, 14))
        story.append(_section_header("Other Fields"))
        extra_rows = [
            (_label_from_key(k), _to_str(data.get(k))) for k in sorted(extras)
        ]
        story.append(_kv_table(extra_rows))

    # Footer note
    story.append(Spacer(1, 16))
    story.append(
        _para(
            "<font size=9 color=grey>"
            "This summary is generated from the FNOL form data and is intended for human review."
            "</font>",
        ),
    )

    doc.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    return output_path


if __name__ == "__main__":
    example = {
        "employee_name": "John Smith",
        "todays_date": "2025-10-03",
        "home_address": "",
        "city": "Springfield",
        "state": "IL",
        "zip_code": "62704",
        "date_of_injury": "2025-09-28",
        "time_of_injury": "14:35:00",
        "address_and_description_of_where_injury_happened": "Warehouse 7, 235 Industrial Park Rd, Springfield, IL",
        "describe_injury_and_part_of_body_affected": "",
        "social_security_number": "XXX-XX-1234",
        "employees_email": "john.smith@example.com",
        "consent_to_receive_claim_notices_by_email_only": True,
        "signature_of_employee": "",
        "employer_name": "Acme Manufacturing Inc.",
        "employer_address": "",
        "date_employer_first_knew_of_injury": "2025-09-28",
        "date_claim_form_was_provided_to_employee": "2025-09-29",
        "date_employer_received_claim_form": "",
        "name_and_address_of_insurance_carrier_or_adjusting_agency": "NorthBank Insurance Co., 77 Coverage Ave, Chicago, IL",
        "insurance_policy_number": "PO123456",
        "signature_of_employer_representative": "",
        "title_of_employer_representative": "HR Manager",
        "telephone_number_of_employer_representative": "555-012-3456",
        "some_extra_field": "Extra value",
    }

    out = write_summary_pdf(example, Path("data/forms/dwc/claim_summary.pdf"))
    print(f"Wrote {out.resolve()}")
