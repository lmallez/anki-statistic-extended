# Anki Statistics Extended

Anki add-on that adds tag-based charts to the statistics screen.

[Download on AnkiWeb](https://ankiweb.net/shared/info/98537397)  
[Report an issue](https://github.com/lmallez/anki-statistic-extended/issues)

## Features

- 📈 Unit mastery score
- ⚠️ Weak units overview
- 🗂️ Card status distribution by tag
- 📚 Today's studied, remaining review, and new-card workload by tag

Charts are rendered with Plotly and bundled in release packages, so the add-on does not depend on a third-party CDN at runtime.

## Installation

Install from [AnkiWeb](https://ankiweb.net/shared/info/98537397). 🚀

## Configuration

The add-on supports a global tag regex and optional deck-specific overrides. The same configuration help is also available inside Anki through the add-on config editor.

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

Regex lookup order:

- 1️⃣ Exact current deck name
- 2️⃣ Parent decks, from most specific to least specific
- 3️⃣ Global `tag_filter_regex`

For a current deck named `Deck::Example 1A::Lesson 03`, the add-on tries:

- `Deck::Example 1A::Lesson 03`
- `Deck::Example 1A`
- `Deck`
- global `tag_filter_regex`

If a regex is invalid, the add-on ignores it and falls back to showing all tags instead of failing to render charts.
