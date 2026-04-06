# Anki Statistics Extended Configuration

## `tag_filter_regex`

Optional regular expression used to decide which tags count as units in the charts.

- `null` means every tag is eligible.
- If provided, only matching tags are included.

Example:

```json
{
  "tag_filter_regex": "^EXAMPLE::"
}
```

## `tag_filter_regex_by_deck`

Optional deck-specific overrides for `tag_filter_regex`.

The add-on checks:

1. the current deck name
2. then parent decks from most specific to least specific
3. then the global `tag_filter_regex`

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

If a regex is invalid, the add-on ignores it and falls back to showing all tags instead of failing to render charts.
