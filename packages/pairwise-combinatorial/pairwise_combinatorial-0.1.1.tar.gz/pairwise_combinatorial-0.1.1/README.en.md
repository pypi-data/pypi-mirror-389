# Pairwise Combinatorial

A Python library for pairwise comparison aggregation using the combinatorial method with Prüfer sequence enumeration. This implementation features perfect parallelization for near-linear speedup with multiple workers.

## Features

- **Combinatorial Method**: Aggregates pairwise comparison matrices using spanning tree enumeration
- **Parallel Processing**: Leverages Prüfer sequences for perfect work distribution across workers
- **Flexible Aggregation**: Supports weighted and simple geometric mean aggregation
- **Incomplete Matrix Support**: Handles incomplete pairwise comparison matrices using LLSM
- **Matrix Generation**: Built-in utilities for generating test comparison matrices

## Installation

Install using `uv`:

```bash
uv pip install pairwise-combinatorial
```

Or install from source:

```bash
git clone https://github.com/danolekh/pairwise_combinatorial
cd pairwise-combinatorial
uv pip install -e .
```

## Quick Start

```python
from pairwise_combinatorial import generate_comparison_matrix, combinatorial_method, weighted_geometric_mean, weighted_arithmetic_mean

def main():
    # Generate a random comparison matrix
    n = 8  # Number of criteria
    A = generate_comparison_matrix(n, missing_ratio=0.0)

    # Apply combinatorial method with parallel processing
    result = combinatorial_method(
        A,
        n_workers=10,  # Number of parallel workers
        aggregator=weighted_geometric_mean,
    )

    print(f"Priority vector: {result}")

if __name__ == '__main__':
    main()
```

## API Reference

### Main Functions

#### `combinatorial_method(A, n_workers, aggregator)`

Main combinatorial method using Prüfer sequence enumeration.

**Parameters:**

- `A` (np.ndarray): Pairwise comparison matrix (n × n)
- `n_workers` (int | Callable): Number of workers or function returning worker count
  - Default: `smart_worker_count` (auto-detects based on matrix size and CPU count)
- `aggregator` (Callable): Function to aggregate priority vectors
  - Geometric: `weighted_geometric_mean` (default), `simple_geometric_mean`
  - Arithmetic: `weighted_arithmetic_mean`, `simple_arithmetic_mean`

**Returns:**

- `np.ndarray`: Final aggregated priority vector

### Aggregation Functions

#### Geometric Mean

#### `weighted_geometric_mean(results)`

Aggregates priority vectors using quality-weighted geometric mean.

#### `simple_geometric_mean(results)`

Aggregates priority vectors using simple geometric mean (equal weights).

#### Arithmetic Mean

#### `weighted_arithmetic_mean(results)`

Aggregates priority vectors using quality-weighted arithmetic mean.

#### `simple_arithmetic_mean(results)`

Aggregates priority vectors using simple arithmetic mean (equal weights).

### Helper Functions

#### `generate_comparison_matrix(n, missing_ratio, generator)`

Generates a pairwise comparison matrix.

**Parameters:**

- `n` (int): Matrix dimension (number of criteria)
- `missing_ratio` (float): Ratio of missing comparisons (0.0 to 1.0)
- `generator` (Callable): Function that generates comparison values
  - Default: `saaty_generator` (uses Saaty scale 1-9)

**Returns:**

- `np.ndarray`: Pairwise comparison matrix

#### `is_full(A)`

Check if the comparison matrix has no missing values.

#### `is_connected(A)`

Check if the comparison matrix graph is connected.

#### `calculate_consistency_ratio(A, w)`

Calculate the Consistency Ratio (CR) for a pairwise comparison matrix.

#### `llsm_incomplete(A)`

Fill incomplete matrices using Log Least Squares Method.

### Worker Selection

#### `smart_worker_count(n)`

Intelligently select number of workers based on matrix size and CPU count.

#### `auto_detect_workers()`

Auto-detect number of workers based on CPU count only.

## Examples

### Complete Matrix Example

```python
import numpy as np
from pairwise_combinatorial import combinatorial_method, weighted_geometric_mean

# Create a simple 4x4 comparison matrix
A = np.array([
    [1.0, 3.0, 5.0, 7.0],
    [1/3, 1.0, 2.0, 4.0],
    [1/5, 1/2, 1.0, 2.0],
    [1/7, 1/4, 1/2, 1.0]
])

# Calculate priority vector
weights = combinatorial_method(A, n_workers=4)
print(f"Weights: {weights}")
```

### Incomplete Matrix Example

```python
import numpy as np
from pairwise_combinatorial import (
    combinatorial_method,
    generate_comparison_matrix,
    is_connected,
)

# Generate matrix with 30% missing values
A = generate_comparison_matrix(n=6, missing_ratio=0.3)

if is_connected(A):
    # Apply combinatorial method
    weights = combinatorial_method(A, n_workers=4)
    print(f"Weights: {weights}")
else:
    print("Matrix is not connected!")
```

### Custom Aggregation

```python
from pairwise_combinatorial import (
    combinatorial_method,
    simple_geometric_mean,
    weighted_arithmetic_mean,
    simple_arithmetic_mean,
)

# Use simple geometric mean
weights = combinatorial_method(
    A,
    n_workers=8,
    aggregator=simple_geometric_mean
)

# Use weighted arithmetic mean
weights = combinatorial_method(
    A,
    n_workers=8,
    aggregator=weighted_arithmetic_mean
)

# Use simple arithmetic mean
weights = combinatorial_method(
    A,
    n_workers=8,
    aggregator=simple_arithmetic_mean
)
```

### Consistency Check

```python
from pairwise_combinatorial import (
    combinatorial_method,
    calculate_consistency_ratio,
    generate_comparison_matrix,
)

A = generate_comparison_matrix(n=5)
weights = combinatorial_method(A)

cr = calculate_consistency_ratio(A, weights)
print(f"Consistency Ratio: {cr:.4f}")

if cr < 0.10:
    print("Matrix is acceptably consistent (Saaty's guideline)")
else:
    print("Matrix consistency is questionable")
```

## Performance

The library uses Prüfer sequence enumeration for perfect parallelization:

- **Matrix size n=5**: ~125 spanning trees, < 1 second
- **Matrix size n=7**: ~16,807 spanning trees, ~1 second
- **Matrix size n=8**: ~262,144 spanning trees, ~10 seconds (8 workers)
- **Matrix size n=9**: ~4,782,969 spanning trees, ~3 minutes (10 workers)

Performance scales near-linearly with the number of workers up to the number of criteria (n).

## Algorithm Details

The combinatorial method:

1. Enumerates all spanning trees using Prüfer sequences
2. For each tree, constructs an Ideally Consistent PCM (ICPCM)
3. Calculates priority vectors from each ICPCM
4. Aggregates all priority vectors using geometric mean

Prüfer sequences provide perfect parallelization by distributing sequence prefixes across workers.

## License

MIT
