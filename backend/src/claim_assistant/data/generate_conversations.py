import json
import os
import random
from datetime import timedelta

from openai import OpenAI

from claim_assistant import PROJECT_DIR
from claim_assistant.data.settings import OpenAISettings

# configure your OpenAI key
settings = OpenAISettings()
client = OpenAI(api_key=settings.openai_api_key)

BASE_DIR = os.path.join(PROJECT_DIR, "data", "forms")
out_dir = os.path.join(PROJECT_DIR, "data", "forms")


def generate_timestamp(start_time, index):
    """Return a timestamp string offset by index minutes from start_time."""
    return (start_time + timedelta(minutes=index)).strftime("%Y-%m-%d %H:%M:%S")


def fill_form(questions: list[dict]) -> list[dict]:
    """
    Ask LLM to fill out the form with plausible answers.
    Returns a list of dicts with "question", "description", "data_type", "answer".
    """
    system_prompt = (
        "You are completing a workers' compensation claim form. "
        "For each question, generate a plausible but fictional answer. "
        "Keep the answers realistic and consistent. "
        "Return a JSON array. Each object must contain: "
        "question, description, data_type, and answer."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "form_answers",
                "schema": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "question": {"type": "string"},
                                    "description": {"type": ["string", "null"]},
                                    "data_type": {"type": "string"},
                                    "answer": {},
                                },
                                "required": ["question", "data_type", "answer"],
                            },
                        },
                    },
                    "required": ["items"],
                },
            },
        },
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(questions, indent=2)},
        ],
        temperature=1.2,
    )
    raw_content = response.choices[0].message.content
    if not raw_content:
        raise ValueError("LLM returned empty content when filling the form")

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError as e:
        print("JSON parse failed. Raw output:")
        print(raw_content)
        raise e

    answers = parsed["items"]
    # Ensure it's a list
    if not isinstance(answers, list):
        raise ValueError(f"Expected list of Q&A objects, got: {type(answers)}")

    # Ensure length matches
    if len(answers) != len(questions):
        raise ValueError(
            f"Number of answers ({len(answers)}) does not match number of questions ({len(questions)})",
        )

    # Ensure every question has an answer
    for q in answers:
        if "answer" not in q or q["answer"] in (None, ""):
            q["answer"] = "N/A"

    return answers


def generate_conversation(questions_with_answers: list[dict]) -> str:
    """
    Generate a conversation between operator and client using existing answers.
    """
    shuffled = questions_with_answers[:]
    random.shuffle(shuffled)

    system_prompt = (
        "You are generating a realistic conversation between an operator and a client. "
        "The operator must ask all of these questions (order can be mixed). "
        "The client should provide the given answers. "
        "The style should be chat-like with timestamps, alternating between Operator and Client. "
        "Keep answers concise but natural."
    )

    content_prompt = "Here are the questions with their answers:\n"
    for qa in shuffled:
        content_prompt += f"- Q: {qa['question']}\n  A: {qa['answer']}\n"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_prompt},
        ],
        temperature=1.2,
    )

    return response.choices[0].message.content


def process_forms(base_dir=BASE_DIR):
    for form_name in os.listdir(base_dir):
        form_dir = os.path.join(base_dir, form_name)
        json_file = os.path.join(form_dir, "form_questions.json")

        if os.path.isfile(json_file):
            with open(json_file, "r", encoding="utf-8") as f:
                questions = json.load(f)

            # step 1: fill form
            print(f"Filling form for: {form_name}")
            form_with_answers = fill_form(questions)

            form_answers_file = os.path.join(form_dir, "form_answers.json")
            with open(form_answers_file, "w", encoding="utf-8") as f:
                json.dump(form_with_answers, f, indent=2, ensure_ascii=False)
            print(f"Saved form answers: {form_answers_file}")

            # step 2: generate conversation
            print(f"Generating conversation for: {form_name}")
            conversation = generate_conversation(form_with_answers)

            convo_file = os.path.join(form_dir, "conversation.txt")
            with open(convo_file, "w", encoding="utf-8") as f:
                f.write(conversation)
            print(f"Saved conversation: {convo_file}")


if __name__ == "__main__":
    conversations = process_forms()
