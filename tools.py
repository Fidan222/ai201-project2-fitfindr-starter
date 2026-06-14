"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.
    """
    listings = load_listings()
    keywords = description.lower().split()

    results = []

    for item in listings:
        # Filter by price
        if max_price is not None and item["price"] > max_price:
            continue

        # Filter by size (case-insensitive, partial match)
        if size is not None:
            if size.lower() not in item["size"].lower():
                continue

        # Score by keyword overlap against title, style_tags, and category
        score = 0
        searchable = (
            item["title"].lower()
            + " "
            + " ".join(item["style_tags"]).lower()
            + " "
            + item["category"].lower()
            + " "
            + item["description"].lower()
        )
        for keyword in keywords:
            if keyword in searchable:
                score += 1

        if score > 0:
            results.append((score, item))

    # Sort by score descending, return just the dicts
    results.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in results]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.
    """
    client = _get_groq_client()

    item_summary = (
        f"{new_item['title']} — {new_item['category']}, "
        f"colors: {', '.join(new_item['colors'])}, "
        f"style: {', '.join(new_item['style_tags'])}"
    )

    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        # Empty wardrobe — give general styling advice
        prompt = f"""A user just thrifted this item: {item_summary}

They haven't shared their wardrobe yet. Give them 1-2 specific outfit ideas for this piece — 
what kinds of bottoms, shoes, and layers would work well with it. Keep it practical and specific, 
not generic. 2-4 sentences."""

    else:
        # Format wardrobe for the prompt
        wardrobe_text = "\n".join(
            f"- {w['name']} ({w['category']}, colors: {', '.join(w['colors'])})"
            for w in wardrobe_items
        )
        prompt = f"""A user just thrifted this item: {item_summary}

Here is their current wardrobe:
{wardrobe_text}

Suggest 1-2 complete outfit combinations using the new item and specific pieces from their wardrobe above. 
Name the exact wardrobe pieces. Add 1-2 sentences of styling notes. Be specific, not generic."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.
    """
    # Guard against empty outfit string
    if not outfit or not outfit.strip():
        return "Couldn't generate a fit card — outfit info was missing. Try running suggest_outfit first."

    # Guard against missing item fields
    title = new_item.get("title", "this piece")
    price = new_item.get("price", "unknown price")
    platform = new_item.get("platform", "a thrift app")

    client = _get_groq_client()

    prompt = f"""Write a short Instagram/TikTok caption for this thrifted outfit.

Item: {title}
Price: ${price}
Found on: {platform}
Outfit: {outfit}

Rules:
- 2-3 sentences max
- Casual, first-person, sounds like a real person not a brand
- Mention the item name, price, and platform naturally (once each)
- Capture the specific vibe of this outfit
- Can include 1-2 relevant emojis
- Do NOT use hashtags"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.9,  # Higher temperature so captions vary each run
    )

    return response.choices[0].message.content.strip()