import json
import logging
import os
from pathlib import Path
from typing import List, Union

import Levenshtein
import pandas as pd
from dotenv import load_dotenv

# import base64
from openai import OpenAI
from pydantic import BaseModel

from claim_assistant.metrics.moverscore.moverscore import get_idf_dict, word_mover_score
from claim_assistant.models.form import Form
from claim_assistant.processors.form_filling_processor import FormFillingProcessor


def extract_text_from_json(json_file: Union[str, Path]) -> List[str]:
    """
    Extract 'text' fields from a JSON file.

    Args:
        json_file: Path to the JSON file

    Returns:
        List of text values found in the JSON file

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    json_path = Path(json_file)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = []

    # Handle different JSON structures
    if isinstance(data, dict):
        # If it's a single object with 'text' field
        if "text" in data:
            texts.append(data["text"])
    elif isinstance(data, list):
        # If it's a list of objects
        for item in data:
            if isinstance(item, dict) and "text" in item:
                texts.append(item["text"])

    return texts


class AnswerResponse(BaseModel):
    """Schema for structured answer response"""

    answer: str


def process_pdf_with_openai(
    pdf_file: str | Path,
    texts: list[str],
    api_key: str = None,
    model: str = "gpt-5-nano-2025-08-07",
) -> list[dict[str, str]]:
    """
    Process a PDF file with OpenAI and return structured output.

    Args:
        pdf_file: Path to the PDF file
        texts: List of text queries/prompts to process
        api_key: OpenAI API key (if None, uses OPENAI_API_KEY env variable)
        model: OpenAI model to use (must support vision/document input)

    Returns:
        List of dictionaries with format {"text": query, "answer": response}
    """
    # Load environment variables from .env file
    if api_key is None:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found in environment variables or .env file",
            )

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Upload PDF file to OpenAI
    pdf_path = Path(pdf_file)
    with open(pdf_path, "rb") as f:
        uploaded_file = client.files.create(file=f, purpose="assistants")

    results = []

    for text in texts:
        # Send request to OpenAI with PDF file using responses.parse
        response = client.responses.parse(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"Based on the provided PDF document, answer this question: {text}\n\nIf the information is not found in the document, respond with exactly 'None'.",
                        },
                        {"type": "input_file", "file_id": uploaded_file.id},
                    ],
                },
            ],
            text_format=AnswerResponse,
            max_output_tokens=2000,
        )

        # Extract the answer from parsed response
        parsed_output = response.output_parsed
        if isinstance(parsed_output, AnswerResponse):
            answer = parsed_output.answer
        elif isinstance(parsed_output, dict):
            answer = parsed_output.get("answer", "")
        else:
            answer = str(parsed_output)
        if answer.strip().lower() in [
            "none",
            "n/a",
            "not found",
            "not available",
            "",
            " ",
        ]:
            answer = None
        print(f"Query: {text}\nAnswer: {answer}\n{'-' * 40}")

        # Append structured output
        results.append({"text": text, "answer": answer})

    return results


def calculate_distances(
    extracted_fields: list[dict[str, str]],
    gt_fields: list[dict[str, str]] | str | Path,
    moverscore_features: list[str] = None,
    save_path: str | Path = "metrics",
    save_prefix: str = "WI_POL123456789_dg",
) -> pd.DataFrame:
    """
    Create a pandas DataFrame from results with 'text' fields as the index.

    Args:
        results: List of dictionaries with format {"text": query, "answer": response}

    Returns:
        pandas DataFrame with 'text' as index and 'answer' as column
    """
    # Load ground truth fields
    if isinstance(gt_fields, list):
        gt_data = gt_fields
    else:
        gt_path = Path(gt_fields)
        with open(gt_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

    df_result = pd.DataFrame(extracted_fields)
    # df_result.set_index("text", inplace=True)
    df_result.set_index("order", inplace=True)

    df_fields = pd.DataFrame(gt_data, columns=["order", "text", "answer"])
    # df_fields.set_index("text", inplace=True)
    df_fields.set_index("order", inplace=True)
    df_fields = df_fields.rename(columns={"answer": "answer_gt"})
    df_fields["answer_extracted"] = df_result["answer"]
    # df_fields.index.name = "field"
    df_fields.rename(columns={"text": "field"}, inplace=True)

    # Calculate Levenshtein similarity ratio (0 to 1, where 1 is identical)
    df_fields["levenshtein"] = df_fields.apply(
        lambda row: Levenshtein.ratio(
            str(row["answer_gt"]),
            str(row["answer_extracted"]),
        ),
        axis=1,
    )
    # Set levenshtein to None for features in moverscore_features
    if moverscore_features:
        df_fields.loc[df_fields["field"].isin(moverscore_features), "levenshtein"] = (
            None
        )

    # Calculate MoverScore
    references = [str(row["answer_gt"]) for _, row in df_fields.iterrows()]
    hypotheses = [str(row["answer_extracted"]) for _, row in df_fields.iterrows()]
    idf_dict_ref = get_idf_dict(references)
    idf_dict_hyp = get_idf_dict(hypotheses)
    moverscore_scores = word_mover_score(
        references,
        hypotheses,
        idf_dict_ref,
        idf_dict_hyp,
        stop_words=[],
        n_gram=1,
        remove_subwords=True,
    )
    df_fields["moverscore"] = moverscore_scores
    # Set moverscore to None for features NOT in moverscore_features
    if moverscore_features:
        df_fields.loc[~df_fields["field"].isin(moverscore_features), "moverscore"] = (
            None
        )

    df_fields["levenshtein_moverscore"] = df_fields["levenshtein"].fillna(
        df_fields["moverscore"],
    )

    save_dir = Path(save_path)
    save_dir.mkdir(parents=True, exist_ok=True)
    df_fields.to_csv(Path(save_dir) / f"{save_prefix}_fields.csv")

    return df_fields


def calculate_policy_metrics(
    data: pd.DataFrame | str | Path,
    save_path: str | Path = "metrics",
    state: str = "WI",
    policy: str = "POL123456789",
    form_type: str = "hd",
    main_params: dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    Calculate metrcis per policy.

    Args:
        data: Either a pandas DataFrame or a path to a CSV file

    Returns:
        pandas DataFrame

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If input type is invalid
    """
    if isinstance(data, pd.DataFrame):
        pass
    elif isinstance(data, (str, Path)):
        csv_path = Path(data)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        data = pd.read_csv(csv_path)
    else:
        raise ValueError(
            f"Invalid input type: {type(data)}. Expected DataFrame, str, or Path",  # type: ignore
        )

    # Check if policy metrics CSV exists, load it or create new
    save_dir = Path(save_path)
    save_dir.mkdir(parents=True, exist_ok=True)
    policy_metrics_path = save_dir / "policies.csv"
    if policy_metrics_path.exists():
        df_policy_metrics = pd.read_csv(policy_metrics_path)
        next_index = len(df_policy_metrics)
    else:
        df_policy_metrics = pd.DataFrame()
        next_index = 0

    df_policy_metrics.loc[next_index, "state"] = state
    df_policy_metrics.loc[next_index, "policy"] = policy
    df_policy_metrics.loc[next_index, "type"] = form_type

    # Levenshtein, MoverScore, and Levenstein_MoverScore averages
    df_policy_metrics.loc[next_index, "levenshtein_avg"] = data["levenshtein"].mean()
    df_policy_metrics.loc[next_index, "moverscore_avg"] = data["moverscore"].mean()
    df_policy_metrics.loc[next_index, "levenshtein_moverscore_avg"] = data[
        "levenshtein_moverscore"
    ].mean()

    # Calculate binary classification metrics based on levenshtein_moverscore
    # Predicted correctly if levenshtein_moverscore == 1, incorrectly otherwise
    y_pred = (data["levenshtein_moverscore"] == 1).astype(int)
    tp = (y_pred == 1).sum()
    tn = 0
    fp = 0
    fn = (y_pred == 0).sum()
    # Accuracy: (TP + TN) / Total
    total = len(data)
    accuracy = (tp + tn) / total if total > 0 else 0.0
    # Precision: TP / (TP + FP)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    # Recall: TP / (TP + FN)
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    # F1 Score: 2 * (Precision * Recall) / (Precision + Recall)
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    # Store metrics
    df_policy_metrics.loc[next_index, "accuracy"] = accuracy
    df_policy_metrics.loc[next_index, "precision"] = precision
    df_policy_metrics.loc[next_index, "recall"] = recall
    df_policy_metrics.loc[next_index, "f1_score"] = f1_score

    # Add levenshtein of main params if provided
    if main_params:
        for key, value in main_params.items():
            matching_rows = data.loc[data["field"] == value, "levenshtein"]
            df_policy_metrics.loc[next_index, key] = (
                matching_rows.iloc[0] if len(matching_rows) > 0 else None
            )

    # Save updated policy metrics
    save_dir = Path(save_path)
    save_dir.mkdir(parents=True, exist_ok=True)
    df_policy_metrics.to_csv(Path(save_dir) / "policies.csv", index=False)

    return df_policy_metrics


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("")

    # Settings
    save_path = "metrics"
    state = "FL"
    policy = "POL987654321"
    type = "hw"  # hw or dg

    # # WI
    # main_params = {
    #     "levenshtein_first_name": "Employee Name (First)",
    #     "levenshtein_middle_name": "Employee Name (Middle)",
    #     "levenshtein_last_name": "Employee Name (Last)",
    #     "levenshtein_data_of_injury": "Injury Date",
    #     "levenshtein_policy_number": "WI Unemployment Ins. Acct No.",
    # }
    # NH
    # main_params = {
    #     "levenshtein_first_name": "Employee Name (First & Last) - First Name",
    #     "levenshtein_middle_name": "Employee Name (First & Last) - First Name",
    #     "levenshtein_last_name": "Employee Name (First & Last) - Last Name",
    #     "levenshtein_data_of_injury": "Injury Date / Time",
    #     "levenshtein_policy_number": "Policy Number",
    # }
    # MN
    # main_params = {
    #     "levenshtein_first_name": "EMPLOYEE First name",
    #     "levenshtein_middle_name": "EMPLOYEE Middle name",
    #     "levenshtein_last_name": "EMPLOYEE Last name",
    #     "levenshtein_data_of_injury": "DATE OF CLAIMED INJURY",
    #     "levenshtein_policy_number": "Policy # (including effective dates) or self-insured certificate #",
    # }
    # KS
    # main_params = {
    #     "levenshtein_first_name": "First",
    #     "levenshtein_middle_name": "Middle",
    #     "levenshtein_last_name": "Last",
    #     "levenshtein_data_of_injury": "Date of injury or occupational disease",
    #     "levenshtein_policy_number": "Policy number",
    # }
    # IA
    # main_params = {
    #     "levenshtein_first_name": "Employee Name - First",
    #     "levenshtein_middle_name": "Employee Name - Middle",
    #     "levenshtein_last_name": "Employee Name - Last",
    #     "levenshtein_data_of_injury": "Date of Injury",
    #     "levenshtein_policy_number": "Policy/Contract Number",
    # }
    # generic
    # main_params = {
    #     "levenshtein_first_name": "First Name",
    #     "levenshtein_middle_name": "First Name",
    #     "levenshtein_last_name": "Last Name",
    #     "levenshtein_data_of_injury": "DATE OF INJURY/ILLNESS",
    #     "levenshtein_policy_number": "POLICY/SELF-INSURED NUMBER",
    # }
    # FL
    main_params = {
        "levenshtein_first_name": "NAME (First, Middle, Last) - First",
        "levenshtein_middle_name": "NAME (First, Middle, Last) - Middle",
        "levenshtein_last_name": "NAME (First, Middle, Last) - Last",
        "levenshtein_data_of_injury": "Date of Accident (Month-Day-Year)",
        "levenshtein_policy_number": "POLICY/MEMBER NUMBER",
    }

    # WI
    # moverscore_features = [
    #     "Sex",
    #     "Employer Mailing Address",
    #     "Employee's Usual Work Schedule When Injured Start Time",
    #     "Nature of Business (Specific Product)",
    #     "Injury Description - Describe Activities of Employee When Injury or Illness Occurred and What Tools, Machinery, Objects, Chemicals, Etc. Were Involved.",
    #     "What Happened to Cause This Injury or Illness? (Describe How The Injury Occurred)",
    #     "What Was The Injury or Illness? (State the Part of Body Affected and How It Was Affected)",
    # ]
    # OH
    # moverscore_features = [
    #     "Diagnosis(es)-narrative description including as appropriate, the location and body part, and ICD code(s)."
    #     "Accident description (Describe the sequence of events that directly caused the injury or death.)",
    #     "Part(s) of body affected (For example: Left knee, right index finger)",
    #     "Sex",
    # ]
    # NY
    # moverscore_features = [
    #     "Part of BodyCause of Injury",
    #     "Accident/Injury Description",
    # ]
    # NH
    # moverscore_features = [
    #     "Gender",
    #     "Occupation when Injured",
    #     "Accident Description",
    #     "Body part Injured",
    #     "Cause of Injury",
    #     "Nature of Injury",
    #     "If so, at what duty status?",
    #     "Initial Treatment",
    # ]
    # MN
    # moverscore_features = [
    #     "Gender",
    #     "Tell us how the injury/illness occurred, what the employee was doing before the incident (give details), and what the injury/illness was.",
    #     "What was the injury or illness (include the part(s) of body)?",
    #     "What tools, equipment, machines, objects, or substances were involved?",
    # ]
    # KS
    # moverscore_features = [
    #     "Nature of business",
    #     "occupation",
    #     "How did accident occur?",
    #     "What was employee doing when injured?",
    #     "Name substance or object that directly caused injury*",
    #     "Describe in detail nature and extent of injury, indicate part of body involved*",
    # ]
    # IA
    # moverscore_features = [
    #     "Gender",
    #     "Tax Filing Status",
    #     "Occupation Description",
    #     "Describe the nature of the injury",
    #     "Part of Body Affected Code",
    #     "Part(s) of body directly affected by the injury or illness",
    #     "Describe the events that caused the injury",
    #     "Name the object or substance that directly injured the employee",
    #     "Specify activity the employee was engaged in when the event occurred"
    # ]
    # FL
    moverscore_features = [
        "EMPLOYEE'S DESCRIPTION OF ACCIDENT (Include Cause of Injury)",
        "SEX",
        "NATURE OF BUSINESS",
    ]

    form_model_json_path = (
        f"/home/maken/symfa/claim-assistant/data/amtrust/{state}/form_model.json"
    )
    gt_answers_json_path = (
        f"/home/maken/symfa/claim-assistant/data/amtrust/{state}/answers_{policy}.json"
    )
    input_pdf_path = f"/home/maken/symfa/claim-assistant/data/amtrust/{state}/form_{type}_{policy}.pdf"

    # Process PDF
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables or .env file",
        )
    client = OpenAI(api_key=api_key)
    form_processor = FormFillingProcessor(client, logger, model_name="gpt-5-2025-08-07")

    logger.info(f"Starting PDF processing with OpenAI for policy {policy}...")
    form: Form = form_processor.process(input_pdf_path, form_model_json_path)
    # Extract only 'text' and 'answer' from each field
    exctracted_fields = [
        field.model_dump(include={"order", "text", "answer"}) for field in form.fields
    ]

    # results = process_pdf_with_openai(
    #     pdf_file="/home/maken/symfa/claim-assistant/data/amtrust/WI/form_hw_POL123456789.pdf",
    #     texts=texts,
    #     # model="gpt-5-mini-2025-08-07",
    #     model="gpt-5-2025-08-07",
    # )
    # logger.info(f"PDF processing completed for policy {policy}.")
    # print(form)
    # results = [
    #     {"text": "What is the policy number?", "answer": None},
    #     {"text": "What is the insured's name?", "answer": "Joe Doe"},
    #     {"text": "What is the coverage amount?", "answer": "$100,000"},
    #     {"text": "Employee Name (First)", "answer": "Joe"},
    #     {"text": "Employee Name (Middle)", "answer": "A."},
    #     {"text": "Employee Name (Last)", "answer": "Doe"},
    #     {"text": "Injury Date", "answer": "2023-01-15"},
    #     {"text": "WI Unemployment Ins. Acct No.", "answer": "POL123456789"},
    # ]
    # gt = [
    #     {"text": "What is the policy number?", "answer": None},
    #     {"text": "What is the insured's name?", "answer": "Andrew Doe"},
    #     {"text": "What is the coverage amount?", "answer": "$150,000"},
    #     {"text": "Employee Name (First)", "answer": "Andrew"},
    #     {"text": "Employee Name (Middle)", "answer": "A."},
    #     {"text": "Employee Name (Last)", "answer": "Doe"},
    #     {"text": "Injury Date", "answer": "2023-01-15"},
    #     {"text": "WI Unemployment Ins. Acct No.", "answer": "POL123456789"},
    # ]

    print(exctracted_fields)
    logger.info("Starting distance calculations...")
    df = calculate_distances(
        extracted_fields=exctracted_fields,
        gt_fields=gt_answers_json_path,
        moverscore_features=moverscore_features,
        save_path=save_path,
        save_prefix=f"{state}_{policy}_{type}",
    )
    logger.info("Distance calculations completed.")
    # print(df)

    df = calculate_policy_metrics(
        data=df,
        save_path=save_path,
        state=state,
        policy=policy,
        form_type=type,
        main_params=main_params,
    )

    print(df)
