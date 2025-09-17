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


def generate_conversation(questions):
    random.shuffle(questions)

    system_prompt = (
        "You are generating a realistic conversation between an operator and a client. "
        "The operator must ask all of these questions (order can be mixed). "
        "The client should provide plausible answers. "
        "The style should be chat-like with timestamps, alternating between Operator and Client. "
        "Keep answers concise but natural."
    )

    content_prompt = "Here are the questions:\n"
    for q in questions:
        content_prompt += f"- {q['question']}\n"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_prompt},
        ],
        temperature=1.2,  # higher randomness
    )

    return response.choices[0].message.content


def process_forms(base_dir=BASE_DIR):
    results = {}

    for form_name in os.listdir(base_dir):
        form_dir = os.path.join(base_dir, form_name)
        json_file = os.path.join(form_dir, "form_questions.json")

        if os.path.isfile(json_file):
            with open(json_file, "r", encoding="utf-8") as f:
                questions = json.load(f)

            # Only extract question text
            question_texts = [q for q in questions if "question" in q]

            print(f"Generating conversation for: {form_name}")
            conversation = generate_conversation(question_texts)

            results[form_name] = conversation

    return results


if __name__ == "__main__":
    conversations = process_forms()

    # Save conversations to output files

    for form_name, convo in conversations.items():
        out_file = os.path.join(out_dir, form_name, "conversation.txt")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(convo)

        print(f"Saved conversation: {out_file}")
