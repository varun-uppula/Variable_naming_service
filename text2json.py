import json

# Read the text file
with open("mapping.txt", "r") as f:
    lines = f.readlines()

mapping_dict = {}
for line in lines:
    if line.strip():
        parts = line.split()
        key = parts[0].strip()
        value = parts[-1].strip()
        mapping_dict[key] = value
        if(len(value)==1):
            print(key)

# Save to JSON
with open("mapping.json", "w") as f:
    json.dump(mapping_dict, f, indent=4)

print("✅ JSON file created: mapping.json")
