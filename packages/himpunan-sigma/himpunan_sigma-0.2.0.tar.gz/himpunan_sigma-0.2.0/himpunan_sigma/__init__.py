import itertools

class Himpunan:
    """
    Implementasi kelas Himpunan untuk mata kuliah Matematika Diskrit.
    Dibuat tanpa menggunakan 'set' bawaan Python.
    """

    def __init__(self, *args):
        """
        Inisialisasi himpunan.
        Memastikan tidak ada elemen duplikat saat pembuatan.
        """
        self._elemen = []
        if args:
            for item in args:
                self.tambah(item)

    def tambah(self, item):
        """
        Menambah satu elemen baru ke himpunan.
        Tidak akan menambah jika elemen sudah ada.
        """
        if item not in self._elemen:
            self._elemen.append(item)

    def kurang(self, item):
        """
        Mengurangi atau menghapus satu elemen dari himpunan.
        """
        if item in self._elemen:
            self._elemen.remove(item)

    # --- Magic Methods Dasar ---

    def __repr__(self):
        """
        Representasi string dari himpunan, agar bisa di-print.
        Contoh: {1, 2, 3}
        """
        if not self._elemen:
            return "{}"
        return "{" + ", ".join(map(str, self._elemen)) + "}"

    def __str__(self):
        """Sama dengan __repr__ untuk 'print()'"""
        return self.__repr__()

    def __len__(self):
        """
        Mengembalikan jumlah elemen (kardinalitas) himpunan.
        Dipanggil menggunakan len(h)
        """
        return len(self._elemen)

    def __contains__(self, item):
        """
        Mengecek apakah suatu elemen ada di dalam himpunan.
        Dipanggil menggunakan 'item in h'
        """
        return item in self._elemen

    # --- Magic Methods Perbandingan ---

    def __eq__(self, other):
        """
        Mengecek apakah dua himpunan SAMA (equal).
        Elemen harus sama, urutan tidak penting.
        Dipanggil menggunakan 'h1 == h2'
        """
        if not isinstance(other, Himpunan):
            return False
        
        # Cara gampang tanpa 'set': cek panjang & subset
        if len(self) != len(other):
            return False
        
        return self <= other  # Reuse logic from subset

    def __le__(self, other):
        """
        Mengecek apakah himpunan ini adalah SUBSET dari 'other'.
        Dipanggil menggunakan 'h1 <= h2'
        """
        if not isinstance(other, Himpunan):
            return False
        
        for item in self._elemen:
            if item not in other:
                return False
        return True

    def __lt__(self, other):
        """
        Mengecek apakah himpunan ini adalah PROPER SUBSET dari 'other'.
        Dipanggil menggunakan 'h1 < h2'
        """
        if not isinstance(other, Himpunan):
            return False
        
        # Harus subset, dan panjangnya harus lebih kecil
        return len(self) < len(other) and self <= other

    def __ge__(self, other):
        """
        Mengecek apakah himpunan ini adalah SUPERSET dari 'other'.
        Dipanggil menggunakan 'h1 >= h2'
        """
        if not isinstance(other, Himpunan):
            return False
        
        # Logika dibalik dari subset
        return other <= self

    def __floordiv__(self, other):
        """
        Mengecek apakah dua himpunan EKUIVALEN (sesuai definisi tugas).
        Dipanggil menggunakan 'h1 // h2'
        """
        # Sesuai deskripsi tugas, ekuivalen = elemen sama.
        # Ini sama persis dengan __eq__
        return self == other

    # --- Magic Methods Operasi Himpunan ---

    def __add__(self, other):
        """
        GABUNGAN (Union) antara dua himpunan.
        Dipanggil menggunakan 'h1 + h2'
        """
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi hanya bisa dengan Himpunan lain")
        
        # Mulai dengan semua elemen dari self
        hasil_union = Himpunan(*self._elemen)
        
        # Tambah elemen dari other (metode 'tambah' akan urus duplikat)
        for item in other._elemen:
            hasil_union.tambah(item)
            
        return hasil_union

    def __truediv__(self, other):
        """
        IRISAN (Intersect) antara dua himpunan.
        Dipanggil menggunakan 'h1 / h2'
        """
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi hanya bisa dengan Himpunan lain")
            
        hasil_irisan = Himpunan()
        for item in self._elemen:
            if item in other:
                hasil_irisan.tambah(item)
        return hasil_irisan

    def __sub__(self, other):
        """
        SELISIH (Difference) antara dua himpunan.
        Dipanggil menggunakan 'h1 - h2'
        """
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi hanya bisa dengan Himpunan lain")
            
        hasil_selisih = Himpunan()
        for item in self._elemen:
            if item not in other:
                hasil_selisih.tambah(item)
        return hasil_selisih

    def __mul__(self, other):
        """
        SELISIH SIMETRIS (Symmetric Difference) antara dua himpunan.
        Dipanggil menggunakan 'h1 * h2'
        Logikanya adalah (A U B) - (A n B) atau (A - B) U (B - A)
        """
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi hanya bisa dengan Himpunan lain")
            
        # Kita pakai (A - B) + (B - A)
        selisih_a_b = self - other
        selisih_b_a = other - self
        return selisih_a_b + selisih_b_a

    def __pow__(self, other):
        """
        CARTESIAN PRODUCT antara dua himpunan.
        Dipanggil menggunakan 'h1 ** h2'
        Menghasilkan himpunan baru berisi tuple (pasangan terurut).
        """
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi hanya bisa dengan Himpunan lain")
            
        hasil_cartesian = Himpunan()
        for item_self in self._elemen:
            for item_other in other._elemen:
                hasil_cartesian.tambah((item_self, item_other))
        return hasil_cartesian
        
    def __iadd__(self, item):
        """
        Operasi 'in-place' untuk menambah elemen.
        Dipanggil menggunakan 'h1 += item'
        """
        self.tambah(item)
        return self
        
    def __isub__(self, item):
        """
        Operasi 'in-place' untuk mengurangi elemen.
        Dipanggil menggunakan 'h1 -= item'
        """
        self.kurang(item)
        return self

    # --- Metode Khusus Sesuai Tugas ---

    def komplement(self, semesta):
        """
        KOMPLEMEN dari himpunan ini terhadap himpunan Semesta.
        """
        if not isinstance(semesta, Himpunan):
            raise TypeError("Himpunan semesta harus berupa Himpunan")
        
        # Komplemen A = Semesta - A
        return semesta - self

    def __abs__(self):
        """
        MENGHITUNG HIMPUNAN KUASA (sesuai contoh).
        Contoh: abs(h1) -> 8 (karena len(h1) = 3, maka 2^3 = 8)
        Ini mengembalikan *jumlah* anggota himpunan kuasa.
        """
        return 2 ** len(self)

    def ListKuasa(self):
        """
        Menampilkan LIST HIMPUNAN KUASA (Power Set).
        Mengembalikan list yang berisi Himpunan-Himpunan bagian.
        """
        # Algoritma iteratif untuk Power Set
        list_himpunan_kuasa = [Himpunan()] # Mulai dengan himpunan kosong

        for item in self._elemen:
            new_subsets = []
            for subset in list_himpunan_kuasa:
                # Buat subset baru dengan menambahkan 'item'
                # (subset + Himpunan(item))
                new_subsets.append(subset + Himpunan(item))
            list_himpunan_kuasa.extend(new_subsets)
            
        return list_himpunan_kuasa
    
