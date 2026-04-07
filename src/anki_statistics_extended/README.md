# Anki Statistics Extended

Anki Statistics Extended adds extra charts to Anki's statistics screen, with a focus on tag-based progress tracking. 📊

It is designed for learners who organize their decks with structured tags such as units, lessons, chapters, or sections. 🏷️

## What it shows ✨

- 📈 Unit mastery score
- ⚠️ Weak units overview
- 🗂️ Card status distribution by tag
- 📚 Today's studied, remaining review, and new-card workload by tag

## Configuration ⚙️

The add-on supports:

- a global tag regex
- optional deck-specific regex overrides

This makes it possible to treat only some tags as units, or use different tag patterns for different decks. 🎯

Example:

```json
{
  "tag_filter_regex": "^EXAMPLE::",
  "tag_filter_regex_by_deck": {
    "Deck::Example 1A": "^EXAMPLE::1A::",
    "Deck::Example 2A": "^EXAMPLE::2A::"
  }
}
```

If no regex is set, all tags are eligible. ✅
