import json
from pathlib import Path

BASE = Path(__file__).parent          # the data-pipeline folder
src = BASE / "raw" / "goodreads_books_young_adult.json"
out_dir = BASE / "output"
out_dir.mkdir(exist_ok=True)
dest = out_dir / "books_trimmed.jsonl"

keep = [
    "book_id", "work_id", "title", "title_without_series", "description",
    "isbn", "isbn13", "average_rating", "ratings_count", "publication_year",
    "image_url", "url", "authors", "popular_shelves", "similar_books",
]

total = 0
with open(src, encoding="utf-8") as fin, open(dest, "w", encoding="utf-8") as fout:
    for line in fin:
        if not line.strip():
            continue
        book = json.loads(line)
        slim = {k: book.get(k) for k in keep}
        fout.write(json.dumps(slim, ensure_ascii=False) + "\n")
        total += 1
        if total % 10000 == 0:
            print(f"{total} books written")

print("Done:", total, "->", dest)