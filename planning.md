# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
Searches the mock listings dataset and returns items that match the user's description, size, and price ceiling. It compares the description against each listing's title, style_tags, and category fields.
**Input parameters:**
- `description` (str): A natural language description of what the user is looking for (e.g. "vintage graphic tee", "flannel shirt"). Matched against title, style_tags, and category.
- `size` (str): The size the user wears (e.g. "M", "W30", "S/M"). If None, size is not filtered.
- `max_price` (float): The highest price the user is willing to pay. If None, price is not filtered

**What it returns:**
A list of matching listing dicts, each containing: id, title, category, style_tags, size, condition, price, colors, brand, platform. The list is sorted by relevance (number of matching style_tags). Returns an empty list if nothing matches.
**What happens if it fails or returns nothing:**
The agent tells the user: "No listings matched your search. Try broadening the description, adjusting your size, or raising your budget." The agent stops, it does not call suggest_outfit or create_fit_card with empty input.
---

### Tool 2: suggest_outfit

**What it does:**
Takes a specific listing item and the user's wardrobe and suggests one complete outfit combination, including which wardrobe pieces pair well with the new item and brief styling notes.
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): A single listing dict returned by search_listings (contains title, category, colors, style_tags, etc.).
- `wardrobe` (dict): A wardrobe dict with an items key containing a list of wardrobe item dicts. Each wardrobe item has: id, name, category, colors, style_tags, and optional notes.

**What it returns:**
A string describing a complete outfit — which wardrobe pieces to combine with the new item, and 1–2 sentences of styling notes (e.g. "Pair with your dark wash baggy jeans and chunky white sneakers. Tuck the front corner slightly for shape.").
**What happens if it fails or returns nothing:**
If the wardrobe is empty, the agent responds: "I don't have your wardrobe info yet, here's a general styling suggestion based on the item's vibe:" and generates a generic suggestion based on the item's style_tags and colors alone. It does not stop the flow.
---

### Tool 3: create_fit_card

**What it does:**
Generates a short, caption-ready description of the complete outfit — written in casual first-person voice, the kind of thing someone would post on Instagram or TikTok.
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion string returned by suggest_outfit.
- `new_item` (dict): The listing dict for the item that was found (used to pull in price, platform, title for the caption).

**What it returns:**
A single string, 1–3 sentences, written in casual social media tone. Each call produces something different. Example: "thrifted this faded band tee off depop for $19 and it was literally made for my wide-legs 🖤 full look in bio"
**What happens if it fails or returns nothing:**
If outfit is an empty string or new_item is missing key fields, the agent says: "Couldn't generate a fit card,some outfit info was missing. Here's what I have:" and returns whatever partial info is available rather than crashing.
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
After receiving the user's message, the agent runs this logic in order:

Parse the user's message to extract: item description, size (if mentioned), max price (if mentioned), and any wardrobe info they described.
Call search_listings(description, size, max_price).

If results is empty → set error message "No listings found for [description] under $[max_price]" and return early. Do not proceed.
If results is not empty → set session["selected_item"] = results[0] and continue.


Call suggest_outfit(session["selected_item"], wardrobe).

If wardrobe has no items → generate a generic suggestion from the item's style_tags, store in session["outfit_suggestion"], and continue with a note that it's wardrobe-agnostic.
If suggestion is returned → set session["outfit_suggestion"] = suggestion and continue.


Call create_fit_card(session["outfit_suggestion"], session["selected_item"]).

If fit card is returned → set session["fit_card"] = fit_card and continue.
If fit card fails → return partial output with a note.


Return all three results to the user: the listing found, the outfit suggestion, and the fit card.

The agent never calls a later tool if an earlier one returned nothing useful.---

## State Management

**How does information from one tool get passed to the next?**
The agent maintains a session dictionary for the duration of one interaction. It stores:
session["selected_item"] — the listing dict chosen from search_listings results
session["outfit_suggestion"] — the string returned by suggest_outfit
session["fit_card"] — the string returned by create_fit_card
session["wardrobe"] — the wardrobe dict (from get_example_wardrobe() or parsed from user input)
session["error"] — set if any tool fails; checked before proceeding to the next step

