# Himpunan - Group 1 - Discrete Mathematics
A simple Python library for performing set operations (Himpunan), supports Fraction and Decimal types, built for Discrete Mathematics learning.

## Installation

You can install this package from PyPI using pip:
```
pip install mtkdiskrit-himpunan-group1-ucmakassar
```

### Quick Start
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
## Testing User Inputs
```
from himpunan import Himpunan
from fractions import Fraction
from decimal import Decimal

def main():
    A_input = input("Masukkan elemen himpunan A (pisahkan dengan spasi): ").split()
    B_input = input("Masukkan elemen himpunan B (pisahkan dengan spasi): ").split()

    A = Himpunan(*A_input)
    B = Himpunan(*B_input)

    print("\nHimpunan A:", A)
    print("Himpunan B:", B)

    while True:
        print("\n=== MENU OPERASI ===")
        print("1. Gabungan (A ∪ B)")
        print("2. Irisan (A ∩ B)")
        print("3. Selisih (A - B)")
        print("4. Selisih Simetris (A ⊕ B)")
        print("5. Perkalian Kartesius (A × B)")
        print("6. Himpunan Bagian (P(A))")
        print("7. Keluar")

        pilihan = input("Pilih operasi (1-7): ")

        if pilihan == "1":
            print("Hasil Gabungan:", A + B)
        elif pilihan == "2":
            print("Hasil Irisan:", A / B)
        elif pilihan == "3":
            print("Hasil Selisih (A - B):", A - B)
        elif pilihan == "4":
            print("Hasil Selisih Simetris:", A * B)
        elif pilihan == "5":
            print("Hasil Perkalian Kartesius:")
            for pasangan in (A ** B):
                print(pasangan)
        elif pilihan == "6":
            print("Himpunan Bagian dari A:")
            P_A = A.ListKuasa()
            for subset in P_A:
                print(subset)
            print(f"Total Himpunan Bagian: {len(P_A)}")
        elif pilihan == "7":
            print("Terima kasih! Program selesai.")
            break
        else:
            print("Pilihan tidak valid, coba lagi.")

if __name__ == "__main__":
    main()
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
