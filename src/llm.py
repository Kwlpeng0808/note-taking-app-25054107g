import os
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

# Use getenv so we can provide a helpful error instead of KeyError
token = os.getenv("GITHUB_TOKEN")
endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1-mini"

if not token:
    raise RuntimeError(
        "GITHUB_TOKEN is not set. Add it to your .env file or set the environment variable before running."
    )


def run_chat():
    client = OpenAI(
        base_url=endpoint,
        api_key=token,
    )

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": "What is the capital of France?",
            }
        ],
        temperature=1.0,
        top_p=1.0,
        model=model
    )

    print(response.choices[0].message.content)


if __name__ == '__main__':
    run_chat()

