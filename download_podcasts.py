import os
import json
import requests
import feedparser
import argparse
from tqdm import tqdm
import re


def slugify(text):
    return re.sub(r"[\W_]+", "-", text.strip().lower())


def download_single_feed(feed_url: str, archive_dir: str, podcast_name: str):
    safe_name = podcast_name.replace(" ", "_")
    podcast_dir = os.path.join(archive_dir, safe_name)
    os.makedirs(podcast_dir, exist_ok=True)

    feed = feedparser.parse(feed_url)
    if not feed.entries:
        print(f"⚠️ No entries found in feed: {feed_url}")
        return

    for entry in tqdm(feed.entries, desc=f"  {podcast_name}", unit="episode"):
        try:
            audio_url = entry.enclosures[0].href
            ext = os.path.splitext(audio_url.split("?")[0])[1] or ".mp3"

            # Date
            pub_date = entry.get("published_parsed")
            if pub_date:
                date_str = f"{pub_date.tm_year:04d}-{pub_date.tm_mon:02d}-{pub_date.tm_mday:02d}"
            else:
                date_str = "undated"

            # Safe title
            raw_title = entry.get("title", "untitled")
            safe_title = slugify(raw_title)

            filename_base = f"{date_str}-{safe_title}"
            audio_path = os.path.join(podcast_dir, filename_base + ext)
            metadata_path = os.path.join(podcast_dir, filename_base + ".json")

            if os.path.exists(audio_path) and os.path.exists(metadata_path):
                continue

            # Download audio
            if not os.path.exists(audio_path):
                r = requests.get(audio_url, stream=True)
                r.raise_for_status()
                with open(audio_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            # Save metadata
            with open(metadata_path, "w") as f:
                json.dump(entry, f, indent=2)

        except Exception as e:
            print(f"⚠️ Error downloading episode from {audio_url}: {e}")


def download_all_feeds(jsonl_path: str, archive_root: str = "pods"):
    """
    Reads a JSONL file with feed URLs and names, and downloads all podcasts.

    :param jsonl_path: Path to the JSONL file containing feeds.
    :param archive_root: Root directory to store all podcasts.
    """
    os.makedirs(archive_root, exist_ok=True)

    with open(jsonl_path, "r") as f:
        feeds = [json.loads(line) for line in f if line.strip()]

    for feed in tqdm(feeds, desc="Downloading feeds", unit="feed"):
        try:
            download_single_feed(feed["url"], archive_root, feed["name"])
        except Exception as e:
            print(f"⚠️ Failed to process feed {feed['name']}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Archive multiple podcast feeds from a JSONL file."
    )
    parser.add_argument(
        "--feeds_file",
        default="feeds.jsonl",
        help="Path to feeds.jsonl containing podcast feed URLs and names.",
    )
    parser.add_argument(
        "--archive_dir",
        default="pods",
        help="Root directory to store archives (default: pods)",
    )

    args = parser.parse_args()
    download_all_feeds(args.feeds_file, args.archive_dir)
