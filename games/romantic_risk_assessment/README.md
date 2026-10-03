# To Tell or Not to Tell

A browser version of the original Python decision-tree game.

## Files

- `index.html` — page shell, site navigation, and chat UI
- `game.css` — game-only messenger/phone styling
- `game.js` — UI logic and JavaScript ↔ Pyodide ↔ Python bridge
- `game.py` — story nodes, state, calculations, and endings

## How the bridge works

```text
player clicks a response
        ↓
JavaScript captures the click
        ↓
choose("value") runs in Python through Pyodide
        ↓
Python advances GameEngine and returns JSON
        ↓
JavaScript parses the JSON
        ↓
new bestie messages + choices render in the chat
```

For numeric questions, JavaScript calls `submit_value()` instead.

## Local testing

From the project root:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000/games/bestie/
```

Do not rely on double-clicking `index.html`, because browsers often block `fetch("./game.py")`
from `file://` pages.

## Editing dialogue

Most story content is in the `NODES` dictionary in `game.py`.

A normal node looks like:

```python
"example": {
    "messages": ["Question from bestie?"],
    "choices": [
        choice("Yes", "yes", "next_node"),
        choice("No", "no", "other_node"),
    ],
},
```

An ending is:

```python
"end_example": {
    "messages": ["Final verdict."],
    "ending": True,
},
```

## Notes on the refactor

The original program contained duplicated friend-group branches and several syntax/runtime
problems. The web version shares repeated branches instead.

The seriousness scale is treated as:

- 0–2: low seriousness
- 3–5: continue into the ex/friend calculation

This resolves the original condition that effectively matched every number after 1 or 2.
