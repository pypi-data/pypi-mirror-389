# pyregexkit

Simplify regex matching, extraction, and replacement with human-friendly syntax.

## Installation

```bash
pip install pyregexkit
```

## Usage

```python
from pyregexkit import match_pattern, extract_all, replace_all

# Check if pattern matches
match_pattern(r"\d+", "123")  # True

# Extract all matches
extract_all(r"\d+", "abc123def456")  # ["123", "456"]

# Replace all matches
replace_all(r"\d+", "X", "abc123def456")  # "abcXdefX"
```

## License

MIT

