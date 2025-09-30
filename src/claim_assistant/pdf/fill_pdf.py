import json
from datetime import datetime

import openai
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Set your OpenAI API key
# openai.api_key = os.getenv("OPENAI_API_KEY")  # Make sure to set this environment variable
openai.api_key = "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"


def analyze_claim_with_openai(form_data: dict) -> dict:
    """Use OpenAI to analyze the claim and generate structured summary."""

    # Prepare the prompt with form data
    prompt = f"""
    Analyze the following workers' compensation claim form data and provide a structured analysis:

    Form Data:
    {json.dumps(form_data, indent=2)}

    Please provide a JSON response with the following structure:
    {{
        "claim_summary": {{
            "case_number": "Generated case number or 'N/A'",
            "submission_date": "Date when claim was submitted"
        }},
        "employee_info": {{
            "name": "Employee full name",
            "contact": "Contact information (phone, email, address)",
            "position": "Job title/position if available"
        }},
        "employer_info": {{
            "name": "Employer name",
            "address": "Employer address",
            "contact": "Employer contact information",
            "insurance_info": "Insurance carrier details"
        }},
        "incident_info": {{
            "description": "Detailed description of the incident",
            "date": "Date of injury",
            "time": "Time of injury if available",
            "location": "Where the incident occurred",
            "circumstances": "Circumstances leading to the incident"
        }},
        "policy_check": {{
            "policy_number": "Insurance policy number",
            "coverage_period": "Policy effective period if available",
            "coverage_details": "What is covered under the policy"
        }},
        "decision_draft": {{
            "status": "Covered/Not covered/Missing data",
            "reasoning": "Explanation for the decision",
            "missing_information": "List any missing critical information",
            "recommendations": "Next steps or recommendations"
        }}
    }}

    Make sure to extract all relevant information from the form data and provide a comprehensive analysis.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-5-nano-2025-08-07",
            messages=[
                {
                    "role": "system",
                    "content": "You are a workers' compensation claim analyst. Analyze claim forms and provide structured summaries.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        # Parse the JSON response
        analysis_json = response.choices[0].message.content
        # Remove any markdown formatting if present
        if analysis_json.startswith("```json"):
            analysis_json = analysis_json.replace("```json", "").replace("```", "").strip()

        return json.loads(analysis_json)

    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        # Return a fallback structure with basic data
        return create_fallback_analysis(form_data)


def create_fallback_analysis(form_data: dict) -> dict:
    """Create a fallback analysis if OpenAI API fails."""
    return {
        "claim_summary": {
            "case_number": "CASE-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
            "submission_date": form_data.get("Today's Date (mm/dd/yyyy)", "N/A"),
        },
        "employee_info": {
            "name": form_data.get("Employee Name", "N/A"),
            "contact": f"Email: {form_data.get("Employee's e-mail", 'N/A')}, Address: {form_data.get('Home Address', 'N/A')}",
            "position": "N/A",
        },
        "employer_info": {
            "name": form_data.get("Name of employer", "N/A"),
            "address": form_data.get("Employer Address", "N/A"),
            "contact": form_data.get("Telephone", "N/A"),
            "insurance_info": form_data.get(
                "Name and address of insurance carrier or adjusting agency", "N/A"
            ),
        },
        "incident_info": {
            "description": f"{form_data.get('Describe injury and part of body affected Line 1', '')} {form_data.get('Describe injury and part of body affected Line 2', '')}",
            "date": form_data.get("Date of Injury (mm/dd/yyyy)", "N/A"),
            "time": form_data.get("Time of Injury", "N/A"),
            "location": f"{form_data.get('Address and description of where injury happened Line 1', '')} {form_data.get('Address and description of where injury happened Line 2', '')}",
            "circumstances": "Manual review required",
        },
        "policy_check": {
            "policy_number": form_data.get("Insurance Policy Number", "N/A"),
            "coverage_period": "Manual verification required",
            "coverage_details": "Manual review required",
        },
        "decision_draft": {
            "status": "Missing data",
            "reasoning": "Automated analysis not available - manual review required",
            "missing_information": "API analysis failed",
            "recommendations": "Conduct manual review of all claim documents",
        },
    }


def create_claim_summary_pdf(analysis: dict, output_path: str):
    """Create a PDF with the structured claim summary."""

    doc = SimpleDocTemplate(
        output_path, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=30,
        textColor=colors.darkblue,
    )

    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkgreen,
    )

    normal_style = styles["Normal"]

    # Build the PDF content
    story = []

    # Title
    story.append(Paragraph("Workers' Compensation Claim Summary", title_style))
    story.append(Spacer(1, 12))

    # Claim Summary Section
    story.append(Paragraph("Claim Summary", section_style))
    claim_data = [
        ["Case Number:", analysis["claim_summary"]["case_number"]],
        ["Submission Date:", analysis["claim_summary"]["submission_date"]],
    ]
    claim_table = Table(claim_data, colWidths=[2 * inch, 4 * inch])
    claim_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(claim_table)
    story.append(Spacer(1, 20))

    # Employee Info Section
    story.append(Paragraph("Employee Information", section_style))
    emp_data = [
        ["Name:", analysis["employee_info"]["name"]],
        ["Contact:", analysis["employee_info"]["contact"]],
        ["Position:", analysis["employee_info"]["position"]],
    ]
    emp_table = Table(emp_data, colWidths=[2 * inch, 4 * inch])
    emp_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(emp_table)
    story.append(Spacer(1, 20))

    # Employer Info Section
    story.append(Paragraph("Employer Information", section_style))
    employer_data = [
        ["Name:", analysis["employer_info"]["name"]],
        ["Address:", analysis["employer_info"]["address"]],
        ["Contact:", analysis["employer_info"]["contact"]],
        ["Insurance:", analysis["employer_info"]["insurance_info"]],
    ]
    employer_table = Table(employer_data, colWidths=[2 * inch, 4 * inch])
    employer_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(employer_table)
    story.append(Spacer(1, 20))

    # Incident Info Section
    story.append(Paragraph("Incident Information", section_style))
    incident_data = [
        ["Description:", analysis["incident_info"]["description"]],
        ["Date:", analysis["incident_info"]["date"]],
        ["Time:", analysis["incident_info"]["time"]],
        ["Location:", analysis["incident_info"]["location"]],
        ["Circumstances:", analysis["incident_info"]["circumstances"]],
    ]
    incident_table = Table(incident_data, colWidths=[2 * inch, 4 * inch])
    incident_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(incident_table)
    story.append(Spacer(1, 20))

    # Policy Check Section
    story.append(Paragraph("Policy Information", section_style))
    policy_data = [
        ["Policy Number:", analysis["policy_check"]["policy_number"]],
        ["Coverage Period:", analysis["policy_check"]["coverage_period"]],
        ["Coverage Details:", analysis["policy_check"]["coverage_details"]],
    ]
    policy_table = Table(policy_data, colWidths=[2 * inch, 4 * inch])
    policy_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(policy_table)
    story.append(Spacer(1, 20))

    # Decision Draft Section
    story.append(Paragraph("Decision Draft", section_style))

    # Color-code the status
    status = analysis["decision_draft"]["status"]
    status_color = (
        colors.green
        if "Covered" in status
        else colors.red
        if "Not covered" in status
        else colors.orange
    )

    decision_data = [
        [
            "Status:",
            Paragraph(f"<font color='{status_color}'><b>{status}</b></font>", normal_style),
        ],
        ["Reasoning:", analysis["decision_draft"]["reasoning"]],
        ["Missing Info:", analysis["decision_draft"]["missing_information"]],
        ["Recommendations:", analysis["decision_draft"]["recommendations"]],
    ]
    decision_table = Table(decision_data, colWidths=[2 * inch, 4 * inch])
    decision_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(decision_table)

    # Build PDF
    doc.build(story)
    print(f"Claim summary PDF created: {output_path}")


def main():
    """Main function to process the claim and generate PDF."""

    # Load the extracted form fields
    json_path = "/home/maken/symfa/claim-assistant/data/forms/dwc/extracted_form_fields.json"

    with open(json_path, "r") as f:
        form_data = json.load(f)

    print("Analyzing claim with OpenAI...")

    # Analyze with OpenAI
    analysis = analyze_claim_with_openai(form_data)

    # Create PDF
    output_pdf_path = "/home/maken/symfa/claim-assistant/data/forms/dwc/claim_summary.pdf"
    create_claim_summary_pdf(analysis, output_pdf_path)

    # Also save the analysis as JSON for reference
    analysis_json_path = "/home/maken/symfa/claim-assistant/data/forms/dwc/claim_analysis.json"
    with open(analysis_json_path, "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"Analysis saved to: {analysis_json_path}")


if __name__ == "__main__":
    main()
