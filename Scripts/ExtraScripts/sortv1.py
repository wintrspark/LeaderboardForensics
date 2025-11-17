#!/usr/bin/env python3
import os
import sys
import json
from collections import defaultdict

def prompt_nonempty(prompt_text):
    while True:
        v = input(prompt_text).strip()
        if v:
            return v

def prompt_int(prompt_text, default):
    v = input(f"{prompt_text} [{default}]: ").strip()
    if not v:
        return default
    try:
        n = int(v)
        if n <= 0:
            raise ValueError
        return n
    except Exception:
        print("Invalid number. Using default", default)
        return default

def get_rank_by_path(obj, path):
    if obj is None:
        return None
    if not path:
        return None
    parts = path.split(".")
    cur = obj
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur

def open_writer(path, mode):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    f = open(path, "w", encoding="utf-8")
    if mode == "array":
        f.write("[")
    else:
        f.write("{")
    return f

def write_item_array(f, first, obj):
    if not first:
        f.write(",\n")
    f.write(json.dumps(obj, ensure_ascii=False))
    return False

def write_item_object(f, first, key, obj):
    if not first:
        f.write(",\n")
    f.write(json.dumps(key, ensure_ascii=False))
    f.write(":")
    f.write(json.dumps(obj, ensure_ascii=False))
    return False

def close_writer(f, mode):
    if mode == "array":
        f.write("]\n")
    else:
        f.write("}\n")
    f.close()

def detect_top_level(fp):
    pos = fp.tell()
    while True:
        b = fp.read(1)
        if not b:
            fp.seek(pos)
            return None
        if b.isspace():
            continue
        fp.seek(pos)
        first = fp.read(1)
        fp.seek(pos)
        if first == "[":
            return "array"
        if first == "{":
            return "object"
        return None

def stream_with_ijson_array(fp):
    import ijson
    for item in ijson.items(fp, "item"):
        yield item

def stream_with_ijson_object(fp):
    import ijson
    for key, val in ijson.kvitems(fp, ""):
        yield key, val

def read_json_value_from_text(fp):
    buf = []
    in_str = False
    escape = False
    depth = 0
    first = fp.read(1)
    if not first:
        return None
    buf.append(first)
    if first == '"' :
        in_str = True
    elif first in '{[':
        depth = 1
    else:
        # primitives (number, true, false, null)
        while True:
            c = fp.read(1)
            if not c or c in ',]\}\n\r\t ':
                break
            buf.append(c)
        return "".join(buf)
    while True:
        c = fp.read(1)
        if not c:
            break
        buf.append(c)
        if in_str:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_str = False
                if depth == 0:
                    break
        else:
            if c == '"' :
                in_str = True
            elif c in '{[':
                depth += 1
            elif c in '}]':
                depth -= 1
                if depth == 0:
                    break
    return "".join(buf)

def stream_array_by_balanced(fp_text):
    while True:
        c = fp_text.read(1)
        if not c:
            return
        if c.isspace():
            continue
        if c == '[':
            break
        else:
            return
    first_item = True
    while True:
        while True:
            c = fp_text.read(1)
            if not c:
                return
            if not c.isspace():
                break
        if c == ']':
            return
        fp_text.seek(fp_text.tell() - 1)
        val_text = read_json_value_from_text(fp_text)
        if val_text is None:
            return
        try:
            obj = json.loads(val_text)
        except Exception:
            raise
        yield obj
        while True:
            c = fp_text.read(1)
            if not c:
                return
            if c.isspace():
                continue
            if c == ',':
                break
            if c == ']':
                return
            fp_text.seek(fp_text.tell() - 1)
            break

