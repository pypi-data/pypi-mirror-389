# Himpunan - Group 1 - Discrete Mathematics
A simple Python library for performing set operations (Himpunan), supports Fraction and Decimal types, built for Discrete Mathematics learning.

## 📦 Installation

You can install this package from PyPI using pip:
```
pip install himpunan-group1-discrete-mathematics
```
or if you're running it locally
'''
git clone https://github.com/mchlstvny/himpunan-project-discrete-mathematics.git
cd himpunan-project-discrete-mathematics
python setup.py install
'''

## 🚀 Quick Start
```
from himpunan import Himpunan
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

## Supported Operations
| Operator       | Description                  |
|----------------|------------------------------|
| A + B          | Union (A ∪ B)                |
| A / B          | Intersection (A ∩ B)         |
| A - B          | Difference (A − B)           |
| A * B          | Symmetric Difference (A ⊕ B) |
| A ** B         | Cartesian Product (A × B)    |
| A <= B         | Subset (⊆)                   |
| A < B          | Proper Subset (⊂)            |
| A >= B         | Superset (⊇)                 |
| A // B         | Equivalent (Equal Elements)  |
| A.Komplemen(S) | Complement wrt Universal Set |
| A.ListKuasa()  | Power Set                    |
| abs(A)         | Number of Power Set Elements |
| A += x         | Add Element                  |
| A -= x         | Remove Element               |

## Example Usage
```
A = Himpunan(2, 4, 5)
B = Himpunan(1, 2, 3)

print("A ∪ B =", A + B)
print("A ∩ B =", A / B)
print("A − B =", A - B)
print("A ⊕ B =", A * B)
print("A × B =", A ** B)
print("Subset (A ⊆ B):", A <= B)
print("Superset (A ⊇ B):", A >= B)
print("Equivalent (A ≡ B):", A // B)
print("Power Set of A:", A.ListKuasa())
print("Complement of A (wrt {1,2,3,4,5}):", A.Komplemen(Himpunan(1,2,3,4,5)))
print("Total subsets in A:", abs(A))

```

## Authors
Group 1:<br>
Keihan Pradika Muzaki (0806022410011)<br>
Michele Stevany Venda Dati (0806022410021)<br>
Siti Amirah Nathania Fahreza (0806022410024)<br>
Universitas Ciputra Surabaya (Kampus Kota Makassar)<br>

## Email
kpradika@student.ciputra.ac.id<br>
mstevany@sstudent.ciputra.ac.id<br>
snathania03@student.ciputra.ac.id<

## Github Repository
```
https://github.com/mchlstvny/himpunan-project-discrete-mathematics.git
```
