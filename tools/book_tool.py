import os
from pathlib import Path

import pandas as pd
from tools.literacy_storage_tool import DYNAMIC_BOOKS_INVENTORY_PATH, get_books_inventory_path


def get_books_inventory_path():
    data_dir = Path(os.getenv("PAAI_DATA_DIR", "data"))
    return data_dir / "books_inventory.csv"


def load_book_library():
    books_path = get_books_inventory_path()

    if not books_path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(books_path)
    except Exception:
        return pd.DataFrame()


def get_book_library_summary():
    books_df = load_book_library()

    if books_df.empty:
        return {
            "has_books": False,
            "book_count": 0,
            "languages": [],
            "genres": [],
            "message": "No saved books found.",
        }

    languages = []
    genres = []

    if "Language" in books_df.columns:
        languages = sorted(
            books_df["Language"]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .unique()
            .tolist()
        )

    if "Genre" in books_df.columns:
        genres = sorted(
            books_df["Genre"]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .unique()
            .tolist()
        )

    return {
        "has_books": True,
        "book_count": len(books_df),
        "languages": languages,
        "genres": genres,
        "message": f"{len(books_df)} saved book(s) found.",
    }


def search_book_library(query):
    books_df = load_book_library()

    if books_df.empty:
        return {
            "query": query,
            "match_count": 0,
            "matches": [],
            "message": "No saved books found.",
        }

    query_text = str(query or "").strip().lower()

    if not query_text:
        return {
            "query": query,
            "match_count": 0,
            "matches": [],
            "message": "Please provide a book title, author, language, or genre to search.",
        }

    searchable_columns = [
        column for column in books_df.columns
        if column.lower() in [
            "title",
            "display title",
            "original title",
            "author",
            "language",
            "genre",
            "mood fit",
            "status",
        ]
    ]

    if not searchable_columns:
        searchable_columns = list(books_df.columns)

    mask = pd.Series(False, index=books_df.index)

    for column in searchable_columns:
        mask = mask | books_df[column].astype(str).str.lower().str.contains(query_text, na=False)

    matches_df = books_df[mask].head(20)

    matches = matches_df.fillna("").to_dict(orient="records")

    return {
        "query": query,
        "match_count": len(matches_df),
        "matches": matches,
        "message": f"Found {len(matches_df)} matching book(s).",
    }
