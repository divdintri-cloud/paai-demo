import requests


def search_google_books(title, author=""):
    query = title

    if author and author != "Unclear":
        query = f"{title} {author}"

    url = "https://www.googleapis.com/books/v1/volumes"

    params = {
        "q": query,
        "maxResults": 1,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        items = data.get("items", [])

        if not items:
            return {}

        volume_info = items[0].get("volumeInfo", {})

        return {
            "metadata_source": "Google Books",
            "title": volume_info.get("title", title),
            "authors": ", ".join(volume_info.get("authors", [])),
            "description": volume_info.get("description", ""),
            "categories": ", ".join(volume_info.get("categories", [])),
            "preview_link": volume_info.get("previewLink", ""),
            "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail", ""),
        }

    except Exception as error:
        return {
            "metadata_source": "Google Books",
            "error": str(error),
        }


def search_open_library(title, author=""):
    query = title

    if author and author != "Unclear":
        query = f"{title} {author}"

    url = "https://openlibrary.org/search.json"

    params = {
        "q": query,
        "limit": 1,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        docs = data.get("docs", [])

        if not docs:
            return {}

        book = docs[0]

        authors = book.get("author_name", [])
        subjects = book.get("subject", [])

        return {
            "metadata_source": "Open Library",
            "title": book.get("title", title),
            "authors": ", ".join(authors[:3]),
            "description": "",
            "categories": ", ".join(subjects[:5]),
            "preview_link": f"https://openlibrary.org{book.get('key', '')}" if book.get("key") else "",
            "thumbnail": f"https://covers.openlibrary.org/b/id/{book.get('cover_i')}-M.jpg" if book.get("cover_i") else "",
        }

    except Exception as error:
        return {
            "metadata_source": "Open Library",
            "error": str(error),
        }


def enrich_book_metadata(title, author=""):
    google_result = search_google_books(title, author)

    if google_result and not google_result.get("error"):
        return google_result

    open_library_result = search_open_library(title, author)

    if open_library_result and not open_library_result.get("error"):
        return open_library_result

    return {
        "metadata_source": "Not found",
        "title": title,
        "authors": author,
        "description": "",
        "categories": "",
        "preview_link": "",
        "thumbnail": "",
    }


def enrich_books_inventory(books):
    enriched_books = []

    for book in books:
        title = book.get("Title", "")
        author = book.get("Author", "")

        metadata = enrich_book_metadata(title, author)

        enriched_book = {
            **book,
            "Metadata Source": metadata.get("metadata_source", ""),
            "Online Title": metadata.get("title", ""),
            "Online Authors": metadata.get("authors", ""),
            "Online Categories": metadata.get("categories", ""),
            "Online Description": metadata.get("description", ""),
            "Preview Link": metadata.get("preview_link", ""),
            "Thumbnail": metadata.get("thumbnail", ""),
        }

        enriched_books.append(enriched_book)

    return enriched_books
