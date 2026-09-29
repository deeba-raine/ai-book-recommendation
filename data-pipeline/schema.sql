CREATE TABLE authors (
    author_id  INTEGER PRIMARY KEY,
    name       TEXT NOT NULL
);

CREATE TABLE books (
    book_id         INTEGER PRIMARY KEY,
    title           TEXT NOT NULL,
    author_id       INTEGER NOT NULL REFERENCES authors(author_id),
    description     TEXT NOT NULL,
    average_rating  NUMERIC(3,2),
    ratings_count   INTEGER,
    image_url       TEXT,
    goodreads_url   TEXT
);

CREATE TABLE genres (
    genre_id  SERIAL PRIMARY KEY,
    name      TEXT UNIQUE NOT NULL
);

-- many-to-many: a book has several genres, a genre has many books
CREATE TABLE book_genres (
    book_id   INTEGER REFERENCES books(book_id) ON DELETE CASCADE,
    genre_id  INTEGER REFERENCES genres(genre_id),
    PRIMARY KEY (book_id, genre_id)
);

-- Goodreads "readers also liked" links, used as a recommendation signal
CREATE TABLE similar_books (
    book_id          INTEGER REFERENCES books(book_id) ON DELETE CASCADE,
    similar_book_id  INTEGER REFERENCES books(book_id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, similar_book_id)
);

CREATE INDEX idx_books_author ON books(author_id);
CREATE INDEX idx_book_genres_genre ON book_genres(genre_id);