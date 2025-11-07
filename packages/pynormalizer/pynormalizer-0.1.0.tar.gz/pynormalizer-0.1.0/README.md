# pynormalizer

Unicode, whitespace, and accent normalization for multilingual text.

## Installation

```bash
pip install pynormalizer
```

## Usage

```python
from pynormalizer import normalize_whitespace, remove_accents

normalize_whitespace("hello    world")  # "hello world"
remove_accents("café")  # "cafe"
```

## License

MIT

