from functions.get_files_info import get_files_info

def main():
    working_dir = "calculator"

    root_contents = get_files_info(working_dir)
    print(root_contents)

    pkg_contents = get_files_info(working_dir, "pkg")
    print(pkg_contents)

    a_contents = get_files_info(working_dir, "/bin")
    print(a_contents)

    b_contents = get_files_info(working_dir, "../")
    print(b_contents)

main()