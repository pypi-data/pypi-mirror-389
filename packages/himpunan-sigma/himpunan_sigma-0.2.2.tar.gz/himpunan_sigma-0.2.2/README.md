# Implementasi Himpunan Python (Tugas Matdis)

Ini adalah sebuah paket Python sederhana yang mengimplementasikan konsep Himpunan (Set) untuk tugas mata kuliah Matematika Diskrit.

Paket ini dibuat murni menggunakan Python, tanpa bergantung pada `set` bawaan Python, dan menggunakan *magic methods* untuk operasi himpunan.

## ✨ Fitur

Kelas `Himpunan` ini mendukung operasi-operasi berikut:

* **Gabungan (Union):** `h1 + h2`
* **Irisan (Intersect):** `h1 / h2`
* **Selisih (Difference):** `h1 - h2`
* **Selisih Simetris:** `h1 * h2`
* **Cartesian Product:** `h1 ** h2`
* **Pengecekan Subset:** `h1 <= h2` (subset) atau `h1 < h2` (proper subset)
* **Pengecekan Superset:** `h1 >= h2`
* **Pengecekan Kesamaan:** `h1 == h2`
* **Komplemen:** `h1.komplement(S)`
* **Himpunan Kuasa (Power Set):** `h1.ListKuasa()`
* **Kardinalitas Himpunan Kuasa:** `abs(h1)`

## 📦 Instalasi

Kamu bisa meng-install paket ini menggunakan `pip`:

```bash
pip install himpunan-sigma==0.2.1