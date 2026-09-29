import json
import re
from collections import Counter
from pathlib import Path

folder = Path(__file__).parent
AUTHORS_FILE = folder / "raw" / "goodreads_book_authors.json"
INPUT_FILE = folder / "output" / "books_trimmed.jsonl"
OUTPUT_FILE = folder / "output" / "books_clean.jsonl"

MIN_DESCRIPTION_LENGTH = 50
MIN_RATINGS = 10

# shelf name -> genre (anything not listed here is ignored)
GENRE_MAP = {
    "fantasy": "fantasy", "urban-fantasy": "fantasy", "romance": "romance",
    "paranormal": "paranormal", "supernatural": "paranormal",
    "sci-fi": "science-fiction", "science-fiction": "science-fiction",
    "dystopia": "dystopian", "dystopian": "dystopian", "mystery": "mystery",
    "thriller": "thriller", "horror": "horror", "contemporary": "contemporary",
    "historical-fiction": "historical-fiction", "adventure": "adventure",
    "humor": "humor", "mythology": "mythology", "retellings": "retellings",
    "fairy-tales": "fairy-tales", "lgbt": "lgbt",
}

# common English words, used to tell English text from other languages
ENGLISH_WORDS = set(
    "the and of to a in is that it was for on with as his her he she they but be at by "
    "this from are an or not you i my all when who".split()
)

# titles that are bundles, not single books
BOX_SET_PATTERN = re.compile(
    r"box(ed)?\s*set|omnibus|collection|bundle|complete (series|saga|trilogy)"
    r"|#\s*\d+\s*[-–]\s*\d+|books?\s*\d+\s*[-–]\s*\d+",
    re.IGNORECASE,
)

removed = Counter()   # how many books each rule removed


def clean_text(text):
    """Remove HTML tags and extra whitespace."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def looks_english(text):
    """Reject text with many accented letters or few common English words."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    non_ascii = sum(1 for c in letters if ord(c) > 127)
    if non_ascii / len(letters) > 0.1:
        return False
    words = re.findall(r"[a-z']+", text.lower())
    if len(words) < 5:
        return False
    english = sum(1 for w in words if w in ENGLISH_WORDS)
    return english / len(words) >= 0.2


def looks_like_real_author(name):
    """Reject usernames like '@ID_AyahASI' or '27' (digits, @, underscores)."""
    return len(name) >= 3 and not re.search(r"[@_\d]", name)


def pick_author(authors):
    """Prefer the entry with no special role (skips translators, editors)."""
    if not authors:
        return None
    main = [a for a in authors if a["role"] == ""]
    return (main or authors)[0]


def get_genres(shelves):
    """Sum shelf counts per genre and keep the top 5."""
    totals = Counter()
    for shelf in shelves or []:
        genre = GENRE_MAP.get(shelf["name"])
        if genre:
            totals[genre] += int(shelf["count"])
    return [genre for genre, _ in totals.most_common(5)]


def normalize_title(title):
    """'Back in Black (A-List, #5)' -> 'backinblack'"""
    title = re.sub(r"\(.*?\)", "", title).lower()
    return re.sub(r"[^a-z0-9]", "", title)


def keep_best(records, key_fn, redirect, reason):
    """Among records with the same key, keep the one with the most ratings."""
    best = {}
    for record in records:
        key = key_fn(record)
        if key not in best:
            best[key] = record
            continue
        current = best[key]
        if record["ratings_count"] > current["ratings_count"]:
            winner, loser = record, current
        else:
            winner, loser = current, record
        best[key] = winner
        redirect[loser["book_id"]] = winner["book_id"]   # remember where it went
        removed[reason] += 1
    return list(best.values())


def resolve(book_id, redirect):
    """Follow a removed book to the edition we kept."""
    while book_id in redirect:
        book_id = redirect[book_id]
    return book_id


# Step 1: author id -> author name
author_names = {}
with open(AUTHORS_FILE, encoding="utf-8") as f:
    for line in f:
        author = json.loads(line)
        author_names[author["author_id"]] = author["name"]

# Step 2: clean each book and drop the ones that fail a rule
records = []
total = 0
with open(INPUT_FILE, encoding="utf-8") as f:
    for line in f:
        book = json.loads(line)
        total += 1

        title = clean_text(book["title"])
        description = clean_text(book["description"])
        ratings = int(book["ratings_count"] or 0)

        if not title or len(description) < MIN_DESCRIPTION_LENGTH:
            removed["weak description"] += 1
            continue
        if ratings < MIN_RATINGS:
            removed["too few ratings"] += 1
            continue
        if BOX_SET_PATTERN.search(title):
            removed["box set or collection"] += 1
            continue
        if not looks_english(description):
            removed["not English"] += 1
            continue

        author = pick_author(book["authors"])
        name = author_names.get(author["author_id"]) if author else None
        if not name:
            removed["no author"] += 1
            continue
        if not looks_like_real_author(name):
            removed["username-style author"] += 1
            continue

        image = book["image_url"] or ""
        records.append({
            "book_id": int(book["book_id"]),
            "work_id": book["work_id"] or book["book_id"],
            "title": title,
            "author_id": author["author_id"],
            "author_name": name,
            "description": description,
            "average_rating": float(book["average_rating"]),
            "ratings_count": ratings,
            "image_url": None if (not image or "nophoto" in image) else image,
            "genres": get_genres(book["popular_shelves"]),
            "similar_books": [int(b) for b in book["similar_books"]],
            "goodreads_url": book["url"],
        })

# Step 3: remove duplicate editions (two rules)
redirect = {}
records = keep_best(records, lambda r: r["work_id"], redirect, "duplicate (same work)")
records = keep_best(
    records,
    lambda r: (r["author_id"], normalize_title(r["title"])),
    redirect,
    "duplicate (same author and title)",
)

# Step 4: similar_books should only point to books that still exist
kept_ids = {r["book_id"] for r in records}
for r in records:
    similar = {resolve(b, redirect) for b in r["similar_books"]}
    r["similar_books"] = sorted(b for b in similar if b in kept_ids and b != r["book_id"])
    del r["work_id"]

# Step 5: save
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"Read {total} books, kept {len(records)}. Removed:")
for reason, count in removed.most_common():
    print(f"  {reason}: {count}")