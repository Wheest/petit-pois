import os
import json
import xml.etree.ElementTree as ET
from email.utils import formatdate
from datetime import datetime
import argparse


def slugify(text):
    import re

    return re.sub(r"[\W_]+", "-", text.strip().lower())


def generate_rss_for_podcast(podcast_dir: str, podcast_title: str, base_url: str):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = podcast_title
    ET.SubElement(channel, "link").text = f"{base_url}/{os.path.basename(podcast_dir)}"
    ET.SubElement(channel, "description").text = f"Archived feed for {podcast_title}"

    episodes = sorted(
        [f for f in os.listdir(podcast_dir) if f.endswith(".json")], reverse=True
    )

    for json_file in episodes:
        json_path = os.path.join(podcast_dir, json_file)
        with open(json_path) as f:
            entry = json.load(f)

        title = entry.get("title", "Untitled Episode")
        pub_date = entry.get("published_parsed")
        if pub_date:
            pub_date_str = formatdate(datetime(*pub_date[:6]).timestamp())
        else:
            pub_date_str = formatdate()

        # Find matching audio file
        base_name = os.path.splitext(json_file)[0]
        audio_file = next(
            (
                f
                for f in os.listdir(podcast_dir)
                if f.startswith(base_name) and not f.endswith(".json")
            ),
            None,
        )
        if not audio_file:
            continue  # Skip if audio is missing

        audio_url = f"{base_url}/{os.path.basename(podcast_dir)}/{audio_file}"

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = audio_url
        ET.SubElement(item, "enclosure", url=audio_url, type="audio/mpeg")
        ET.SubElement(item, "pubDate").text = pub_date_str

    # Save RSS file
    rss_path = os.path.join(podcast_dir, "archive.xml")
    tree = ET.ElementTree(rss)
    tree.write(rss_path, encoding="utf-8", xml_declaration=True)
    print(f"✅ Generated RSS: {rss_path}")


def generate_all_feeds(archive_root: str, base_url: str):
    for dir_name in os.listdir(archive_root):
        dir_path = os.path.join(archive_root, dir_name)
        if os.path.isdir(dir_path):
            title = dir_name.replace("_", " ")
            generate_rss_for_podcast(dir_path, title, base_url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate RSS feeds from archived podcast metadata."
    )
    parser.add_argument(
        "--archive_dir",
        default="pods",
        help="Root directory where podcast archives are stored.",
    )
    parser.add_argument(
        "--base_url", required=True, help="Public base URL for serving audio files."
    )

    args = parser.parse_args()
    generate_all_feeds(args.archive_dir, args.base_url)
