import os


MAX_CHARS = 10000

def get_file_content(working_directory: str, file_path: str) -> str:
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path)) 
    

    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: Cannot list "{file_path}" as it is outside the permitted working directory'
    
    if not os.path.isfile(abs_file_path):
        return f'Error: "{file_path}" is not a file' 


    
    file_content_string = ""

    try:
        with open(abs_file_path, "r") as f:
            file_content_string = f.read(MAX_CHARS)
            if len(file_content_string) >= MAX_CHARS:
                file_content_string += (f'[.. File "{file_path}" truncated to 1000 Char]')

        return file_content_string
        
    except Exception as e:
        return f'Exception reading file: {e}'