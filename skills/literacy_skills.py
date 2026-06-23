import base64
import os
import json
from io import BytesIO

from PIL import Image

from tools.book_metadata_tool import enrich_books_inventory
from tools.openai_client import call_model, client


VISION_MODEL = "gpt-4.1"


def image_to_base64(uploaded_file):
    image = Image.open(uploaded_file).convert("RGB")
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def extract_books_from_images(uploaded_files):
    image_inputs = []

    for photo_index, uploaded_file in enumerate(uploaded_files, start=1):
        image_base64 = image_to_base64(uploaded_file)
        image_inputs.append(
            {
                "type": "input_image",
                "image_url": f"data:image/jpeg;base64,{image_base64}",
            }
        )

    prompt = """
You are the Literacy Agent for PAAI.

The user uploaded photos of books they own.

Your job is to extract as many visible or partially visible books as possible from the photos.

Important behavior:
- Extract clearly visible books.
- Also include partially readable books when there is a reasonable guess.
- Do not skip a book only because the author is unclear.
- If title is partially readable, include the best guess and mark confidence as Low.
- If author is not readable, use "Unclear".
- Do not invent books that are not visible at all.
- Be honest about uncertainty.

Language handling:
- Check for English and non-English books.
- Detect Tamil books if Tamil script is visible.
- Preserve Tamil titles exactly in Tamil script when readable.
- Do not translate Tamil titles unless you are confident.
- If possible, include transliteration in Notes.
- If language is Tamil, set Language to "Tamil".
- If country/region is likely, use "Tamil Nadu / India" or "India".
- Also detect Hindi, Telugu, Malayalam, Kannada, Spanish, French, and other languages if visible.

Confidence rules:
- High: title and author are clearly readable.
- Medium: title is readable but author is unclear, or title is mostly readable.
- Low: title is partially readable or uncertain.
- Needs Review: Yes if confidence is Medium or Low.

Return only valid JSON.
Do not include markdown.
Do not include explanation outside JSON.

Return format:

[
  {
    "Photo Number": 1,
    "Title": "Book title or best guess",
    "Original Title": "Original title as seen on book. Preserve Tamil script if readable.",
    "Display Title": "Best title to show to user. Use Tamil script for Tamil books.",
    "Translated Title": "English translation if known, otherwise Unclear",
    "Script Detected": "Tamil / Latin / Devanagari / Telugu / Malayalam / Kannada / Other / Unclear",
    "Author": "Author name or Unclear",
    "Extraction Confidence": "High / Medium / Low",
    "Needs Review": "Yes / No",
    "Why Uncertain": "Short reason or None",
    "Genre": "Likely genre",
    "Mood Fit": "Initial mood guess",
    "Energy Level": "Easy / Medium / Deep",
    "Status": "Owned",
    "Language": "Likely language or Unclear",
    "Country or Region": "Likely country/region or Unclear",
    "Award or Notability Note": "Unknown",
    "Notes": "Short reason this book may fit a mood"
  }
]
"""

    response = client.responses.create(
        model=VISION_MODEL,
        input=[
            {
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}] + image_inputs,
            }
        ],
    )

    raw_text = response.output_text

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {
            "error": "The model returned text that was not valid JSON.",
            "raw_output": raw_text,
        }


def enrich_classify_and_group_books(enriched_books):
    system_prompt = """
You are the Literacy Agent for PAAI.

You analyze a user's owned book inventory plus online metadata.

Your job:
1. Preserve extraction confidence fields exactly:
   - Photo Number
   - Extraction Confidence
   - Needs Review
   - Why Uncertain
2. Preserve multilingual fields:
   - Original Title
   - Display Title
   - Translated Title
   - Script Detected
3. Clean up genre.
4. Infer mood fit.
5. Infer energy level.
6. Infer likely language.
7. Infer country or region connected to the author/book when reasonably possible.
8. Add award or notability note.

Important:
- Preserve Tamil titles in Tamil script.
- For Tamil books, use Tamil title in Display Title when available.
- Do not falsely claim a book won an award.
- If award information is not clearly supported, use labels like:
  - "Classic / widely known"
  - "Bestselling / influential"
  - "Notability unclear"
  - "Award information not found"
- If language or country is uncertain, say "Unclear".
- If the extraction confidence is Low, keep Needs Review as Yes.
- Return only valid JSON.
- Do not include markdown.

Return format:
{
  "books": [
    {
      "Photo Number": 1,
      "Title": "Book title",
      "Original Title": "Original title",
      "Display Title": "Display title",
      "Translated Title": "Translated title or Unclear",
      "Script Detected": "Script",
      "Author": "Author",
      "Extraction Confidence": "High / Medium / Low",
      "Needs Review": "Yes / No",
      "Why Uncertain": "Reason or None",
      "Genre": "Clean genre",
      "Mood Fit": "Mood label",
      "Energy Level": "Easy / Medium / Deep",
      "Status": "Owned",
      "Language": "Language",
      "Country or Region": "Country or region",
      "Award or Notability Note": "Careful award/notability note",
      "Notes": "Short useful note",
      "Metadata Source": "Source",
      "Online Categories": "Categories",
      "Online Description": "Description",
      "Preview Link": "Preview link",
      "Thumbnail": "Thumbnail"
    }
  ],
  "suggested_moods": [
    "Mood 1",
    "Mood 2",
    "Mood 3"
  ],
  "collection_summary": "Short summary of the user's library collection."
}
"""

    user_prompt = f"""
Owned book inventory with online metadata:
{json.dumps(enriched_books, indent=2, ensure_ascii=False)}
"""

    raw_output = call_model(system_prompt, user_prompt)

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        return {
            "books": enriched_books,
            "suggested_moods": [
                "Motivated",
                "Focused",
                "Reflective",
                "Light and easy",
                "Career growth",
                "AI Product Manager growth",
            ],
            "collection_summary": "Default summary used because classification returned non-JSON output.",
            "raw_output": raw_output,
        }


