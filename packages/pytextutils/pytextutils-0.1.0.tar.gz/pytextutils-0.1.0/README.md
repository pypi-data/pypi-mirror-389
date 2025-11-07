# pytextutils

Common string helpers - reverse, slugify, capitalize, remove punctuation.

## Installation

```bash
pip install pytextutils
```

## Usage

```python
from pytextutils import reverse_string, slugify, capitalize_words

# Reverse a string
reverse_string("hello")  # "olleh"

# Create URL-friendly slug
slugify("Hello World")  # "hello-world"

# Capitalize words
capitalize_words("hello world")  # "Hello World"
```

## Features

- `reverse_string()` - Reverse a string
- `slugify()` - Convert text to URL-friendly slug
- `capitalize_words()` - Capitalize first letter of each word
- `remove_punctuation()` - Remove all punctuation
- `remove_whitespace()` - Remove all whitespace
- `truncate()` - Truncate text to specified length
- `word_count()` - Count words in text
- `is_palindrome()` - Check if text is a palindrome

## License

MIT

