# Anki Statistics Extended

This Anki add-on adds Plotly-based charts to Anki's stats view, grouped by tag. The current graphs show:

- unit mastery score
- weak units
- card status distribution by tag
- today's studied, remaining review, and new-card workload by tag

Tech: Python, Anki hooks, Plotly.js

[Download on AnkiWeb](https://ankiweb.net/shared/info/1388408398)

## Local install

Build and install into your local `addons21` folder:

```bash
make install
```

## Formatting

This repo uses `black` for Python formatting.

Check formatting:

```bash
make lint
```

Format the repo:

```bash
make format
```

Build the add-on archive only:

```bash
make build
```

Run a quick Python syntax check:

```bash
make check
```

## Configuration

The add-on supports a global tag regex and optional deck-specific overrides.

Example config:

```json
{
  "tag_filter_regex": "^EXAMPLE::",
  "tag_filter_regex_by_deck": {
    "Deck::Example 1A": "^EXAMPLE::1A::",
    "Deck::Example 2A": "^EXAMPLE::2A::"
  }
}
```

Resolution order is:

- exact current deck name
- parent decks of the current deck, from most specific to least specific
- global `tag_filter_regex`

So if your current deck is `Deck::Example 1A::Lesson 03`, the add-on will try:

- `Deck::Example 1A::Lesson 03`
- `Deck::Example 1A`
- `Deck`
- global `tag_filter_regex`

## Architecture

The add-on is organized around a small chart registry:

- `stats.py` wires into Anki's stats dialog and injects all registered charts
- `charts/base.py` provides the base chart abstractions
- `charts/registry.py` is the single place where available charts are registered
- each file in `charts/` owns one graph's data collection and Plotly rendering
- `collection.py` contains shared Anki collection helpers and card-status logic

## Adding a graph

1. Create a new chart module in `src/anki_statistics_extended/charts/`.
2. Implement a `PlotlyChart` subclass with `build_data()` and `build_render_js()`.
3. Register the chart in `src/anki_statistics_extended/charts/registry.py`.

With that in place, the graph will automatically be injected into the stats screen.
