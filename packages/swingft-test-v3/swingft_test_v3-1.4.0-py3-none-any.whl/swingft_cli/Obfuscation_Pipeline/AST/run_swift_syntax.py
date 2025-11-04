import os
import subprocess
import shutil
import swingft_cli
from importlib import resources

def run_command(cmd):
    subprocess.run(cmd, capture_output=True, text=True)

def run_swift_syntax(code_project_dir):
    dest_dir = os.path.join(code_project_dir, "SyntaxAST")

    with resources.as_file(resources.files("swingft_cli").joinpath("Obfuscation_Pipeline/AST/SyntaxAST")) as src:
        shutil.copytree(src, dest_dir, dirs_exist_ok=True)

    target_name = "SyntaxAST"

    swift_list_dir = os.path.join(code_project_dir, "swift_file_list.txt")
    external_list_dir = os.path.join(code_project_dir, "AST", "output", "external_file_list.txt")

    os.chdir(dest_dir)
    build_marker_file = os.path.join(".build", "build_path.txt")
    previous_build_path = ""
    if os.path.exists(build_marker_file):
        with open(build_marker_file, "r") as f:
            previous_build_path = f.read().strip()
    
    current_build_path = os.path.abspath(".build")
    if previous_build_path != current_build_path or previous_build_path == "":
        run_command(["swift", "package", "clean"])
        shutil.rmtree(".build", ignore_errors=True)
        run_command(["swift", "build"])
        with open(build_marker_file, "w") as f:
            f.write(current_build_path)

    run_command(["swift", "run", target_name, swift_list_dir, external_list_dir, code_project_dir])
