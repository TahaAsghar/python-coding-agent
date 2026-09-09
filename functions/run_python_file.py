import os
import subprocess
import time

def run_python_file(working_directory: str, file_path: str, args: list[str]):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path)) 
    

    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: Cannot list "{file_path}" as it is outside the permitted working directory'
    
    if not os.path.isfile(abs_file_path):
        return f'Error: "{file_path}" is not a file' 
    
    if not file_path.endswith('.py'):
        return f'Error: "{file_path}" is not a Python File'

    try:
        final_args = ["python3", file_path]
        final_args.extend(args)
        output = subprocess.run(final_args,cwd=working_directory, timeout=30, capture_output=True)
        final_string = f"""
        STDOUT: {output.stdout}
        STDERR: {output.stderr}
         """
        return final_string

    except Exception as e:
        return f'Error executing Python File, {e}'
