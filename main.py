import os
import sys

import httpx
import ollama
from dotenv import load_dotenv
from google.genai import types

from schemas import (
    schema_get_file_content,
    schema_get_files_info,
    schema_run_python_file,
    schema_write_file,
)
from call_funtion import call_function

load_dotenv()

SYSTEM_PROMPT = """
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

def generate_content_raw(api_key: str, messages: list[dict], system_prompt: str, tools_payload: list[dict]) -> dict:
    """Call Gemini generateContent directly via httpx to preserve thoughtSignature in response."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"models/gemini-3.6-flash:generateContent?key={api_key}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": messages,
        "tools": tools_payload,
        "generationConfig": {"thinkingConfig": {"thinkingBudget": -1}},
    }
    response = httpx.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()

def run_gemini_agent(prompt: str):
    api_key = os.getenv("GEMINI_KEY")

    # Derive the raw API payload from the schema objects already defined in schemas.py
    tools_payload = [
        {
            "function_declarations": [
                s.model_dump(exclude_none=True)
                for s in [
                    schema_get_files_info,
                    schema_get_file_content,
                    schema_run_python_file,
                    schema_write_file,
                ]
            ]
        }
    ]

    # Messages are kept as raw dicts so thoughtSignature is preserved verbatim
    messages: list[dict] = [
        {"role": "user", "parts": [{"text": prompt}]}
    ]

    max_iterations = 20
    for iteration in range(max_iterations):
        data = generate_content_raw(api_key, messages, SYSTEM_PROMPT, tools_payload)

        if "error" in data:
            print(f"API Error: {data['error']['message']}")
            return

        candidates = data.get("candidates", [])
        if not candidates:
            print("No candidates in response")
            return

        candidate_content = candidates[0].get("content", {})
        usage = data.get("usageMetadata", {})

        # Append the model's raw content (including thoughtSignature) verbatim
        messages.append(candidate_content)

        # Collect function calls from the response parts
        function_calls = [
            part["functionCall"]
            for part in candidate_content.get("parts", [])
            if "functionCall" in part
        ]

        if function_calls:
            # Execute each function call and collect results
            tool_parts = []
            for fc in function_calls:
                # Build a lightweight object that call_function can use
                fc_obj = types.FunctionCall(name=fc["name"], args=fc.get("args", {}))
                result = call_function(fc_obj)
                print(f"-> {result['content']}")
                tool_parts.append({
                    "functionResponse": {
                        "name": fc["name"],
                        "response": {"result": result["content"]},
                    }
                })
            messages.append({"role": "user", "parts": tool_parts})
        else:
            # No function call — extract text and finish
            text_parts = [
                part.get("text", "")
                for part in candidate_content.get("parts", [])
                if "text" in part
            ]
            print("".join(text_parts))
            print(f"Prompt Token: {usage.get('promptTokenCount', '?')}")
            print(f"Response Token: {usage.get('candidatesTokenCount', '?')}")
            break
    else:
        print("Reached maximum iterations (20) without completing.")


def get_ollama_tools() -> list[dict]:
    """Convert Gemini FunctionDeclaration schemas into Ollama/OpenAI JSON Schema format."""
    def to_ollama_type(t: str) -> str:
        return t.lower() if isinstance(t, str) else str(t).lower()
        
    tools = []
    schemas = [
        schema_get_files_info,
        schema_get_file_content,
        schema_run_python_file,
        schema_write_file,
    ]
    for s in schemas:
        s_dump = s.model_dump(exclude_none=True)
        if "parameters" in s_dump:
            s_dump["parameters"]["type"] = to_ollama_type(s_dump["parameters"].get("type", "OBJECT"))
            props = s_dump["parameters"].get("properties", {})
            for key, prop in props.items():
                if "type" in prop:
                    prop["type"] = to_ollama_type(prop["type"])
                if prop.get("type") == "array" and "items" in prop and "type" in prop["items"]:
                    prop["items"]["type"] = to_ollama_type(prop["items"]["type"])
                    
        tools.append({
            "type": "function",
            "function": s_dump
        })
    return tools


def run_ollama_agent(prompt: str, model: str):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    
    tools = get_ollama_tools()
    max_iterations = 20
    
    for iteration in range(max_iterations):
        response = ollama.chat(
            model=model,
            messages=messages,
            tools=tools
        )
        
        message = response.get("message", {})
        messages.append(message)
        
        tool_calls = message.get("tool_calls", [])
        if not tool_calls:
            print(message.get("content", ""))
            break
            
        for tool_call in tool_calls:
            fc_name = tool_call["function"]["name"]
            fc_args = tool_call["function"]["arguments"]
            # Convert args to our internal types.FunctionCall for call_function
            fc_obj = types.FunctionCall(name=fc_name, args=fc_args)
            result = call_function(fc_obj)
            print(f"-> {result['content']}")
            
            messages.append({
                "role": "tool",
                "content": str(result["content"]),
                "name": fc_name
            })
    else:
        print("Reached maximum iterations (20) without completing.")


def main():
    if len(sys.argv) < 2:
        print("I need a Prompt")
        sys.exit(1)
        
    prompt = sys.argv[1]
    
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        print(f"Running agent with Ollama (model: {model})...")
        run_ollama_agent(prompt, model)
    else:
        run_gemini_agent(prompt)


if __name__ == "__main__":
    main()