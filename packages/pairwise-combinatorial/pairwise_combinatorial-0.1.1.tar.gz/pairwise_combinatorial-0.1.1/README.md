# Pairwise Combinatorial

[English version](README.en.md)

Python бібліотека для агрегації парних порівнянь з використанням комбінаторного методу та послідовностей Прюфера. Ця реалізація забезпечує ідеальну паралелізацію для майже лінійного прискорення з декількома робочими процесами.

## Особливості

- **Комбінаторний метод**: Агрегує матриці парних порівнянь через перерахування остовних дерев
- **Паралельна обробка**: Використовує послідовності Прюфера для ідеального розподілу роботи між процесами
- **Гнучка агрегація**: Підтримує зважене та просте середнє геометричне
- **Підтримка неповних матриць**: Обробляє неповні матриці парних порівнянь за допомогою LLSM
- **Генерація матриць**: Вбудовані утиліти для генерації тестових матриць порівнянь

## Встановлення

Встановити за допомогою `uv`:

```bash
uv pip install pairwise-combinatorial
```

Або встановити з джерела:

```bash
git clone https://github.com/danolekh/pairwise_combinatorial
cd pairwise-combinatorial
uv pip install -e .
```

## Швидкий старт

```python
from pairwise_combinatorial import generate_comparison_matrix, combinatorial_method, weighted_geometric_mean, weighted_arithmetic_mean

def main():
    # Генеруємо випадкову матрицю порівнянь
    n = 8 # Кількість критеріїв
    A = generate_comparison_matrix(n, missing_ratio=0.0)

    # Застосовуємо комбінаторний метод з паралельною обробкою
    result = combinatorial_method(
        A,
        n_workers=10,  # Кількість паралельних робочих процесів
        aggregator=weighted_geometric_mean,
    )

    print(f"Вектор пріоритетів: {result}")

if __name__ == '__main__':
    main()
```

## Довідник API

### Основні функції

#### `combinatorial_method(A, n_workers, aggregator)`

Основний комбінаторний метод з використанням послідовностей Прюфера.

**Параметри:**

- `A` (np.ndarray): Матриця парних порівнянь (n × n)
- `n_workers` (int | Callable): Кількість робочих процесів або функція, що повертає їх кількість
  - За замовчуванням: `smart_worker_count` (автоматично визначає на основі розміру матриці та кількості CPU)
- `aggregator` (Callable): Функція для агрегації векторів пріоритетів
  - Геометричні: `weighted_geometric_mean` (за замовчуванням), `simple_geometric_mean`
  - Арифметичні: `weighted_arithmetic_mean`, `simple_arithmetic_mean`

**Повертає:**

- `np.ndarray`: Фінальний агрегований вектор пріоритетів

### Функції агрегації

#### Геометричне середнє

#### `weighted_geometric_mean(results)`

Агрегує вектори пріоритетів за допомогою зваженого середнього геометричного.

#### `simple_geometric_mean(results)`

Агрегує вектори пріоритетів за допомогою простого середнього геометричного (рівні ваги).

#### Арифметичне середнє

#### `weighted_arithmetic_mean(results)`

Агрегує вектори пріоритетів за допомогою зваженого середнього арифметичного.

#### `simple_arithmetic_mean(results)`

Агрегує вектори пріоритетів за допомогою простого середнього арифметичного (рівні ваги).

### Допоміжні функції

#### `generate_comparison_matrix(n, missing_ratio, generator)`

Генерує матрицю парних порівнянь.

**Параметри:**

- `n` (int): Розмірність матриці (кількість критеріїв)
- `missing_ratio` (float): Частка відсутніх порівнянь (від 0.0 до 1.0)
- `generator` (Callable): Функція, що генерує значення порівнянь
  - За замовчуванням: `saaty_generator` (використовує шкалу Сааті 1-9)

**Повертає:**

- `np.ndarray`: Матриця парних порівнянь

#### `is_full(A)`

Перевіряє, чи матриця порівнянь не має відсутніх значень.

#### `is_connected(A)`

