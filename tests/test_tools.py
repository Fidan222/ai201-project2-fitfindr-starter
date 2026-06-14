"""
tests/test_tools.py

Tests for each FitFindr tool. Run with: pytest tests/
Each failure mode has its own test.
"""

from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── search_listings tests ─────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []  # empty list, no exception

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)

def test_search_size_filter():
    results = search_listings("top", size="XL", max_price=None)
    # Every result should contain "xl" somewhere in the size field
    for item in results:
        assert "xl" in item["size"].lower()

def test_search_returns_correct_fields():
    results = search_listings("vintage", size=None, max_price=100)
    if results:
        required_fields = ["id", "title", "category", "price", "platform"]
        for field in required_fields:
            assert field in results[0]


# ── suggest_outfit tests ──────────────────────────────────────────────────────

def test_suggest_outfit_with_wardrobe():
    # Use a real listing-style dict as the new item
    new_item = {
        "id": "lst_006",
        "title": "Graphic Tee — 2003 Tour Bootleg Style",
        "category": "tops",
        "style_tags": ["graphic tee", "vintage", "grunge", "streetwear"],
        "colors": ["black"],
        "price": 24.00,
        "platform": "depop",
        "condition": "good",
        "size": "L",
        "brand": None,
        "description": "Vintage-style bootleg tee with faded graphic.",
    }
    wardrobe = get_example_wardrobe()
    result = suggest_outfit(new_item, wardrobe)
    assert isinstance(result, str)
    assert len(result) > 0

def test_suggest_outfit_empty_wardrobe():
    # Should not crash — should return a general suggestion
    new_item = {
        "id": "lst_006",
        "title": "Graphic Tee — 2003 Tour Bootleg Style",
        "category": "tops",
        "style_tags": ["graphic tee", "vintage", "grunge", "streetwear"],
        "colors": ["black"],
        "price": 24.00,
        "platform": "depop",
        "condition": "good",
        "size": "L",
        "brand": None,
        "description": "Vintage-style bootleg tee with faded graphic.",
    }
    wardrobe = get_empty_wardrobe()
    result = suggest_outfit(new_item, wardrobe)
    assert isinstance(result, str)
    assert len(result) > 0  # Should return something, not an empty string


# ── create_fit_card tests ─────────────────────────────────────────────────────

def test_fit_card_returns_string():
    new_item = {
        "title": "Vintage Band Tee — Faded Grey",
        "price": 19.00,
        "platform": "depop",
    }
    outfit = "Wear with dark wash baggy jeans and chunky white sneakers."
    result = create_fit_card(outfit, new_item)
    assert isinstance(result, str)
    assert len(result) > 0

def test_fit_card_empty_outfit():
    # Should return an error message string, not crash
    new_item = {
        "title": "Vintage Band Tee — Faded Grey",
        "price": 19.00,
        "platform": "depop",
    }
    result = create_fit_card("", new_item)
    assert isinstance(result, str)
    assert len(result) > 0  # Error message, not empty

def test_fit_card_mentions_platform():
    new_item = {
        "title": "Oversized Flannel Shirt",
        "price": 22.00,
        "platform": "thredUp",
    }
    outfit = "Pair with straight leg jeans and combat boots."
    result = create_fit_card(outfit, new_item)
    assert isinstance(result, str)
    # Caption should mention the platform somewhere
    assert "thredup" in result.lower() or "thredUp" in result