import json
import os

from claim_assistant import PROJECT_DIR
from claim_assistant.data.generate_conversations import fill_form, generate_conversation
from claim_assistant.data.settings import OpenAISettings
from openai import OpenAI

# configure your OpenAI key
settings = OpenAISettings()
client = OpenAI(api_key=settings.openai_api_key)

BASE_DIR = os.path.join(PROJECT_DIR, "data", "forms")
out_dir = os.path.join(PROJECT_DIR, "data", "forms")


def process_one_form(form_name="dwc", base_dir=BASE_DIR, n_samples=3):
    form_dir = os.path.join(base_dir, form_name)
    json_file = os.path.join(form_dir, "form_questions.json")

    if not os.path.isfile(json_file):
        raise FileNotFoundError(f"No form_questions.json found for form {form_name}")

    with open(json_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    for i in range(1, n_samples + 1):
        # step 1: fill form
        print(f"Filling form {form_name}, sample {i}")
        form_with_answers = fill_form(questions)

        form_answers_file = os.path.join(form_dir, f"form_answers_{i}.json")
        with open(form_answers_file, "w", encoding="utf-8") as f:
            json.dump(form_with_answers, f, indent=2, ensure_ascii=False)
        print(f"Saved form answers: {form_answers_file}")

        # step 2: generate conversation
        print(f"Generating conversation for {form_name}, sample {i}")
        conversation = generate_conversation(form_with_answers)

        convo_file = os.path.join(form_dir, f"conversation_{i}.txt")
        with open(convo_file, "w", encoding="utf-8") as f:
            f.write(conversation)
        print(f"Saved conversation: {convo_file}")


if __name__ == "__main__":
    process_one_form("dwc", n_samples=3)
