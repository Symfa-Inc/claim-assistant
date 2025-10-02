import json
from datetime import datetime
import openai
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import io

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
            # temperature=0.3,
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


def format_contact_info(contact_data):
    """Format contact information nicely from nested dictionary."""
    if isinstance(contact_data, dict):
        formatted_parts = []
        
        # Handle phone numbers
        if 'phone_primary' in contact_data:
            formatted_parts.append(f"Primary Phone: {contact_data['phone_primary']}")
        if 'phone_secondary' in contact_data:
            formatted_parts.append(f"Secondary Phone: {contact_data['phone_secondary']}")
        
        # Handle email
        if 'email' in contact_data:
            formatted_parts.append(f"Email: {contact_data['email']}")
        
        # Handle address
        if 'address' in contact_data and isinstance(contact_data['address'], dict):
            address = contact_data['address']
            address_parts = []
            
            if 'line1' in address:
                address_parts.append(address['line1'])
            if 'line2' in address:
                address_parts.append(address['line2'])
            
            # Add city, state, zip
            location_parts = []
            if 'city' in address:
                location_parts.append(address['city'])
            if 'state' in address:
                location_parts.append(address['state'])
            if 'zip' in address:
                location_parts.append(address['zip'])
            
            if location_parts:
                address_parts.append(', '.join(location_parts))
            
            if address_parts:
                formatted_parts.append(f"Address: {', '.join(address_parts)}")
        
        return ' | '.join(formatted_parts) if formatted_parts else str(contact_data)
    
    return str(contact_data)

def format_value(key, value):
    """Format values based on their type and key."""
    if key == 'contact' and isinstance(value, dict):
        return format_contact_info(value)
    elif isinstance(value, dict):
        # Handle other nested dictionaries
        formatted_items = []
        for k, v in value.items():
            formatted_key = k.replace('_', ' ').title()
            formatted_items.append(f"{formatted_key}: {v}")
        return ' | '.join(formatted_items)
    elif isinstance(value, list):
        return ', '.join(str(item) for item in value)
    else:
        return str(value)

