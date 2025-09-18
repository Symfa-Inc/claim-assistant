from uuid import uuid4

import requests
from pydantic import BaseModel, Field

pdf_url = "https://s23.q4cdn.com/407969754/files/doc_earnings/2023/q4/transcript/Uber-Q4-23-Prepared-Remarks.pdf"

# Get PDF bytes
pdf_response = requests.get(pdf_url)
assert pdf_response.status_code == 200
pdf_bytes = pdf_response.content


user_id = str(uuid4())
headers = {"x-key": user_id}


class FinancialData(BaseModel):
    name: str = Field(..., description="Name of the financial figure, such as revenue.")
    value: float = Field(..., description="Nominal earnings in local currency.")
    scale: str = Field(..., description="Scale of figure, such as MM, B, or percent.")
    period_start: str = Field(
        ...,
        description="The start of the time period in ISO format.",
    )
    period_duration: int = Field(..., description="Duration of period, in months")
    evidence: str = Field(
        ...,
        description="Verbatim sentence of text where figure was found.",
    )


url = "https://extract-server-f34kggfazq-uc.a.run.app"

data = {
    "user_id": user_id,
    "description": "Financial revenues and other figures.",
    "schema": FinancialData.schema(),
    "instruction": (
        "Extract standard financial figures, specifically earnings and "
        "revenue figures. Only extract historical facts, not estimates or guidance."
    ),
}

response = requests.post(f"{url}/extractors", json=data, headers=headers)
extractor = response.json()


result = requests.post(
    f"{url}/extract",
    data={"extractor_id": extractor["uuid"], "model_name": "gpt-3.5-turbo"},
    files={"file": pdf_bytes},
    headers=headers,
)

result.json()
