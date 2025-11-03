# heapgeneratorq

A comprehensive Python package containing implementations of various algorithms and data structures for educational purposes.

## Features

This package includes implementations of:

- **LAB 1 - Searching Algorithms**: Linear and Binary Search with Student Record System
- **LAB 2 - Sorting Algorithms**: Quick Sort and Merge Sort with Transaction Management
- **LAB 3 - Graph Algorithms**: Prim's and Kruskal's Minimum Spanning Tree
- **LAB 4 - Shortest Path**: Dijkstra's Algorithm for Delivery Network
- **LAB 5 - Dynamic Programming**: 0/1 Knapsack Problem Solver
- **LAB 6 - All-Pairs Shortest Path**: Floyd-Warshall Algorithm
- **LAB 7 - Combinatorics**: Magic Square Generator (Odd, Doubly Even, Singly Even)
- **LAB 8 - Backtracking**: N-Queens Problem Solver

## Installation

Install the package using pip:

```bash
pip install heapgeneratorq
```

## Usage

After installation, you can access the algorithms file:

```python
import heapgeneratorq
import os

# Get the path to the algorithms file
algorithms_file = os.path.join(os.path.dirname(heapgeneratorq.__file__), 'l1.py')
print(f"Algorithms file located at: {algorithms_file}")

# You can also copy it to your current directory
import shutil
shutil.copy(algorithms_file, 'l1.py')
```

Or run it directly:

```bash
python -m heapgeneratorq.l1
```

## Requirements

- Python 3.7 or higher

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Your Name

## Changelog

### 0.1.0 (2025-11-03)
- Initial release
- Includes comprehensive algorithm implementations
