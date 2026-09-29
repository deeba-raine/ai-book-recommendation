import json
from pathlib import Path

folder = Path(__file__).parent

GENRES = {"fantasy", "romance", "paranormal", "science-fiction", "dystopian",
          "mystery", "thriller", "horror", "contemporary", "historical-fiction"}

# Step 1: build a lookup of author id -> author name
author_names = {}
for line in open(folder / "raw" / "goodreads_book_authors.json", encoding="utf-8"):
    author = json.loads(line)
    author_names[author["author_id"]] = author["name"]

# Step 2: clean each book and save it
out = open(folder / "output" / "books_clean.jsonl", "w", encoding="utf-8")
kept = 0

for line in open(folder / "output" / "books_trimmed.jsonl", encoding="utf-8"):
    book = json.loads(line)

    # drop books with a weak description or too few ratings
    if len(book["description"] or "") < 50 or int(book["ratings_count"] or 0) < 10:
        continue

    # replace the author id with the author's name
    author_id = book["authors"][0]["author_id"]
    if author_id not in author_names:
        continue

    # keep only real genres from the shelves (top 5)
    genres = [s["name"] for s in book["popular_shelves"] if s["name"] in GENRES][:5]

    # skip the placeholder cover
    image = None if "nophoto" in book["image_url"] else book["image_url"]

    clean = {
        "book_id": int(book["book_id"]),
        "title": book["title"],
        "author_name": author_names[author_id],
        "description": book["description"],
        "average_rating": float(book["average_rating"]),
        "image_url": image,
        "genres": genres,
        "goodreads_url": book["url"],
    }
    out.write(json.dumps(clean) + "\n")
    kept += 1

out.close()
print("Kept", kept, "books")