def main():
    input_path = prompt_nonempty("Path to JSON: ")
    if not os.path.isfile(input_path):
        print("File not found:", input_path)
        return
    chunk = prompt_int("chunk (items per folder)", 1000)
    out_base = input("Output base directory [out]: ").strip() or "out"
    rank_path = input("Rank field path (dot notation) [rank]: ").strip() or "rank"

    writers = {}
    first_flags = {}
    writers_mode = {}
    counts = defaultdict(int)
    total = 0
    no_rank_key = "no_rank"

    try:
        with open(input_path, "rb") as fp_bin:
            tl = detect_top_level(fp_bin)
            use_ijson = True
            try:
                if tl == "array":
                    gen = stream_with_ijson_array(fp_bin)
                elif tl == "object":
                    gen = stream_with_ijson_object(fp_bin)
                else:
                    use_ijson = False
            except Exception:
                use_ijson = False

            if use_ijson:
                if tl == "array":
                    for obj in gen:
                        total += 1
                        rank_val = get_rank_by_path(obj, rank_path) if isinstance(obj, dict) else None
                        try:
                            r = int(rank_val)
                            if r <= 0:
                                group = None
                            else:
                                group = (r - 1) // chunk + 1
                        except Exception:
                            group = None
                        key = str(group) if group is not None else no_rank_key
                        if key not in writers:
                            folder = os.path.join(out_base, key)
                            path = os.path.join(folder, "data.json")
                            f = open_writer(path, "array")
                            writers[key] = f
                            first_flags[key] = True
                            writers_mode[key] = "array"
                        f = writers[key]
                        first = first_flags[key]
                        first = write_item_array(f, first, obj)
                        first_flags[key] = first
                        counts[key] += 1
                else:
                    for k, obj in gen:
                        total += 1
                        rank_val = get_rank_by_path(obj, rank_path) if isinstance(obj, dict) else None
                        try:
                            r = int(rank_val)
                            if r <= 0:
                                group = None
                            else:
                                group = (r - 1) // chunk + 1
                        except Exception:
                            group = None
                        key = str(group) if group is not None else no_rank_key
                        if key not in writers:
                            folder = os.path.join(out_base, key)
                            path = os.path.join(folder, "data.json")
                            f = open_writer(path, "object")
                            writers[key] = f
                            first_flags[key] = True
                            writers_mode[key] = "object"
                        f = writers[key]
                        first = first_flags[key]
                        first = write_item_object(f, first, k, obj)
                        first_flags[key] = first
                        counts[key] += 1
            else:
                with open(input_path, "r", encoding="utf-8") as fp_text:
                    tl = detect_top_level(fp_text)
                    if tl == "array":
                        for obj in stream_array_by_balanced(fp_text):
                            total += 1
                            rank_val = get_rank_by_path(obj, rank_path) if isinstance(obj, dict) else None
                            try:
                                r = int(rank_val)
                                if r <= 0:
                                    group = None
                                else:
                                    group = (r - 1) // chunk + 1
                            except Exception:
                                group = None
                            key = str(group) if group is not None else no_rank_key
                            if key not in writers:
                                folder = os.path.join(out_base, key)
                                path = os.path.join(folder, "data.json")
                                f = open_writer(path, "array")
                                writers[key] = f
                                first_flags[key] = True
                                writers_mode[key] = "array"
                            f = writers[key]
                            first = first_flags[key]
                            first = write_item_array(f, first, obj)
                            first_flags[key] = first
                            counts[key] += 1
                    else:
                        print("Top-level object detected and ijson is unavailable. Attempting full load. If the file is huge this may fail.")
                        fp_text.seek(0)
                        data = json.load(fp_text)
                        if isinstance(data, dict):
                            iterator = iter(data.items())
                            for k, obj in iterator:
                                total += 1
                                rank_val = get_rank_by_path(obj, rank_path) if isinstance(obj, dict) else None
                                try:
                                    r = int(rank_val)
                                    if r <= 0:
                                        group = None
                                    else:
                                        group = (r - 1) // chunk + 1
                                except Exception:
                                    group = None
                                key = str(group) if group is not None else no_rank_key
                                if key not in writers:
                                    folder = os.path.join(out_base, key)
                                    path = os.path.join(folder, "data.json")
                                    f = open_writer(path, "object")
                                    writers[key] = f
                                    first_flags[key] = True
                                    writers_mode[key] = "object"
                                f = writers[key]
                                first = first_flags[key]
                                first = write_item_object(f, first, k, obj)
                                first_flags[key] = first
                                counts[key] += 1
                        else:
                            print("Unsupported top-level JSON type.")
                            return

    finally:
        for k, f in list(writers.items()):
            try:
                mode = writers_mode.get(k, "array")
                close_writer(f, mode)
            except Exception:
                try:
                    f.close()
                except Exception:
                    pass

    print("Processed", total, "objects")
    for k in sorted(counts, key=lambda x: (x == no_rank_key, int(x) if x.isdigit() else float('inf'))):
        print(f"Folder '{k}': {counts[k]} objects")
    print("Output base directory:", os.path.abspath(out_base))

if __name__ == "__main__":
    main()
