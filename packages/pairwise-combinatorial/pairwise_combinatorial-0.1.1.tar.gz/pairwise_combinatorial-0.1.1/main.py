import time

from pairwise_combinatorial import (
    combinatorial_method,
    generate_comparison_matrix,
    weighted_geometric_mean,
)


def main():
    n = 9

    A = generate_comparison_matrix(
        n,
        0,
    )

    start_time = time.time()

    result = combinatorial_method(
        A,
        n_workers=10,
        aggregator=weighted_geometric_mean,
    )

    elapsed = time.time() - start_time
    print(f"{result}")
    print(f"elapsed {elapsed}")


if __name__ == "__main__":
    main()
