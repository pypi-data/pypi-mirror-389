# gap-mapper

[![PyPI version](https://badge.fury.io/py/gap-mapper.svg)](https://badge.fury.io/py/gap-mapper)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A simple Python utility to find a "gapped" or "sparse" string within a text and return its original offsets.

This is useful when you need to find a string that has had extra, arbitrary spaces inserted into it.

## Installation

Install the package from PyPI:

```bash
pip install gap-mapper
```

## Usage

The main function is `gapmap()`.

It takes an `original_text` (the haystack) and a `spaced_needle` (the gapped string to find). It finds the needle (ignoring its spaces) within the original text (also ignoring its spaces) and returns the correct `(start, end)` offsets of the match *in the original text*.

```python
import gap_mapper

# The full text to search within
haystack = "Hello, world! This is the main text."

# The string to find, which has extra, inconsistent spaces
needle = "w   o r l   d"

# Find the offsets
offsets = gap_mapper.gapmap(haystack, needle)

if offsets:
    print(f"Match found at offsets: {offsets}")
    
    start, end = offsets
    print(f"Matched string: '{haystack[start:end]}'")
else:
    print("No match found.")

```
Match found at offsets: (7, 12)
Matched string: 'world'

As you can see, gapmap correctly located "world" in the haystack and returned its true offsets (7, 12), even though the needle was "w o r l d".