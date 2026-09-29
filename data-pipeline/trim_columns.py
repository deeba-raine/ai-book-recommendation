import pandas as pd

df = pd.read_json(
    "raw/goodreads_books_young_adult.json",
    lines=True,
    dtype=False,
)

keep = [
    "book_id", "work_id", "title", "title_without_series", "description",
    "isbn", "isbn13", "average_rating", "ratings_count", "publication_year",
    "image_url", "url", "authors", "popular_shelves", "similar_books",
]

df = df[keep]

df.to_json("data-pipeline/output/books_trimmed.jsonl", orient="records", lines=True)
print(df.shape)