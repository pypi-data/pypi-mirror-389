# LexoRank4py

LexoRank reference implementation in Python. A library for generating lexicographic ordering strings using base36 encoding.

## Installation

### Install from PyPI (Recommended)

```bash
pip install lexorank4py
```

### Install from source

```bash
# Clone the repository
git clone https://github.com/luofanlf/lexorank4py.git
cd lexorank

# Install using pip
pip install .
```

### Install in development mode

```bash
pip install -e .
```

## Usage

```python
from lexorank import (
    initialize_lexorank,
    get_rank_between,
    get_rank_before,
    get_rank_after,
    rank_to_int,
    int_to_rank,
)

# Initialize ranks for a list of items
ranks = initialize_lexorank(5)
print(ranks)  # ['0', '7', 'e', 'l', 's']

# Get rank between two ranks
rank = get_rank_between("0", "1")
print(rank)  # '08'

# Get rank before (at the head)
rank_before = get_rank_before("a")
print(rank_before)

# Get rank after (at the tail)
rank_after = get_rank_after("z")
print(rank_after)

# Convert between rank strings and integers
rank_str = int_to_rank(100)
int_value = rank_to_int("2s")
```

## API Reference

### `initialize_lexorank(num: int) -> list[str]`

Initialize lexorank strings for a given number of items.

### `get_rank_between(left: str, right: str) -> str`

Get the rank string between two ranks.

### `get_rank_before(right: str) -> str`

Get the rank string before the given rank (for inserting at the head).

### `get_rank_after(left: str) -> str`

Get the rank string after the given rank (for inserting at the tail).

### `rank_to_int(rank: str) -> int`

Convert a lexorank string (base36) to an integer.

### `int_to_rank(value: int) -> str`

Convert an integer to a lexorank string (base36).

### `int_to_rank_with_length(value: int, length: int) -> str`

Convert an integer to a lexorank string with fixed length.

