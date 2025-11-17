# remove .json entries that have less than 3 keys under "usernames"
import os
import json

def clean_json_folder(folder_path):
    for name in os.listdir(folder_path):
        if not name.lower().endswith(".json"):
            continue

        path = os.path.join(folder_path, name)

        try:
            with open(path, "r", encoding="utf8") as f:
                data = json.load(f)
        except Exception:
            continue

        usernames = data.get("usernames")
        if not isinstance(usernames, list) or len(usernames) < 3:
            try:
                os.remove(path)
                print(f"Deleted: {name}")
            except Exception as e:
                print(f"Failed to delete {name}: {e}")

if __name__ == "__main__":
    folder = input("Enter the path to the folder containing JSON files: ").strip()
    if os.path.isdir(folder):
        clean_json_folder(folder)
    else:
        print("Invalid folder path.")
