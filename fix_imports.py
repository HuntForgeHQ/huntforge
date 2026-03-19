import re

filepath = r"c:\Users\nimes\OneDrive\Desktop\huntforge\Project\huntforge\core\orchestrator.py"
with open(filepath, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('from modules.'):
        # e.g. from modules.passive.subfinder import Subfinder
        # => from modules.passive.subfinder import SubfinderModule as Subfinder
        match = re.match(r'(from modules\..+ import )(\w+)(.*)', line)
        if match:
            cls_name = match.group(2)
            if not cls_name.endswith('Module'):
                new_line = f"{match.group(1)}{cls_name}Module as {cls_name}{match.group(3)}\n"
                new_lines.append(new_line)
                continue
    new_lines.append(line)

with open(filepath, 'w') as f:
    f.writelines(new_lines)
print("Imports fixed.")
