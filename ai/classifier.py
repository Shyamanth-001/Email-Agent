import os

from dotenv import load_dotenv
from groq import Groq

from ai.schemas import EmailClassification


load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


SYSTEM_PROMPT = """
You are an email classification system for a small business.

Analyze the incoming email and return the result as valid JSON.

The JSON object MUST contain exactly these fields:

{
    "category": "...",
    "priority": "...",
    "sentiment": "...",
    "summary": "...",
    "requires_response": true
}

Rules:

1. category must be one of:
   - technical_support
   - billing
   - sales
   - order
   - complaint
   - general
   - spam
   - other

2. priority must be one of:
   - low
   - medium
   - high

3. sentiment must be one of:
   - positive
   - neutral
   - negative
   - frustrated

4. summary must be a concise factual summary of the email.

5. requires_response must be either true or false.

6. Do not invent information that is not present in the email.
7. Do not assume the customer's problem has been solved.
8. If the email is ambiguous, choose "other".

Return only the JSON object.
"""


def classify_email(
    subject: str,
    body: str
) -> EmailClassification:

    user_prompt = f"""
Email subject:
{subject}

Email body:
{body}
"""

    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        response_format={
            "type": "json_object"
        },
        temperature=0
    )

    content = completion.choices[0].message.content

    result = EmailClassification.model_validate_json(
        content
    )

    return result