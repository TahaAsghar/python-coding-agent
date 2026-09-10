from collections.abc import Callable

from functions.get_file_content import get_file_content
from functions.get_files_info import get_files_info
from functions.run_python_file import run_python_file
from functions.write_file import write_file


WORKING_DIR = "calculator"

function_map: dict[str, Callable[..., str]] = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "run_python_file": run_python_file,
    "write_file": write_file,
}


def call_function(function_call, verbose: bool = False) -> dict:
    function_name = function_call.name
    function_args = dict(function_call.args or {})
    if verbose:
        print(f" - Calling function: {function_name}({function_args})")
    else:
        print(f" - Calling function: {function_name}")

    if function_name not in function_map:
        return {
            "role": "tool",
            "content": f"Error: Unknown function: {function_name}",
        }

    function_args["working_directory"] = WORKING_DIR
    if function_name == "run_python_file":
        function_args.setdefault("args", [])

    result = function_map[function_name](**function_args)

    return {
        "role": "tool",
        "content": result,
    }
