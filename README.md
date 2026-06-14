# FitFindr

A multi-tool AI agent that helps users find secondhand clothing and figure out how to wear it. The user describes what they're looking for, and FitFindr searches mock thrift listings, suggests a complete outfit using their existing wardrobe, and generates a shareable caption, all in one interaction.

---

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_key_here
```

Run the app:
```bash
python app.py
```

Open the URL shown in your terminal.
---

## Tool Inventory

### `search_listings(description: str, size: str | None, max_price: float | None) → list[dict]`

Searches the mock listings dataset for items matching the user's request. It scores each listing by how many keywords from the description appear in the listing's title, style_tags, category, and description fields. Results are sorted by score, highest first. Returns an empty list if nothing matches, never raises an exception.

Each dict in the returned list contains: `id`, `title`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`.

---

### `suggest_outfit(new_item: dict, wardrobe: dict) → str`

Takes the selected listing and the user's wardrobe and returns a string with 1–2 complete outfit combinations. If the wardrobe has items, the LLM is asked to reference specific pieces by name. If the wardrobe is empty, the LLM falls back to general styling advice based on the item's style tags and colors. Always returns a non-empty string.

---

### `create_fit_card(outfit: str, new_item: dict) → str`

Generates a short, casual caption for the outfit, the kind of thing someone would post on Instagram. Uses the item's title, price, and platform. Temperature is set to 0.9 so the output varies each run. If the outfit string is empty, returns a descriptive error message instead of crashing.

---

## How the Planning Loop Works

The agent does not call all three tools unconditionally. Here is the actual conditional logic:

1. The user's query is parsed with regex to extract a description, size (if mentioned), and max price (if mentioned). Filler words are stripped so the search keywords are clean.

2. `search_listings` is called with those parsed values. If the result is an empty list, the agent sets an error message in the session — something like "No listings matched 'designer ballgown' in size XXS under $5. Try a broader description, a different size, or a higher budget." — and returns early. `suggest_outfit` and `create_fit_card` are never called.

3. If results come back, the top result is saved as `session["selected_item"]` and passed into `suggest_outfit` along with the user's wardrobe. The agent does not ask the user to re-enter the item.

4. The outfit suggestion is saved as `session["outfit_suggestion"]` and passed into `create_fit_card` along with the selected item.

5. The session is returned with all three outputs populated.

---

## State Management

The agent uses a single `session` dictionary that lives for the duration of one interaction. It stores:

- `session["parsed"]` — the extracted description, size, and max_price from the query
- `session["search_results"]` — the full list returned by search_listings
- `session["selected_item"]` — the top result, passed into suggest_outfit
- `session["wardrobe"]` — the wardrobe dict, loaded once and reused
- `session["outfit_suggestion"]` — the string returned by suggest_outfit, passed into create_fit_card
- `session["fit_card"]` — the final caption string
- `session["error"]` — set if any step fails; checked before proceeding

Each tool gets its inputs directly from the session. The user is never asked to re-enter something the agent already has. The session resets between interactions.

---

## Error Handling

| Tool | Failure mode | What the agent does |
|------|-------------|---------------------|
| `search_listings` | No listings match the query | Sets `session["error"]` to "No listings matched '[description]' in size [size] under $[price]. Try a broader description, a different size, or a higher budget." Returns early. `suggest_outfit` and `create_fit_card` are not called. |
| `suggest_outfit` | Wardrobe is empty | Switches to a general styling prompt instead of a wardrobe-specific one. Returns general advice like "This piece pairs well with wide-leg trousers and chunky sneakers for a 90s-inspired look." Never returns an empty string. |
| `create_fit_card` | `outfit` argument is empty string | Returns "Couldn't generate a fit card because outfit info was missing. Try running suggest_outfit first." Does not call the LLM. |

**Concrete example from testing:**

Running `create_fit_card('', results[0])` with an empty outfit string returned:
```
Couldn't generate a fit card — outfit info was missing. Try running suggest_outfit first.
```
No exception was raised. The agent returned a readable string the UI could display.

---

## Spec Reflection

**One way the spec helped:** Writing out the planning loop in `planning.md` with explicit if/else branches before touching the code made the agent.py implementation straightforward. Because I had already decided "if results is empty, set error and return — do not proceed," the branching logic was already clear when it came time to write it.

**One way implementation diverged from the spec:** The spec described parsing size and price from the user's query but didn't say how. I originally assumed the LLM would handle parsing, but switched to regex instead because  it's faster, doesn't require an extra API call, and is easier to test. The tradeoff is that unusual phrasings (like "thirty dollars max" instead of "$30") won't parse correctly. For a mock project with predictable inputs this is fine, but a real version would need LLM-based parsing.

---

## AI Usage

**Instance 1 — implementing search_listings:**
I gave Claude the Tool 1 spec block from planning.md (inputs, return value, failure mode) and the `load_listings()` function signature from data_loader.py. I asked it to implement the function so it filtered by all three parameters and scored results by keyword overlap. The generated code worked but originally used `in` on the full listing string, which caused false matches (e.g. "M" matching "medium wash"). I revised it to search against specific fields like title, style_tags, category, description that is  joined as a single lowercase string.

**Instance 2 — implementing the planning loop:**
I gave Claude the Architecture diagram from planning.md and the State Management section and asked it to implement `run_agent()`. The generated code matched the spec closely but called all three tools unconditionally without checking the search result first. I revised it to add the early return after the empty-results check, which is the core branching behavior the milestone required.