def recommend_books_by_mood(mood, books_context):
    system_prompt = """
You are the Literacy Agent for PAAI.

You recommend books from the user's owned book inventory.

Rules:
- Recommend exactly 3 books.
- Recommend owned books only.
- Match the user's selected mood.
- Prefer books with High or Medium extraction confidence.
- If recommending a Low confidence book, clearly say it needs review.
- Use genre, subject, language, country/region, author, online categories, and descriptions when available.
- Preserve Tamil titles in Tamil script if available.
- For non-English books, display the original title first.
- If an English translation or transliteration exists, include it after the original title.
- Highlight award-winning, classic, bestselling, or notable books carefully.
- Explain why each book fits the mood.
- Return only valid JSON.
- Do not include markdown.

Return format:
{
  "recommendations": [
    {
      "title": "Display title. Preserve Tamil script if available.",
      "author": "Author",
      "language": "Language",
      "genre_or_subject": "Genre or subject",
      "thumbnail": "Thumbnail URL if available",
      "why_this_fits": "Short reason this book fits the selected mood",
      "confidence_note": "High confidence / Medium confidence / Needs review"
    }
  ]
}
"""

    user_prompt = f"""
User selected mood:
{mood}

Owned book inventory:
{books_context}

Recommend exactly 3 books from the owned inventory.
"""

    return call_model(system_prompt, user_prompt)


def build_enriched_book_inventory(uploaded_files):
    extracted_books = extract_books_from_images(uploaded_files)

    if isinstance(extracted_books, dict) and "error" in extracted_books:
        return extracted_books

    enriched_books = enrich_books_inventory(extracted_books)
    classified_result = enrich_classify_and_group_books(enriched_books)

    return {
        "books": classified_result.get("books", enriched_books),
        "moods": {
            "suggested_moods": classified_result.get("suggested_moods", []),
        },
        "collection_summary": classified_result.get("collection_summary", ""),
    }


def check_book_ownership(book_query):
    import pandas as pd
    from pathlib import Path

    inventory_path = Path(os.getenv("PAAI_DATA_DIR", "data")) / "books_inventory.csv"

    if not inventory_path.exists():
        return {
            "owned": False,
            "message": "I do not see a saved book inventory yet.",
            "matches": [],
        }

    df = pd.read_csv(inventory_path)

    if df.empty:
        return {
            "owned": False,
            "message": "Your saved book inventory is empty.",
            "matches": [],
        }

    query = book_query.lower().strip()

    df["Search Text"] = (
        df.get("Title", "").fillna("").astype(str)
        + " "
        + df.get("Display Title", "").fillna("").astype(str)
        + " "
        + df.get("Original Title", "").fillna("").astype(str)
        + " "
        + df.get("Translated Title", "").fillna("").astype(str)
        + " "
        + df.get("Author", "").fillna("").astype(str)
    ).str.lower()

    matches_df = df[df["Search Text"].str.contains(query, na=False)]

    if matches_df.empty:
        return {
            "owned": False,
            "message": f"I do not see '{book_query}' in your saved library.",
            "matches": [],
        }

    display_columns = [
        col for col in [
            "Title",
            "Display Title",
            "Original Title",
            "Translated Title",
            "Author",
            "Language",
            "Genre",
            "Extraction Confidence",
            "Thumbnail",
        ]
        if col in matches_df.columns
    ]

    matches = matches_df[display_columns].head(5).to_dict(orient="records")

    return {
        "owned": True,
        "message": f"Yes, you appear to own '{book_query}'.",
        "matches": matches,
    }
