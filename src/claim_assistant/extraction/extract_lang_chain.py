import json
from uuid import uuid4

import requests

from claim_assistant.extraction.data_form_classes import WorkSafeFormData

conversation_path = (
    "/home/maken/symfa/claim-assistant/data/forms/work_safe/conversation.txt"
)
file_name = "work_safe_form"

# Get txt bytes
with open(conversation_path, "rb") as f:
    bytes = f.read()


user_id = str(uuid4())
headers = {"x-key": user_id}

url = "https://extract-server-f34kggfazq-uc.a.run.app"

data = {
    "user_id": user_id,
    "description": "Insurance claim form data extraction from worker injury claims.",
    "schema": WorkSafeFormData.model_json_schema(),
    "instruction": (
        "Extract worker injury claim information from insurance forms. "
        "Focus on personal details, injury specifics, employment information, and medical data."
    ),
}

response = requests.post(f"{url}/extractors", json=data, headers=headers)
extractor = response.json()


result = requests.post(
    f"{url}/extract",
    data={"extractor_id": extractor["uuid"], "model_name": "gpt-3.5-turbo"},
    files={"file": bytes},
    headers=headers,
)

print(result.json())
with open(f"{file_name}.json", "w") as f:
    json.dump(result.json(), f, indent=2)
