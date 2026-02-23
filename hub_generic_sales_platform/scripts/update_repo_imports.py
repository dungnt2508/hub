import os
import re

root_dir = "g:/project python/hub/bot_v4"

# Map old module names to new repository imports
# Since we are exposing everything in repositories/__init__.py, we can map to app.infrastructure.database.repositories
old_to_new = {
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
    "app.infrastructure.database.repositories": "app.infrastructure.database.repositories",
}

def replace_in_file(file_path):
    if "app\\infrastructure\\database\\repositories" in file_path:
        return # Skip the repositories themselves to avoid circular or weird stuff
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    for old, new in old_to_new.items():
        if old in content:
            content = content.replace(old, new)
            modified = True
            
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated repositories import: {file_path}")

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".py"):
            replace_in_file(os.path.join(root, file))
