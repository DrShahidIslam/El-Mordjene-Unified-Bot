import ast
import os
import sys

def check_syntax(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            ast.parse(f.read())
        return True, None
    except Exception as e:
        return False, str(e)

root_dir = "."
py_files = []
for root, dirs, files in os.walk(root_dir):
    if "node_modules" in root or ".venv" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            py_files.append(os.path.join(root, file))

errors = []
for py_file in py_files:
    ok, err = check_syntax(py_file)
    if not ok:
        errors.append(f"{py_file}: {err}")

if errors:
    print("\n".join(errors))
    sys.exit(1)
else:
    print("No syntax errors found.")