def create_advanced_text_pdf_pypdf(analysis: dict, output_path: str):
    """Create a more advanced PDF with better text handling."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Layout settings
    left_margin = 50
    right_margin = width - 50
    top_margin = height - 50
    bottom_margin = 50
    max_width = right_margin - left_margin
    
    y_pos = top_margin
    line_height = 14
    section_spacing = 20
    
    def get_text_width(text, font_name, font_size):
        """Calculate actual text width."""
        return c.stringWidth(text, font_name, font_size)
    
    def add_wrapped_text(text, x, y, max_width, font_name="Helvetica", font_size=10, bold=False):
        """Add text with proper wrapping and return the final y position."""
        nonlocal y_pos
        
        if bold:
            font_name = "Helvetica-Bold"
        
        c.setFont(font_name, font_size)
        
        # Split text into words
        words = str(text).split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            text_width = get_text_width(test_line, font_name, font_size)
            
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
                # Check if single word is too long
                if get_text_width(word, font_name, font_size) > max_width:
                    # Break long word
                    while word:
                        for i in range(len(word), 0, -1):
                            if get_text_width(word[:i], font_name, font_size) <= max_width:
                                lines.append(word[:i])
                                word = word[i:]
                                break
                        else:
                            # Fallback if word is still too long
                            lines.append(word)
                            word = ""
        
        if current_line:
            lines.append(current_line)
        
        # Draw the lines
        for line in lines:
            if y < bottom_margin:
                c.showPage()
                y = top_margin
            
            c.drawString(x, y, line)
            y -= line_height
        
        return y
    
    def add_section_header(title, y):
        """Add a section header."""
        if y < bottom_margin + 30:
            c.showPage()
            y = top_margin
        
        # Add some space before section
        y -= section_spacing
        
        # Draw section header
        c.setFont("Helvetica-Bold", 14)
        c.drawString(left_margin, y, title)
        y -= line_height + 5
        
        # Add underline
        c.line(left_margin, y + 2, left_margin + get_text_width(title, "Helvetica-Bold", 14), y + 2)
        y -= 10
        
        return y
    
    def add_formatted_section(section_title, section_data, y_pos):
        """Add a section with properly formatted data."""
        y_pos = add_section_header(section_title, y_pos)
        
        for key, value in section_data.items():
            display_key = key.replace("_", " ").title()
            formatted_value = format_value(key, value)
            
            # Special handling for contact information
            if key == 'contact' and isinstance(value, dict):
                y_pos = add_wrapped_text(f"{display_key}:", left_margin, y_pos, max_width, font_size=10, bold=True)
                
                # Format contact details nicely
                contact_lines = []
                if 'phone_primary' in value:
                    contact_lines.append(f"Primary Phone: {value['phone_primary']}")
                if 'phone_secondary' in value:
                    contact_lines.append(f"Secondary Phone: {value['phone_secondary']}")
                if 'email' in value:
                    contact_lines.append(f"Email: {value['email']}")
                
                # Format address separately
                if 'address' in value and isinstance(value['address'], dict):
                    addr = value['address']
                    address_line = "Address: "
                    addr_parts = []
                    
                    if 'line1' in addr:
                        addr_parts.append(addr['line1'])
                    if 'line2' in addr:
                        addr_parts.append(addr['line2'])
                    
                    # City, State, ZIP on same line
                    location = []
                    if 'city' in addr:
                        location.append(addr['city'])
                    if 'state' in addr:
                        location.append(addr['state'])
                    if 'zip' in addr:
                        location.append(addr['zip'])
                    
                    if location:
                        addr_parts.append(', '.join(location))
                    
                    address_line += ', '.join(addr_parts)
                    contact_lines.append(address_line)
                
                # Add each contact line
                for contact_line in contact_lines:
                    y_pos = add_wrapped_text(contact_line, left_margin + 20, y_pos, max_width - 20, font_size=10)
                    y_pos -= 3
                
            elif len(formatted_value) > 60:
                # Long values on separate lines
                y_pos = add_wrapped_text(f"{display_key}:", left_margin, y_pos, max_width, font_size=10, bold=True)
                y_pos = add_wrapped_text(formatted_value, left_margin + 20, y_pos, max_width - 20, font_size=10)
            else:
                # Short values on same line
                y_pos = add_wrapped_text(f"{display_key}: {formatted_value}", left_margin, y_pos, max_width, font_size=10)
            
            y_pos -= 5
        
        return y_pos
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    title = "WORKERS' COMPENSATION CLAIM SUMMARY"
    title_width = get_text_width(title, "Helvetica-Bold", 16)
    title_x = (width - title_width) / 2  # Center the title
    c.drawString(title_x, y_pos, title)
    y_pos -= 30
    
    # Add all sections using the new formatted function
    y_pos = add_formatted_section("CLAIM SUMMARY", analysis["claim_summary"], y_pos)
    y_pos = add_formatted_section("EMPLOYEE INFORMATION", analysis["employee_info"], y_pos)
    y_pos = add_formatted_section("EMPLOYER INFORMATION", analysis["employer_info"], y_pos)
    y_pos = add_formatted_section("INCIDENT INFORMATION", analysis["incident_info"], y_pos)
    y_pos = add_formatted_section("POLICY INFORMATION", analysis["policy_check"], y_pos)
    
    # Decision Draft with special status highlighting
    y_pos = add_section_header("DECISION DRAFT", y_pos)
    
    # Highlight status
    status = analysis["decision_draft"]["status"]
    y_pos = add_wrapped_text(f"STATUS: {status.upper()}", left_margin, y_pos, max_width, font_size=12, bold=True)
    y_pos -= 10
    
    # Other decision fields
    decision_fields = ["reasoning", "missing_information", "recommendations"]
    for field in decision_fields:
        if field in analysis["decision_draft"]:
            display_name = field.replace("_", " ").title()
            value = analysis["decision_draft"][field]
            
            y_pos = add_wrapped_text(f"{display_name}:", left_margin, y_pos, max_width, font_size=10, bold=True)
            y_pos = add_wrapped_text(str(value), left_margin + 20, y_pos, max_width - 20, font_size=10)
            y_pos -= 5
    
    c.save()
    buffer.seek(0)
    
    # Use PyPDF to write the final file
    reader = PdfReader(buffer)
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
    
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
    
    print(f"Advanced claim summary PDF created: {output_path}")

# Update your main function
def main():
    """Main function to process the claim and generate PDF."""
    
    # Load the extracted form fields
    json_path = "/home/maken/symfa/claim-assistant/data/forms/dwc/extracted_form_fields.json"
    
    with open(json_path, "r") as f:
        form_data = json.load(f)
    
    print("Analyzing claim with OpenAI...")
    
    # Analyze with OpenAI (your existing function)
    analysis = analyze_claim_with_openai(form_data)
    
    # Create PDF using PyPDF approach
    output_pdf_path = "/home/maken/symfa/claim-assistant/data/forms/dwc/claim_summary_pypdf.pdf"
    
    # # Method 1: Simple text version with wrapping
    # create_simple_text_pdf_pypdf(analysis, output_pdf_path.replace('.pdf', '_simple.pdf'))
    
    # Method 2: Advanced version with better formatting
    create_advanced_text_pdf_pypdf(analysis, output_pdf_path.replace('.pdf', '_advanced.pdf'))
    
    # Also save the analysis as JSON for reference
    analysis_json_path = "/home/maken/symfa/claim-assistant/data/forms/dwc/claim_analysis.json"
    with open(analysis_json_path, "w") as f:
        json.dump(analysis, f, indent=2)
    
    print(f"Analysis saved to: {analysis_json_path}")

if __name__ == "__main__":
    main()
