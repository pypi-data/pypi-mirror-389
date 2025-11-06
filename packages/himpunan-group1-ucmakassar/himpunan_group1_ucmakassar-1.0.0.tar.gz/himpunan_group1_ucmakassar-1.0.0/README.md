# Himpunan - Group 1 - Discrete Mathematics

A simple Python library for performing set operations (Himpunan) — supports Fraction and Decimal types, built for Discrete Mathematics learning.

## Installation

You can install this package from PyPI using pip:
```
pip install himpunan-group1-ucmakassar
```

### Quick Start
```
from himpunan.himpunan import Himpunan
from fractions import Fraction
from decimal import Decimal
```

## Create sets
```
A = Himpunan(1, 2, Fraction(1, 2), Decimal('3.5'))
B = Himpunan(2, 3, Fraction(3, 4))

print("Himpunan A:", A)
print("Himpunan B:", B)
```

### Union
```
print("Gabungan (A ∪ B):", A + B)
```

### Intersection
```
print("Irisan (A ∩ B):", A / B)
```

### Difference
```
print("Selisih (A - B):", A - B)
```

### Symmetric Difference
```
print("Selisih Simetris (A ⊕ B):", A * B)
```
### Cartesian Product
```
print("Perkalian Kartesius (A × B):", A ** B)
```

### Power Set
```
print("Himpunan Bagian (P(A)):", A.ListKuasa())
```

## Supported Operations
Operator	Deskripsi	Contoh
A + B	Gabungan (Union)	{1,2} + {2,3} → {1,2,3}
A / B	Irisan (Intersection)	{1,2} / {2,3} → {2}
A - B	Selisih (Difference)	{1,2} - {2,3} → {1}
A * B	Selisih Simetris (Symmetric Difference)	{1,2} * {2,3} → {1,3}
A ** B	Perkalian Kartesius (Cartesian Product)	{1,2} ** {3,4} → [(1,3),(1,4),(2,3),(2,4)]
A.ListKuasa()	Himpunan Bagian (Power Set)	[∅, {1}, {2}, {1,2}]

## Example Output
```
A = Himpunan(1, 2)
B = Himpunan(2, 3)

print(A + B)   # {1, 2, 3}
print(A / B)   # {2}
print(A - B)   # {1}
print(A * B)   # {1, 3}
print(A ** B)  # [(1, 2), (1, 3), (2, 2), (2, 3)]
```

## Authors
Group 1:<br>
Keihan Pradika Muzaki (0806022410011)<br>
Michele Stevany Venda Dati (0806022410021)<br>
Siti Amirah Nathania Fahreza (0806022410024)<br>
Universitas Ciputra Surabaya (Kampus Kota Makassar)<br>
📧 Email: mchlstvny@gmail.com

## License
This project is licensed under the MIT License — see the LICENSE file for details.