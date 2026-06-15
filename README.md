# SPK Pemilihan Saham Undervalued — Sektor Basic Material BEI

Sistem Pendukung Keputusan berbasis web menggunakan metode **TOPSIS** dengan
kriteria fundamental **Benjamin Graham & Peter Lynch**, dibangun dengan Python
dan Streamlit. Sesuai landasan skripsi yang Anda lampirkan.

## Garis besar tahapan pembuatan

Mengikuti alur penelitian pada Bab III skripsi, aplikasi ini dibangun melalui
enam tahap berikut.

**Tahap 1 — Studi literatur & identifikasi masalah.** Mengkaji konsep pasar
modal, analisis fundamental, kriteria screening Graham–Lynch, metode TOPSIS,
serta tools pengembangan (Python + Streamlit). Output tahap ini adalah rumusan
masalah dan delapan rasio yang akan menjadi kriteria penilaian: PER, PBV, DER,
ROE, EPS, Current Ratio, Net Profit Margin, dan PEG Ratio.

**Tahap 2 — Pengumpulan data.** Data laporan keuangan tahunan emiten sektor
basic material BEI periode 2021–2024 diekstraksi menggunakan teknik web
scraping. Modul `scraper.py` memanfaatkan library `yfinance` untuk mengunduh
rasio-rasio fundamental, lalu `preprocess()` membersihkan data (NaN, outlier,
konversi unit) dan menyimpannya sebagai CSV.

**Tahap 3 — Perancangan sistem.** Tiga komponen perancangan: (a) use case
diagram dengan 4 use case utama — pilih periode, atur bobot, jalankan TOPSIS,
ekspor hasil; (b) flowchart algoritma TOPSIS lima tahap; (c) rancangan UI tiga
halaman — Input, Hasil Ranking, Detail Saham.

**Tahap 4 — Implementasi sistem.** Empat modul utama:

- `scraper.py` — modul scraping & preprocessing.
- `topsis.py` — modul komputasi TOPSIS (normalisasi, pembobotan, solusi ideal
  positif/negatif, jarak Euclidean, skor preferensi).
- `sample_data.csv` — data sampel untuk demo (2021–2024).
- `app.py` — modul antarmuka web Streamlit dengan tiga halaman.

**Tahap 5 — Pengujian sistem.** Black Box Testing terhadap enam aspek
fungsional (input periode, pengaturan bobot, kalkulasi TOPSIS, tampilan
ranking, visualisasi, ekspor) plus validasi akurasi dengan membandingkan
output sistem terhadap perhitungan manual pada spreadsheet (toleransi
ε ≤ 0,0001).

**Tahap 6 — Analisis hasil & penarikan kesimpulan.** Menganalisis konsistensi
saham yang masuk peringkat atas lintas tahun, kelebihan dan keterbatasan
sistem, lalu menyusun kesimpulan dan saran.

## Struktur file

```
app.py                       ← Aplikasi Streamlit utama (3 halaman)
topsis.py                    ← Algoritma TOPSIS murni
scraper.py                   ← Scraping yfinance + preprocessing
sample_data.csv              ← Data demo 12 emiten × 4 tahun
template_input_saham.xlsx    ← Template Excel siap pakai (3 sheet)
requirements.txt             ← Daftar dependensi
README.md                    ← Dokumen ini
```

## Template Excel siap pakai

File `template_input_saham.xlsx` berisi tiga sheet:

1. **Petunjuk** — panduan singkat pengisian data dan aturan format.
2. **Data Saham** — tabel header dengan indikator tipe kriteria (COST/BENEFIT),
   20 baris contoh data, dan 15 baris kosong berwarna kuning untuk diisi user.
   Sudah dilengkapi data validation pada kolom Tahun (2020–2030).
3. **Bobot Preset** — tiga skenario bobot siap pakai (Merata, Graham-Lynch,
   Valuasi Dominan) dengan formula SUM untuk validasi total = 1.

Di aplikasi Streamlit, klik **"Unduh template"** di sidebar, isi data Anda,
lalu upload kembali — aplikasi otomatis mengenali sheet "Data Saham" dan
me-rename kolom (ROE (%) → ROE, dst.) sebelum menjalankan TOPSIS.

## Cara menjalankan

```bash
# 1. Pasang dependensi
pip install -r requirements.txt

# 2. (Opsional) ambil data terbaru dari Yahoo Finance
python scraper.py

# 3. Jalankan aplikasi web
streamlit run app.py
```

Buka `http://localhost:8501` di browser. Aplikasi punya tiga halaman:

1. **Input & Konfigurasi** — pilih tahun, pilih kriteria, atur bobot.
2. **Hasil Perangkingan** — tabel ranking + bar chart + heatmap + ekspor CSV.
3. **Detail Saham** — pemeriksaan ambang batas Graham-Lynch per emiten + tren
   historis tiap rasio.

## Catatan tipe kriteria

| Kriteria          | Tipe    | Alasan                                         |
|-------------------|---------|------------------------------------------------|
| PER               | cost    | Semakin rendah, semakin murah relatif laba     |
| PBV               | cost    | Semakin rendah, semakin murah relatif ekuitas  |
| DER               | cost    | Utang kecil = neraca sehat                     |
| ROE               | benefit | Profitabilitas tinggi diinginkan               |
| EPS               | benefit | Laba per saham tinggi diinginkan               |
| Current Ratio     | benefit | Likuiditas tinggi diinginkan                   |
| Net Profit Margin | benefit | Efisiensi laba tinggi diinginkan               |
| PEG Ratio         | cost    | PER relatif pertumbuhan, rendah lebih baik     |
