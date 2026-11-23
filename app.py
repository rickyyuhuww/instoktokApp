import streamlit as st
import pandas as pd
from logika import (
    Barang,
    InventarisToko,
    validasi_input_barang,
    hitung_total_stok,
    filter_stok_menipis,
    ringkasan_mutasi,
)

st.set_page_config(page_title="InStokTok - Inventaris UMKM", page_icon="📦", layout="wide")

# Inisialisasi state agar data tersimpan selama sesi berjalan
if "inventaris" not in st.session_state:
    toko = InventarisToko()
    toko.tambah_barang(Barang("BRG001", "Beras Pandan Wangi 5kg", "Sembako", 72000, 15, 5))
    toko.tambah_barang(Barang("BRG002", "Minyak Goreng 2L", "Sembako", 36000, 4, 5))
    toko.tambah_barang(Barang("BRG003", "Gula Pasir 1kg", "Sembako", 17500, 20, 8))
    st.session_state.inventaris = toko

inventaris: InventarisToko = st.session_state.inventaris


def render_form_barang():
    """Menampilkan form penambahan master barang baru."""
    with st.form("form_tambah_barang", clear_on_submit=True):
        st.subheader("Tambah Master Barang Baru")
        col1, col2 = st.columns(2)
        with col1:
            kode = st.text_input("Kode Barang (misal: BRG004)")
            nama = st.text_input("Nama Barang")
            kategori = st.selectbox("Kategori", ["Sembako", "Minuman", "Makanan Ringan", "ATK", "Lainnya"])
        with col2:
            harga = st.number_input("Harga Satuan (Rp)", min_value=0, step=500)
            stok_awal = st.number_input("Stok Awal", min_value=0, step=1)
            stok_min = st.number_input("Batas Minimum Stok", min_value=0, step=1, value=5)

        submit = st.form_submit_button("Simpan Barang", use_container_width=True)
        if submit:
            valid, pesan_validasi = validasi_input_barang(kode, nama, harga, stok_awal, stok_min)
            if not valid:
                st.error(pesan_validasi)
            else:
                barang_baru = Barang(kode, nama, kategori, harga, stok_awal, stok_min)
                sukses, pesan = inventaris.tambah_barang(barang_baru)
                if sukses:
                    st.success(pesan)
                    st.rerun()
                else:
                    st.warning(pesan)


def render_form_transaksi():
    """Menampilkan form pencatatan barang masuk dan keluar."""
    st.subheader("Catat Transaksi Stok")
    if not inventaris.daftar_barang:
        st.info("Belum ada barang terdaftar. Tambahkan barang terlebih dahulu.")
        return

    opsi_barang = {f"{b.kode} - {b.nama} (Sisa: {b.stok})": b.kode for b in inventaris.daftar_barang}
    with st.form("form_transaksi", clear_on_submit=True):
        pilihan = st.selectbox("Pilih Barang", list(opsi_barang.keys()))
        col1, col2 = st.columns(2)
        with col1:
            jenis = st.radio("Jenis Transaksi", ["Masuk", "Keluar"], horizontal=True)
        with col2:
            jumlah = st.number_input("Jumlah Unit", min_value=1, step=1, value=1)

        submit_trx = st.form_submit_button("Proses Transaksi", use_container_width=True)
        if submit_trx:
            kode_terpilih = opsi_barang[pilihan]
            sukses, pesan = inventaris.catat_transaksi(kode_terpilih, jenis, jumlah)
            if sukses:
                st.success(pesan)
                st.rerun()
            else:
                st.error(pesan)


def tampilkan_tabel_stok():
    """Menampilkan pencarian, peringatan stok menipis, dan tabel inventaris dengan Pandas."""
    st.subheader("Daftar Inventaris & Status Stok")
    col_cari, col_filter = st.columns([3, 1])
    with col_cari:
        keyword = st.text_input("Cari barang berdasarkan kode, nama, atau kategori...")
    with col_filter:
        hanya_menipis = st.checkbox("Hanya stok menipis/habis")

    data_stok = filter_stok_menipis(inventaris.daftar_barang, keyword)
    if hanya_menipis:
        data_stok = [item for item in data_stok if item["Status"] != "Aman"]

    if data_stok:
        df_stok = pd.DataFrame(data_stok)
        st.dataframe(
            df_stok,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Harga": st.column_config.NumberColumn("Harga (Rp)", format="Rp %d"),
                "Nilai Aset": st.column_config.NumberColumn("Nilai Aset (Rp)", format="Rp %d"),
            },
        )
    else:
        st.warning("Data barang tidak ditemukan.")


# --- TAMPILAN UTAMA ---
st.title("📦 InStokTok — Manajemen Inventaris UMKM")
st.caption("Aplikasi pencatatan keluar-masuk barang sederhana untuk toko kelontong & ritel.")

rekap = ringkasan_mutasi(inventaris.riwayat_transaksi)
total_unit = hitung_total_stok(inventaris.daftar_barang)
jumlah_menipis = sum(1 for b in inventaris.daftar_barang if b.status_stok() != "Aman")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Jenis Barang", f"{len(inventaris.daftar_barang)} Item")
m2.metric("Total Unit Stok (Rekursif)", f"{total_unit} Unit")
m3.metric("Perlu Restock", f"{jumlah_menipis} Item")
m4.metric("Mutasi (Masuk / Keluar)", f"+{rekap['total_masuk']} / -{rekap['total_keluar']}")

st.divider()

tab_stok, tab_transaksi, tab_master, tab_riwayat = st.tabs(
    ["📋 Stok Barang", "🔄 Catat Keluar/Masuk", "➕ Tambah Barang", "📜 Riwayat Mutasi"]
)

with tab_stok:
    tampilkan_tabel_stok()

with tab_transaksi:
    render_form_transaksi()

with tab_master:
    render_form_barang()

with tab_riwayat:
    st.subheader("Riwayat Transaksi Keluar-Masuk")
    filter_jenis = st.selectbox("Filter Jenis Mutasi", ["Semua", "Masuk", "Keluar"])
    hasil_mutasi = ringkasan_mutasi(inventaris.riwayat_transaksi, filter_jenis)
    if hasil_mutasi["riwayat_tabel"]:
        df_riwayat = pd.DataFrame(hasil_mutasi["riwayat_tabel"])
        st.dataframe(df_riwayat, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada riwayat transaksi tercatat.")