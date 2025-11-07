# pyarraytools

Flatten, chunk, deduplicate, rotate, shuffle, and group lists.

## Installation

```bash
pip install pyarraytools
```

## Usage

```python
from pyarraytools import flatten, chunk, deduplicate

flatten([[1, 2], [3, 4]])  # [1, 2, 3, 4]
chunk([1, 2, 3, 4, 5], 2)  # [[1, 2], [3, 4], [5]]
deduplicate([1, 2, 2, 3])  # [1, 2, 3]
```

## License

MIT

