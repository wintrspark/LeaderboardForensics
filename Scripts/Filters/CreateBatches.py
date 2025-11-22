#!/usr/bin/env python3
import os
import json
import re
from collections import OrderedDict
from pathlib import Path

def leading_int(name):
    m = re.match(r'\s*?(\d+)', name)
    return int(m.group(1)) if m else 10**12

def find_json_file(folder: Path):
    for item in sorted(folder.iterdir()):
        if item.is_file() and item.suffix.lower() == '.json':
            return item
    return None

def load_json(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)

def sort_by_rank(items):
    def rank_of(kv):
        v = kv[1]
        try:
            return int(v.get('latest', {}).get('rank', 10**12))
        except Exception:
            return 10**12
    return sorted(items, key=rank_of)

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p

def main():
    root = input("Enter path to data folders root: ").strip()
    if not root:
        print("No path provided. Exiting.")
        return
    rootp = Path(root).expanduser().resolve()
    if not rootp.exists() or not rootp.is_dir():
        print("Provided path does not exist or is not a directory.")
        return

    subdirs = [d for d in sorted(rootp.iterdir(), key=lambda p: leading_int(p.name)) if d.is_dir()]
    if not subdirs:
        print("No subfolders found in the provided directory.")
        return

    script_dir = Path(__file__).resolve().parent
    out_root = ensure_dir(script_dir.joinpath('OUT'))

    batch_index = 1
    for i in range(0, len(subdirs), 3):
        group = subdirs[i:i+3]
        if not group:
            break

        batch_dir = ensure_dir(out_root.joinpath(f"batch_{batch_index}"))
        merged = {}
        missing = []
        for folder in group:
            jf = find_json_file(folder)
            if not jf:
                missing.append(folder.name)
                continue
            try:
                data = load_json(jf)
            except Exception as e:
                print(f"Failed to load JSON {jf}: {e}")
                missing.append(folder.name)
                continue
            for k, v in data.items():
                if k in merged:
                    continue
                merged[k] = v

        items = sort_by_rank(list(merged.items()))
        ordered = OrderedDict(items)

        out_file = batch_dir.joinpath("combined.json")
        try:
            with out_file.open('w', encoding='utf-8') as f:
                json.dump(ordered, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to write {out_file}: {e}")
            return

        print(f"Batch {batch_index}: merged {len(ordered)} records from folders {[p.name for p in group]} -> {out_file}")
        if missing:
            print(f"  Note: missing or unreadable JSON in {missing}")
        batch_index += 1

    print("Done. OUT directory:", str(out_root))

if __name__ == '__main__':
    main()