Перевіряє, чи граф матриці порівнянь є зв'язним.

#### `calculate_consistency_ratio(A, w)`

Обчислює коефіцієнт узгодженості (CR) для матриці парних порівнянь.

#### `llsm_incomplete(A)`

Заповнює неповні матриці за допомогою методу логарифмічних найменших квадратів.

### Вибір кількості робочих процесів

#### `smart_worker_count(n)`

Інтелектуально визначає кількість робочих процесів на основі розміру матриці та кількості CPU.

#### `auto_detect_workers()`

Автоматично визначає кількість робочих процесів лише на основі кількості CPU.

## Приклади

### Приклад з повною матрицею

```python
import numpy as np
from pairwise_combinatorial import combinatorial_method, weighted_geometric_mean

# Створюємо просту матрицю порівнянь 4x4
A = np.array([
    [1.0, 3.0, 5.0, 7.0],
    [1/3, 1.0, 2.0, 4.0],
    [1/5, 1/2, 1.0, 2.0],
    [1/7, 1/4, 1/2, 1.0]
])

# Обчислюємо вектор пріоритетів
weights = combinatorial_method(A, n_workers=4)
print(f"Ваги: {weights}")
```

### Приклад з неповною матрицею

```python
import numpy as np
from pairwise_combinatorial import (
    combinatorial_method,
    generate_comparison_matrix,
    is_connected,
)

# Генеруємо матрицю з 30% відсутніх значень
A = generate_comparison_matrix(n=6, missing_ratio=0.3)

if is_connected(A):
    # Застосовуємо комбінаторний метод
    weights = combinatorial_method(A, n_workers=4)
    print(f"Ваги: {weights}")
else:
    print("Матриця не є зв'язною!")
```

### Власна агрегація

```python
from pairwise_combinatorial import (
    combinatorial_method,
    simple_geometric_mean,
    weighted_arithmetic_mean,
    simple_arithmetic_mean,
)

# Використовуємо просте середнє геометричне
weights = combinatorial_method(
    A,
    n_workers=8,
    aggregator=simple_geometric_mean
)

# Використовуємо зважене середнє арифметичне
weights = combinatorial_method(
    A,
    n_workers=8,
    aggregator=weighted_arithmetic_mean
)

# Використовуємо просте середнє арифметичне
weights = combinatorial_method(
    A,
    n_workers=8,
    aggregator=simple_arithmetic_mean
)
```

### Перевірка узгодженості

```python
from pairwise_combinatorial import (
    combinatorial_method,
    calculate_consistency_ratio,
    generate_comparison_matrix,
)

A = generate_comparison_matrix(n=5)
weights = combinatorial_method(A)

cr = calculate_consistency_ratio(A, weights)
print(f"Коефіцієнт узгодженості: {cr:.4f}")

if cr < 0.10:
    print("Матриця має прийнятну узгодженість (за критерієм Сааті)")
else:
    print("Узгодженість матриці викликає сумніви")
```

## Продуктивність

Бібліотека використовує послідовності Прюфера для ідеальної паралелізації:

- **Розмір матриці n=5**: ~125 остовних дерев, < 1 секунди
- **Розмір матриці n=7**: ~16,807 остовних дерев, ~1 секунда
- **Розмір матриці n=8**: ~262,144 остовних дерев, ~10 секунд (8 робочих процесів)
- **Розмір матриці n=9**: ~4,782,969 остовних дерев, ~3 хвилини (10 робочих процесів)

Продуктивність масштабується майже лінійно з кількістю робочих процесів до кількості критеріїв (n).

## Деталі алгоритму

Комбінаторний метод:

1. Перераховує всі остовні дерева за допомогою послідовностей Прюфера
2. Для кожного дерева будує ідеально узгоджену МПП (ICPCM)
3. Обчислює вектори пріоритетів з кожної ICPCM
4. Агрегує всі вектори пріоритетів за допомогою середнього геометричного

Послідовності Прюфера забезпечують ідеальну паралелізацію через розподіл префіксів послідовностей між робочими процесами.

## Ліцензія

MIT
