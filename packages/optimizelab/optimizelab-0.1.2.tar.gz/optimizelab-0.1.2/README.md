# optimizelab

A collection of classical and nature-inspired optimization algorithms.

**Author:** code spaze

## Installation

From this folder, you can build distributions and upload to PyPI:

```bash
python -m pip install --upgrade build twine
python -m build
twine upload dist/*
```

## Usage

```python
from optimizelab import tabu_search
print(tabu_search.source_code)  # view the source of the tabu search module
```
