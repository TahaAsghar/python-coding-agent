from email import message
import os
import sys

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def main():
    api_key = os.getenv("GEMINI_KEY")
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            client_args={"transport": httpx.HTTPTransport(local_address="0.0.0.0")},
        ),
    )

    if len(sys.argv) < 2:
        print("I need a Prompt")
        sys.exit(1)

    prompt = sys.argv[1] 

    messages = [types.Content(role="user", parts=[types.Part(text=prompt)])]

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=messages,
    )

    print(response.text)
    print(f"Prompt Token: {response.usage_metadata.prompt_token_count}")
    print(f"Response Token: {response.usage_metadata.candidates_token_count}")


main()