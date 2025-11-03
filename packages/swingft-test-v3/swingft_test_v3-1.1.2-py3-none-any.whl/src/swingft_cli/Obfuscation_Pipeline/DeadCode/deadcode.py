import os
from .identifier_list import read_identifier_list
from .insert_deadcode import insert_deadcode

def deadcode(obf_project_dir):
    swift_file_path = []
    file_path = os.path.join(obf_project_dir, "swift_file_list.txt")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                swift_file_path.append(line)
    
    read_identifier_list(obf_project_dir)
    insert_deadcode(swift_file_path)