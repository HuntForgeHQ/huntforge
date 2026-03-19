import os
import shutil

ROOT = r"c:\Users\nimes\OneDrive\Desktop\huntforge\Project\huntforge"

# 1. Missing static files
def touch(path, content=""):
    full_path = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    if not os.path.exists(full_path):
        with open(full_path, "w") as f:
            f.write(content)

# create files from README structure
touch("CONTRIBUTING.md", "# Contributing to HuntForge")
touch("core/efficiency_filter.py", "# Efficiency Filter (Stub)")
touch("core/deduplicator.py", "# Deduplicator (Stub)")
touch("config/tool_configs.yaml", "# Missing Tool Configs")
touch("config/machine_profiles.yaml", "# Missing Machine Profiles")
touch("data/bug_bounty_scopes.json", "{}")
touch("scripts/install_tools.sh", "#!/bin/bash\n# Install Tools")
touch("scripts/setup_wizard.py", "# Setup Wizard")
touch("scripts/check_tools.py", "# Check Tools")
touch("dashboard/static/style.css", "/* Style CSS */")

# 2. Move base_module.py from core/ to modules/
old_base = os.path.join(ROOT, "core", "base_module.py")
new_base = os.path.join(ROOT, "modules", "base_module.py")

if os.path.exists(old_base):
    shutil.move(old_base, new_base)
    print("Moved base_module.py to modules/")

# 3. Update all imports in modules/**/*.py
modules_dir = os.path.join(ROOT, "modules")
for root, dirs, files in os.walk(modules_dir):
    for f in files:
        if f.endswith(".py"):
            filepath = os.path.join(root, f)
            with open(filepath, "r") as rfile:
                content = rfile.read()
            
            new_content = content.replace("from core.base_module import BaseModule", "from modules.base_module import BaseModule")
            
            if new_content != content:
                with open(filepath, "w") as wfile:
                    wfile.write(new_content)
                print(f"Updated imports in {f}")

print("Structure alignment complete.")
