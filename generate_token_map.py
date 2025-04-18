#!/usr/bin/env python3

import os
import json
import argparse
import hashlib
import base64
from datetime import datetime
import re

MAP_FILE = "/etc/nginx/podcast_tokens.map"
BACKUP_DIR = "/etc/nginx/token_map_backups"


def slugify(text):
    return re.sub(r"[\W_]+", "-", text.strip().lower())


def generate_token_for_name(name, seed=None):
    raw = f"{seed}:{name}".encode("utf-8")
    h = hashlib.sha256(raw).digest()
    return base64.urlsafe_b64encode(h)[:16].decode("utf-8")


def create_token_map(archive_root, seed=None):
    token_map = {}
    for dir_name in sorted(os.listdir(archive_root)):
        dir_path = os.path.join(archive_root, dir_name)
        if os.path.isdir(dir_path):
            token = generate_token_for_name(dir_name, seed=seed)
            token_map[token] = dir_name
    return token_map


def write_token_map(token_map, output_path=MAP_FILE):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Backup old map
    if os.path.exists(output_path):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"podcast_tokens_{timestamp}.map")
        os.rename(output_path, backup_file)
        print(f"📦 Backed up previous map to {backup_file}")

    with open(output_path, "w") as f:
        for token, folder in token_map.items():
            f.write(f"{token} {folder};\n")

    print(f"✅ Wrote token map to {output_path}")


def write_reference_json(token_map, archive_root):
    ref_path = os.path.join(archive_root, "tokens.json")
    with open(ref_path, "w") as f:
        json.dump(token_map, f, indent=2)
    print(f"📘 Reference tokens.json written to: {ref_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate nginx token map for podcast access"
    )
    parser.add_argument(
        "--archive_dir",
        default="/srv/www/petit-pois/pods",
        help="Root directory of podcast folders",
    )
    parser.add_argument(
        "--map_file",
        default=MAP_FILE,
        help="Path to output nginx token map file",
    )
    parser.add_argument(
        "--seed",
        default=0,
        type=int,
        help="Optional seed for reproducible token generation (default: random)",
    )

    args = parser.parse_args()
    seed = args.seed

    token_map = create_token_map(args.archive_dir, seed=seed)
    write_token_map(token_map, args.map_file)
    write_reference_json(token_map, args.archive_dir)
