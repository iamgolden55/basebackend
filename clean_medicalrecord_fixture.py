import json

INPUT_FILE = 'data_backup.json'
OUTPUT_FILE = 'data_backup_cleaned.json'

with open(INPUT_FILE, 'r') as f:
    data = json.load(f)

seen_user_ids = set()
cleaned = []

for obj in data:
    if obj.get('model') == 'api.medicalrecord':
        user_id = obj['fields'].get('user')
        if user_id in seen_user_ids:
            continue  # skip duplicate
        seen_user_ids.add(user_id)
    cleaned.append(obj)

with open(OUTPUT_FILE, 'w') as f:
    json.dump(cleaned, f, indent=2)

print(f"Cleaned fixture written to {OUTPUT_FILE}. {len(data) - len(cleaned)} duplicates removed.") 