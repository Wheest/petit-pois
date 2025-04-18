import os
import json
import xml.etree.ElementTree as ET
from email.utils import formatdate
from datetime import datetime
import argparse
import re


def slugify(text):
    return re.sub(r"[\W_]+", "-", text.strip().lower())


def load_token_map(path):
    """
    Load an nginx-formatted map file like:
    abc123 Podcast_Name_One;
    xyz456 Podcast_Name_Two;
    """
    token_map = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and ";" in line:
                token, folder = line.rstrip(";").split(None, 1)
                token_map[token] = folder
    return token_map


def generate_rss_for_podcast(
    podcast_dir: str, podcast_title: str, base_url: str, token: str = None
):
    base_url = base_url.rstrip("/")
    podcast_basename = os.path.basename(podcast_dir)
    url_prefix = (
        f"{base_url}/secure/{token}" if token else f"{base_url}/pods/{podcast_basename}"
    )

    # Add iTunes and media namespaces
    rss = ET.Element(
        "rss",
        version="2.0",
        attrib={
            "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
            "xmlns:media": "http://search.yahoo.com/mrss/",
        },
    )
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = podcast_title
    ET.SubElement(channel, "link").text = f"{url_prefix}"
    ET.SubElement(channel, "description").text = f"Archived feed for {podcast_title}"
    ET.SubElement(channel, "language").text = "en"
    ET.SubElement(channel, "itunes:summary").text = f"Archived feed for {podcast_title}"
    ET.SubElement(channel, "itunes:author").text = "petit-pois"
    ET.SubElement(channel, "itunes:explicit").text = "no"

    owner = ET.SubElement(channel, "itunes:owner")
    ET.SubElement(owner, "itunes:name").text = "petit-pois"
    ET.SubElement(owner, "itunes:email").text = "noreply@example.com"

    # Podcast-level cover image (itunes, standard <image>, and media:thumbnail)
    image_url = None
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        image_path = os.path.join(podcast_dir, f"cover{ext}")
        if os.path.exists(image_path):
            image_url = f"{url_prefix}/cover{ext}"
            ET.SubElement(channel, "itunes:image", href=image_url)

            # RSS 2.0 <image>
            image_tag = ET.SubElement(channel, "image")
            ET.SubElement(image_tag, "url").text = image_url
            ET.SubElement(image_tag, "title").text = podcast_title
            ET.SubElement(image_tag, "link").text = url_prefix

            # media:thumbnail
            ET.SubElement(channel, "media:thumbnail", url=image_url)
            break

    episodes = sorted(
        [f for f in os.listdir(podcast_dir) if f.endswith(".json")], reverse=True
    )

    for json_file in episodes:
        json_path = os.path.join(podcast_dir, json_file)
        with open(json_path) as f:
            entry = json.load(f)

        base_name = os.path.splitext(json_file)[0]
        audio_file = entry.get("filename") or next(
            (
                f
                for f in os.listdir(podcast_dir)
                if f.startswith(base_name) and not f.endswith(".json")
            ),
            None,
        )
        if not audio_file:
            continue

        title = entry.get("title", "Untitled Episode")
        pub_date = entry.get("published_parsed")
        pub_date_str = (
            formatdate(datetime(*pub_date[:6]).timestamp())
            if pub_date
            else formatdate()
        )
        description = entry.get("summary") or entry.get("content", [{}])[0].get(
            "value", ""
        )
        subtitle = entry.get("subtitle", "")
        duration = entry.get("itunes_duration", "")
        itunes_title = entry.get("itunes_title", title)
        guid = entry.get("id", audio_file)
        author = entry.get("author", "")

        audio_path = os.path.join(podcast_dir, audio_file)
        file_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
        if not file_size:
            file_size = int(entry.get("links", [{}])[0].get("length", 0))

        audio_url = f"{url_prefix}/{audio_file}"

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = audio_url
        ET.SubElement(
            item, "enclosure", url=audio_url, type="audio/mpeg", length=str(file_size)
        )
        ET.SubElement(item, "pubDate").text = pub_date_str
        ET.SubElement(item, "guid").text = guid

        if description:
            ET.SubElement(item, "description").text = description
        if author:
            ET.SubElement(item, "author").text = author
        if subtitle:
            ET.SubElement(item, "itunes:subtitle").text = subtitle
        if itunes_title:
            ET.SubElement(item, "itunes:title").text = itunes_title
        if duration:
            ET.SubElement(item, "itunes:duration").text = str(duration)

        # Episode-level image
        image_filename = entry.get("image_filename")
        if image_filename:
            episode_img_url = f"{url_prefix}/{image_filename}"
            ET.SubElement(item, "itunes:image", href=episode_img_url)
            ET.SubElement(item, "media:thumbnail", url=episode_img_url)

    rss_path = os.path.join(podcast_dir, "archive.xml")
    tree = ET.ElementTree(rss)
    tree.write(rss_path, encoding="utf-8", xml_declaration=True)
    print(f"✅ Generated RSS: {rss_path}")


def generate_all_feeds(archive_root: str, base_url: str, map_file: str = None):
    token_map = load_token_map(map_file) if map_file else {}
    for dir_name in os.listdir(archive_root):
        dir_path = os.path.join(archive_root, dir_name)
        if os.path.isdir(dir_path):
            token = next(
                (t for t, folder in token_map.items() if folder == dir_name), None
            )
            if not token:
                print(f"⚠️ No token found for {dir_name}.")
            title = dir_name.replace("_", " ")
            generate_rss_for_podcast(dir_path, title, base_url, token)


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
    parser.add_argument(
        "--map_file",
        help="Optional path to token map (JSON format). Enables secure token-based URLs.",
    )

    args = parser.parse_args()
    generate_all_feeds(args.archive_dir, args.base_url, args.map_file)