Each tool receives its inputs directly from the session rather than from the user re-entering them. The session is not persisted between separate conversations — it resets each time.
---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query |No listings matched '[description]' under $[max_price]. Try a broader description, a different size, or a higher budget." Agent stops and does not proceed. |
| suggest_outfit | Wardrobe is empty |I don't have your wardrobe on file, so here's a general styling idea based on this item's vibe:" followed by a tags-based suggestion. Agent continues to create_fit_card. |
| create_fit_card | Outfit input is missing or incomplete | Couldn't write a full fit card — here's what I have: [partial info]." Agent returns what it can rather than crashing.|

---

## Architecture

User query
    │
    ▼
Parse input (description, size, max_price, wardrobe info)
    │
    ▼
Planning Loop
    │
    ├─► search_listings(description, size, max_price)
    │       │
    │       ├── results = [] ──► "No listings found. Try adjusting your search." → STOP
    │       │
    │       └── results = [item, ...] 
    │               │
    │               ▼
    │       session["selected_item"] = results[0]
    │               │
    ├─► suggest_outfit(selected_item, wardrobe)
    │       │
    │       ├── wardrobe empty ──► generic tag-based suggestion, continue anyway
    │       │
    │       └── suggestion returned
    │               │
    │               ▼
    │       session["outfit_suggestion"] = suggestion
    │               │
    └─► create_fit_card(outfit_suggestion, selected_item)
            │
            ├── missing data ──► return partial output with note
            │
            └── fit_card returned
                    │
                    ▼
            session["fit_card"] = fit_card
                    │
                    ▼
        Return to user:
        [listing found] + [outfit suggestion] + [fit card]

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
search_listings: Give Claude the Tool 1 spec from this file (inputs, return value, failure mode) plus the load_listings() function signature from data_loader.py. Ask it to implement the function so it filters by all three parameters and handles the empty-results case. Verify by running 3 test queries: one that should return results, one with a price too low to match anything, and one with a size that doesn't exist in the data.
suggest_outfit: Give Claude the Tool 2 spec and the wardrobe schema from wardrobe_schema.json. Ask it to implement the function using the wardrobe dict format. Verify by testing with get_example_wardrobe() (should return a real outfit) and get_empty_wardrobe() (should return a graceful fallback, not crash).
create_fit_card: Give Claude the Tool 3 spec and two example listing dicts from listings.json. Ask it to write a function that produces a different caption each time. Verify by calling it 3 times with different items and checking that the tone is casual and the output references the actual item's price and platform.

**Milestone 4 — Planning loop and state management:**
Give Claude the Architecture diagram from this file plus the State Management section. Ask it to implement the planning loop as a function that takes a user message and a session dict, calls the three tools in order, and stores results in the session. Verify by tracing through the complete interaction example below and checking that: (1) the loop stops early when search returns nothing, (2) state from step 1 flows into step 2 without re-prompting the user, and (3) all three results appear in the final output.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
The agent reads the message and figures out what the user actually wants, a specific item at a specific price. It calls search_listings("vintage graphic tee", size=None, max_price=30.0) and gets back a few matches from the listings data. The best one is a Faded Band Tee for $22 on Depop. If nothing comes back, the agent tells the user and stops, it doesn't keep going with empty hands.
**Step 2:**
Now that there's an actual item, the agent holds onto it and calls suggest_outfit with that tee plus whatever wardrobe info the user gave. The user mentioned baggy jeans and chunky sneakers, so those go in too. The tool comes back with a full look and some notes on how to wear it. If the wardrobe is basically empty, it works with what it has and keeps the suggestion reasonable.
**Step 3:**
With a real item and a real outfit in hand, the agent calls create_fit_card to wrap it all up. This is the part that turns everything into something the user could actually post, short, casual, written like a person and not a product page.
**Final output to user:**
They see the listing that was found, how to style it, and a ready-to-use caption. If something broke along the way, they heard about it at that step, the agent never just quietly skips ahead and pretends everything is fine.