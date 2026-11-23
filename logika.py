from datetime import datetime

"""ZIDANE (Class Barang dan fungsi validasi_input_barang())"""
def validasi_input_barang(kode: str, nama: str, harga: float, stok_awal: int, stok_min: int) -> tuple[bool, str]:
    """Memvalidasi data master barang sebelum ditambahkan ke inventaris."""
    if not kode.strip() or not nama.strip():
        return False, "Kode dan nama barang wajib diisi."
    if harga <= 0:
        return False, "Harga barang harus lebih dari 0."
    if stok_awal < 0 or stok_min < 0:
        return False, "Stok awal dan batas minimum stok tidak boleh negatif."
    return True, "Valid"


class Barang:
    """Merepresentasikan data satu item barang di toko."""

    def __init__(self, kode: str, nama: str, kategori: str, harga: float, stok: int, stok_min: int):
        self.kode = kode.strip().upper()
        self.nama = nama.strip()
        self.kategori = kategori.strip()
        self.harga = float(harga)
        self.stok = int(stok)
        self.stok_min = int(stok_min)

    def status_stok(self) -> str:
        """Menentukan status ketersediaan stok berdasarkan batas minimum."""
        if self.stok == 0:
            return "Habis"
        elif self.stok <= self.stok_min:
            return "Stok Menipis"
        return "Aman"

    def nilai_aset(self) -> float:
        """Menghitung total nilai aset berdasarkan stok saat ini dan harga satuan."""
        return self.stok * self.harga

    def to_dict(self) -> dict:
        """Mengonversi objek Barang menjadi dictionary untuk tampilan tabel."""
        return {
            "Kode": self.kode,
            "Nama Barang": self.nama,
            "Kategori": self.kategori,
            "Harga": self.harga,
            "Stok": self.stok,
            "Batas Min": self.stok_min,
            "Status": self.status_stok(),
            "Nilai Aset": self.nilai_aset(),
        }

"""RIFQI (Class InventarisToko, Class Transaksi dan fungsi rekursif hitung_total_stok())"""

class Transaksi:
    """Class induk untuk pencatatan mutasi stok barang."""

    def __init__(self, kode_barang: str, nama_barang: str, jumlah: int, jenis: str):
        self.kode_barang = kode_barang
        self.nama_barang = nama_barang
        self.jumlah = int(jumlah)
        self.jenis = jenis
        self.waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def terapkan_stok(self, barang: Barang) -> tuple[bool, str]:
        raise NotImplementedError("Sub-class harus mengimplementasikan metode ini.")

    def to_dict(self) -> dict:
        return {
            "Waktu": self.waktu,
            "Jenis": self.jenis,
            "Kode": self.kode_barang,
            "Nama Barang": self.nama_barang,
            "Jumlah": self.jumlah,
        }


class TransaksiMasuk(Transaksi):
    """Turunan Transaksi untuk penambahan stok barang."""

    def __init__(self, kode_barang: str, nama_barang: str, jumlah: int):
        super().__init__(kode_barang, nama_barang, jumlah, "Masuk")

    def terapkan_stok(self, barang: Barang) -> tuple[bool, str]:
        if self.jumlah <= 0:
            return False, "Jumlah barang masuk harus lebih dari 0."
        barang.stok += self.jumlah
        return True, f"Stok {barang.nama} bertambah +{self.jumlah} (Total: {barang.stok})."


class TransaksiKeluar(Transaksi):
    """Turunan Transaksi untuk pengurangan stok barang."""

    def __init__(self, kode_barang: str, nama_barang: str, jumlah: int):
        super().__init__(kode_barang, nama_barang, jumlah, "Keluar")

    def terapkan_stok(self, barang: Barang) -> tuple[bool, str]:
        if self.jumlah <= 0:
            return False, "Jumlah barang keluar harus lebih dari 0."
        if self.jumlah > barang.stok:
            return False, f"Stok tidak cukup! Sisa stok {barang.nama} hanya {barang.stok}."
        barang.stok -= self.jumlah
        return True, f"Stok {barang.nama} berkurang -{self.jumlah} (Sisa: {barang.stok})."


class InventarisToko:
    """Mengelola daftar objek Barang dan riwayat Transaksi."""

    def __init__(self):
        self.daftar_barang: list[Barang] = []
        self.riwayat_transaksi: list[Transaksi] = []

    def cari_barang_by_kode(self, kode: str) -> Barang | None:
        kode_bersih = kode.strip().upper()
        for item in self.daftar_barang:
            if item.kode == kode_bersih:
                return item
        return None

    def tambah_barang(self, barang: Barang) -> tuple[bool, str]:
        if self.cari_barang_by_kode(barang.kode) is not None:
            return False, f"Kode barang '{barang.kode}' sudah terdaftar."
        self.daftar_barang.append(barang)
        return True, f"Barang '{barang.nama}' berhasil ditambahkan."

    def catat_transaksi(self, kode_barang: str, jenis: str, jumlah: int) -> tuple[bool, str]:
        barang = self.cari_barang_by_kode(kode_barang)
        if barang is None:
            return False, "Barang tidak ditemukan."

        if jenis == "Masuk":
            trx = TransaksiMasuk(barang.kode, barang.nama, jumlah)
        elif jenis == "Keluar":
            trx = TransaksiKeluar(barang.kode, barang.nama, jumlah)
        else:
            return False, "Jenis transaksi tidak dikenali."

        berhasil, pesan = trx.terapkan_stok(barang)
        if berhasil:
            self.riwayat_transaksi.append(trx)
        return berhasil, pesan

"""ZASKIA (Fungsi filter_stok_menipis() dan ringkasan_mutasi())"""
def hitung_total_stok(daftar_barang: list[Barang], indeks: int = 0) -> int:
    """Menghitung total seluruh unit stok secara rekursif."""
    if indeks >= len(daftar_barang):
        return 0
    return daftar_barang[indeks].stok + hitung_total_stok(daftar_barang, indeks + 1)


def filter_stok_menipis(daftar_barang: list[Barang], keyword: str = "") -> list[dict]:
    """Menyaring barang berdasarkan kata kunci dan status stok menipis/habis."""
    kata = keyword.strip().lower()
    hasil: list[dict] = []
    for item in daftar_barang:
        cocok_kata = (
            kata == ""
            or kata in item.nama.lower()
            or kata in item.kategori.lower()
            or kata in item.kode.lower()
        )
        if cocok_kata:
            hasil.append(item.to_dict())
    return hasil


def ringkasan_mutasi(riwayat: list[Transaksi], filter_jenis: str = "Semua") -> dict:
    """Menghitung total unit masuk, total unit keluar, dan data riwayat terfilter."""
    total_masuk = 0
    total_keluar = 0
    data_tabel: list[dict] = []

    for trx in riwayat:
        if trx.jenis == "Masuk":
            total_masuk += trx.jumlah
        elif trx.jenis == "Keluar":
            total_keluar += trx.jumlah

        if filter_jenis == "Semua" or trx.jenis == filter_jenis:
            data_tabel.append(trx.to_dict())

    return {
        "total_masuk": total_masuk,
        "total_keluar": total_keluar,
        "riwayat_tabel": data_tabel,
    }