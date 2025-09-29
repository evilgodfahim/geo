import feedparser
import hashlib
import os
from datetime import datetime
import xml.etree.ElementTree as ET

# ✅ 9 feeds to combine
FEEDS = [
    "https://www.atlanticcouncil.org/feed/",
    "https://www.lowyinstitute.org/the-interpreter/rss.xml",
    "https://politepol.com/fd/BzFhFtawKQrt.xml",
    "https://politepol.com/fd/R39To2fYhqqO.xml",
    "https://asiatimes.com/feed/",
    "https://foreignpolicy.com/feed/",
    "https://thediplomat.com/feed/",
    "https://warontherocks.com/feed/",
    "https://www.foreignaffairs.com/rss.xml",
    "https://original.antiwar.com/feed/",
    "https://rss.diffbot.com/rss?url=https://www.csis.org/analysis?f%255B0%255D%3Dcontent_type%253Areport",
    "https://www.worldpoliticsreview.com/feed/"
]

OUTPUT_FILE = "combined.xml"
INDEX_FILE = "index.txt"
MAX_ARTICLES = 200  # keep last 500

def get_id(entry):
    """Generate unique ID for each entry"""
    base = entry.get("id") or entry.get("link") or entry.get("title", "")
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

def load_seen():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()

def save_seen(seen):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        for item in seen:
            f.write(item + "\n")

def main():
    seen = load_seen()
    new_articles = []

    print(f"Processing {len(FEEDS)} feeds...")

    for feed in FEEDS:
        parsed = feedparser.parse(feed)
        for entry in parsed.entries:
            uid = get_id(entry)
            if uid not in seen:
                seen.add(uid)
                new_articles.append((entry, uid))

    # Sort newest first
    def sort_key(item):
        entry = item[0]
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        return datetime.now()
    new_articles.sort(key=sort_key, reverse=True)

    # Trim to max limit
    all_articles = new_articles[:MAX_ARTICLES]

    # Save updated seen list (only keep latest 500)
    save_seen(set(uid for _, uid in all_articles))

    # Build RSS XML
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Combined Feed"
    ET.SubElement(channel, "link").text = "https://yourusername.github.io/combined.xml"
    ET.SubElement(channel, "description").text = "Aggregated feed without duplicates"
    ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    for entry, uid in all_articles:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = entry.get("title", "No title")
        ET.SubElement(item, "link").text = entry.get("link", "")
        ET.SubElement(item, "guid").text = uid
        ET.SubElement(item, "description").text = entry.get("summary", "")
        pub_date = entry.get("published", datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"))
        ET.SubElement(item, "pubDate").text = pub_date

    tree = ET.ElementTree(rss)
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    main()
