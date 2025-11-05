# sphinx-deck

A Sphinx extension for converting reStructuredText and Markdown to [k1LoW/deck](https://github.com/k1LoW/deck)-compatible Markdown format.

## Overview

sphinx-deck enables you to write presentations in familiar reStructuredText (reST) or Markdown syntax and convert them to deck-compatible Markdown for Google Slides generation.

## Features

- Support for both reST and Markdown source files
- Convert to deck-compatible Markdown with proper slide separators (`---`)
- Automatic conversion of section headers to deck format (currently h2 and h3 for titles)

## Installation

```bash
$ pip install sphinx-deck
```

For Markdown support, also install:

```bash
$ pip install "myst-parser[linkify]"
```

## Quick Start

### Basic Setup

Add to your `conf.py`:

```python
extensions = [
    "sphinx_deck",
]
```

### With Markdown Support

```python
extensions = [
    "myst_parser",
    "sphinx_deck",
]

myst_enable_extensions = [
    "linkify",
]
myst_linkify_fuzzy_links = False
```

### Usage

For detailed examples, please see the `example/` directory in this repository.

1. Write your presentation in reST:

```restructuredtext
Title
=====

First section
-------------

Content 1
^^^^^^^^^

Content 2
^^^^^^^^^
```

2. Or write in Markdown:

```markdown
# Title

## First section

### Content 1

### Content 2
```

3. Build the deck-compatible Markdown:

```bash
$ sphinx-build -M markdown source build
```

This generates deck-compatible Markdown in the `build` directory:

```markdown
# Title

---

## First section

---

## Content 1

---

## Content 2
```

4. Use k1LoW/deck to create Google Slides:

```bash
$ deck new build/markdown/index.md
$ deck apply build/markdown/index.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
