#!/usr/bin/env python3

import os
import json
import argparse
import secrets
from datetime import datetime

MAP_FILE = "/etc/nginx/podcast_tokens.map"
BACKUP_DIR = "/etc/nginx/token_map_backups"


def slugify(text):
    import re
    return re.sub(r"[\W_]+", "-", text.strip().lower())


def generate_token():
    return secrets.token_urlsafe(12)


def create_token_map(archive_root):
    token_map = {}
    for dir_name in sorted(os.listdir(archive_root)):
        dir_path = os.path.join(archive_root, dir_name)
        if os.path.isdir(dir_path):
            token = generate_token()
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
        f.write("# token\t\tpodcast_folder\n")
        for token, folder in token_map.items():
            f.write(f"{token}\t{folder}\n")
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
    args = parser.parse_args()

    token_map = create_token_map(args.archive_dir)
    write_token_map(token_map, args.map_file)
    write_reference_json(token_map, args.archive_dir)
