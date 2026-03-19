import os
import re

MODULES_DIR = r"c:\Users\nimes\OneDrive\Desktop\huntforge\Project\huntforge\modules"

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # regex to find "class Something(BaseModule):"
    # and replace it with "class SomethingModule(BaseModule):"
    
    # But wait, what if it's already SomethingModule(BaseModule)?
    def repl(m):
        cls_name = m.group(1)
        if not cls_name.endswith('Module'):
            return f"class {cls_name}Module(BaseModule):"
        return m.group(0)

    new_content = re.sub(r'class\s+([A-Za-z0-9_]+)\(BaseModule\):', repl, content)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")

for root, dirs, files in os.walk(MODULES_DIR):
    for f in files:
        if f.endswith('.py'):
            process_file(os.path.join(root, f))
