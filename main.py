import os
import sys

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types
from schemas import (
    schema_get_file_content,
    schema_get_files_info,
    schema_run_python_file,
    schema_write_file,
)
from call_funtion import call_function

load_dotenv()

def main():
    api_key = os.getenv("GEMINI_KEY")
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            client_args={"transport": httpx.HTTPTransport(local_address="0.0.0.0")},
        ),
    )

    system_prompt = """
You are a helpful AI coding agent.

Use a function call only when the user needs information from the working directory or codebase.
For general questions (for example, "what is the color of the sky"), answer in text and do not call any function.

You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

All paths you provide should be relative to the working directory.
You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
"""

    available_tools = types.Tool(
        function_declarations=[
            schema_get_files_info,
            schema_get_file_content,
            schema_run_python_file,
            schema_write_file,
        ]
    )

    if len(sys.argv) < 2:
        print("I need a Prompt")
        sys.exit(1)

    prompt = sys.argv[1] 

    messages = [types.Content(role="user", parts=[types.Part(text=prompt)])]
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[available_tools],
    )

    max_iterations = 20
    for iteration in range(max_iterations):
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=messages,
            config=config,
        )

        if response is None or response.usage_metadata is None:
            print("response is malformed")
            return

        if response.candidates and response.candidates[0].content:
            messages.append(response.candidates[0].content)

        if response.function_calls:
            tool_parts = []
            for function_call in response.function_calls:
                result = call_function(function_call)
                print(f"-> {result['content']}")
                tool_parts.append(
                    types.Part.from_function_response(
                        name=function_call.name,
                        response={"result": result["content"]},
                    )
                )
            messages.append(types.Content(role="user", parts=tool_parts))
        else:
            print(response.text)
            print(f"Prompt Token: {response.usage_metadata.prompt_token_count}")
            print(f"Response Token: {response.usage_metadata.candidates_token_count}")
            break
    else:
        print("Reached maximum iterations (20) without completing.")


main()