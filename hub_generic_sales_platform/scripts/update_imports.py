import os

root_dir = "g:/project python/hub/bot_v4"
target_str = "app.infrastructure.database.models"
replacement_str = "app.infrastructure.database.models"

def replace_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if target_str in content:
        new_content = content.replace(target_str, replacement_str)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated: {file_path}")

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".py"):
            replace_in_file(os.path.join(root, file))
