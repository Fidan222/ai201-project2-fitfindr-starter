"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Usage:
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """Initialize and return a fresh session dict for one user interaction."""
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


# ── query parser ──────────────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max_price from a natural language query.
    Uses regex to find price and size mentions, then treats the rest as description.

    Returns a dict with keys: description (str), size (str|None), max_price (float|None)
    """
    # Extract price — looks for patterns like "under $30", "$30", "under 30"
    price_match = re.search(r"(?:under\s+)?\$?(\d+(?:\.\d+)?)", query, re.IGNORECASE)
    max_price = float(price_match.group(1)) if price_match else None

    # Extract size — looks for common size patterns
    size_match = re.search(
        r"\b(XXS|XS|S\/M|M\/L|L\/XL|XL\/XXL|S|M|L|XL|XXL|W\d{2}(?:\s*L\d{2})?|US\s*\d+(?:\.\d+)?)\b",
        query,
        re.IGNORECASE,
    )
    size = size_match.group(1) if size_match else None

    # Remove price and size mentions to get a cleaner description
    description = query
    if price_match:
        description = description.replace(price_match.group(0), "")
    if size_match:
        description = description.replace(size_match.group(0), "")

    # Clean up filler words so the search keywords are more useful
    filler = r"\b(looking for|i want|find me|under|around|size|a|an|the|for|and|in|im|i'm)\b"
    description = re.sub(filler, " ", description, flags=re.IGNORECASE)
    description = re.sub(r"\s+", " ", description).strip(" ,$")

    return {
        "description": description if description else query,
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
        wardrobe: User's wardrobe dict

    Returns:
        The session dict. Check session["error"] first — if not None,
        the interaction ended early and fit_card / outfit_suggestion will be None.
    """
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse the query
    parsed = _parse_query(query)
    session["parsed"] = parsed

    # Step 3: Search for listings
    results = search_listings(
        description=parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
    )
    session["search_results"] = results

    # If nothing found — set error and return early, do not proceed
    if not results:
        price_str = f" under ${parsed['max_price']:.0f}" if parsed["max_price"] else ""
        size_str = f" in size {parsed['size']}" if parsed["size"] else ""
        session["error"] = (
            f"No listings matched '{parsed['description']}'{size_str}{price_str}. "
            f"Try a broader description, a different size, or a higher budget."
        )
        return session

    # Step 4: Select the top result
    session["selected_item"] = results[0]

    # Step 5: Suggest an outfit
    outfit_suggestion = suggest_outfit(
        new_item=session["selected_item"],
        wardrobe=session["wardrobe"],
    )
    session["outfit_suggestion"] = outfit_suggestion

    # Step 6: Generate the fit card
    fit_card = create_fit_card(
        outfit=session["outfit_suggestion"],
        new_item=session["selected_item"],
    )
    session["fit_card"] = fit_card

    # Step 7: Return completed session
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found:    {session['selected_item']['title']} — ${session['selected_item']['price']} on {session['selected_item']['platform']}")
        print(f"\nOutfit:   {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
    print(f"fit_card is None: {session2['fit_card'] is None}")