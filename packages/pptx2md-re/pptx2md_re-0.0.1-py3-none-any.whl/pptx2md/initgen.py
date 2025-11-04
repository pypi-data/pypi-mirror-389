import os
import ast

def extract_exports(filepath):
    """
    Extracts top-level function and class names from a Python file.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        node = ast.parse(f.read(), filename=filepath)
    exports = []
    for n in node.body:
        if isinstance(n, ast.FunctionDef) or isinstance(n, ast.ClassDef):
            exports.append(n.name)
    return exports

def generate_init(dirpath):
    """
    Generates a __init__.py file in the given directory that re-exports functions and classes from local modules.
    """
    exports = []
    lines = []
    for file in os.listdir(dirpath):
        if file.endswith(".py") and file != "__init__.py":
            modname = file[:-3]
            filepath = os.path.join(dirpath, file)
            names = extract_exports(filepath)
            if names:
                lines.append(f"from .{modname} import {', '.join(names)}")
                exports.extend(names)

    if lines:
        lines.append("")
        lines.append(f"__all__ = {exports}")
        init_path = os.path.join(dirpath, "__init__.py")
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"✅ Generated: {init_path}")

def walk_and_generate(root):
    """
    Recursively walks through all subdirectories and generates __init__.py files.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        generate_init(dirpath)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python generate_init_files.py <path-to-package-root>")
        sys.exit(1)
    
    root_dir = sys.argv[1]
    walk_and_generate(root_dir)
