import json

from fillpdf import fillpdfs

# input_path = "/home/maken/symfa/claim-assistant/data/forms/dwc/form_raw.pdf"
# data = fillpdfs.get_form_fields(input_path)

# print(data)


# data['DIA'] = '23'
# data['MES'] = 'Octubre'
# data['AÑO'] = '23'
# data['NOMBRE REPRESENTADO'] = 'Sergio'

# output_path = f"/data/output.pdf"
# fillpdfs.write_fillable_pdf(input_path,output_path,data)


def fill_dwc_pdf(input_pdf_path: str, output_pdf_path: str, data: dict) -> None:
    """
    Fill a DWC PDF form with the provided data.

    Args:
        input_pdf_path (str): Path to the input PDF form.
        output_pdf_path (str): Path to save the filled PDF form.
        data (dict): Dictionary containing form field names and their corresponding values.

    Returns:
        None
    """
    data_pdf = fillpdfs.get_form_fields(input_pdf_path)
    data_form = data["data"][0]

    # Fill the form fields with extracted data
    data_pdf["Employee Name"] = data_form.get("employee_name", "")
    data_pdf["Home Address"] = data_form.get("home_address", "")
    data_pdf["Employee City"] = data_form.get("city", "")
    data_pdf["Employee State"] = data_form.get("state", "")
    data_pdf["Employee Zip"] = data_form.get("zip_code", "")
    data_pdf["Today's Date"] = data_form.get("todays_date", "")
    data_pdf["Date of Injury \\(mm/dd/yyyy\\)"] = data_form.get("date_of_injury", "")
    data_pdf["Time of Injury. a.m"] = data_form.get("time_of_injury_am", "")
    data_pdf["Time of Injury. p.m"] = data_form.get("time_of_injury_pm", "")
    data_pdf["Address and description of where injury happened Line 1"] = data_form.get(
        "address_and_description_of_where_injury_happened_line_1", ""
    )
    data_pdf["Address and description of where injury happened Line 2"] = data_form.get(
        "address_and_description_of_where_injury_happened_line_2", ""
    )
    data_pdf["Describe injury and part of body affected Line 1"] = data_form.get(
        "describe_injury_and_part_of_body_affected_line_1", ""
    )
    data_pdf["Describe injury and part of body affected Line 2"] = data_form.get(
        "describe_injury_and_part_of_body_affected_line_2", ""
    )
    data_pdf["Social Security Number"] = data_form.get("social_security_number", "")
    data_pdf["Check if you agree to receive notices about your claim by email only"] = (
        data_form.get("consent_to_receive_claim_notices_by_email_only", "")
    )
    # data_pdf["Employee's Email"] = data_form.get("employees_email", "")
    data_pdf["Signature of employee"] = data_form.get("signature_of_employee", "")

    data_pdf["Name of employer"] = data_form.get("employer_name", "")
    data_pdf["Employer Address"] = data_form.get("employer_address", "")
    data_pdf["Date employer first knew of injury. \\(mm/dd/yyyy\\)"] = data_form.get(
        "date_employer_first_knew_of_injury", ""
    )
    data_pdf["Date claim form was provided to employee. \\(mm/dd/yyyy\\)"] = data_form.get(
        "date_claim_form_provided_to_employee", ""
    )
    data_pdf["Date employer received claim form. \\(mm/dd/yyyy\\)"] = data_form.get(
        "date_employer_received_claim_form", ""
    )
    data_pdf["Name and address of insurance carrier or adjusting agency"] = data_form.get(
        "name_and_address_of_insurance_carrier_or_adjusting_agency", ""
    )
    data_pdf["Insurance Policy Number"] = data_form.get("insurance_policy_number", "")
    data_pdf["Title"] = data_form.get("title_of_employer_representative", "")
    data_pdf["Telephone"] = data_form.get("telephone_number_of_employer_representative:", "")
    data_pdf["Employer copy"] = data_form.get("employer_copy", "")
    data_pdf["Employee copy"] = data_form.get("employee_copy:", "")
    data_pdf["Claims Administrator"] = data_form.get("claim_administrator", "")
    data_pdf["Temporary Receipt"] = data_form.get("temporary_reciept", "")
    data_pdf["Signature of employer representative"] = data_form.get(
        "signature_of_employer_representative:", ""
    )

    fillpdfs.write_fillable_pdf(input_pdf_path, output_pdf_path, data_pdf)


def load_json_data(json_file_path: str) -> dict:
    """Load JSON data from file."""
    with open(json_file_path, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    data = load_json_data("/home/maken/symfa/claim-assistant/data/forms/dwc/extracted_answers.json")

    fill_dwc_pdf(
        input_pdf_path="/home/maken/symfa/claim-assistant/data/forms/dwc/form_raw.pdf",
        output_pdf_path="/home/maken/symfa/claim-assistant/data/forms/dwc/form_filled.pdf",
        data=data,
    )
