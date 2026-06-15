# Cara Menjalankan Aplikasi (Windows)

File `.py` itu kode program — bukan file yang langsung jalan kalau diklik
dua kali. Aplikasi ini butuh **Python** dan **Streamlit** untuk menampilkan
halaman web-nya. Ikuti tiga langkah di bawah.

---

## Langkah 1 — Pasang Python (sekali saja)

1. Buka https://www.python.org/downloads/ di browser.
2. Klik tombol **Download Python 3.x.x** (versi 3.10 ke atas).
3. Buka file installer.
4. **PENTING:** centang kotak **"Add Python to PATH"** di bagian bawah jendela
   installer sebelum klik *Install Now*.
5. Tunggu sampai instalasi selesai → klik *Close*.

Cek instalasi: buka **Command Prompt** (tekan tombol Windows, ketik `cmd`,
Enter), lalu ketik:

```
python --version
```

Kalau muncul `Python 3.x.x`, instalasi berhasil.

---

## Langkah 2 — Klik dua kali `jalankan_aplikasi.bat`

Di folder yang sama dengan `app.py`, ada file **`jalankan_aplikasi.bat`**.

- **Klik dua kali** file tersebut.
- Jendela hitam akan terbuka. Pertama kali dijalankan, Windows akan
  mengunduh library yang dibutuhkan (streamlit, pandas, numpy, yfinance,
  matplotlib). Ini butuh **2–5 menit** tergantung kecepatan internet.
- Setelah selesai, browser akan terbuka otomatis di
  **http://localhost:8501** menampilkan aplikasi.

Kalau browser tidak terbuka otomatis, salin tautan `http://localhost:8501`
yang muncul di jendela hitam dan tempel di browser Anda.

---

## Langkah 3 — Gunakan aplikasi

Aplikasi punya tiga halaman (lihat sidebar kiri):

1. **Input & Konfigurasi** — pilih tahun, kriteria, atur bobot via slider.
2. **Hasil Perangkingan** — tabel ranking, bar chart, heatmap, ekspor CSV.
3. **Detail Saham** — pemeriksaan ambang Graham-Lynch + tren historis.

Untuk **menghentikan** aplikasi: kembali ke jendela hitam, tekan
`Ctrl + C`, lalu tutup jendelanya.

---

## Kalau ada masalah

**"python is not recognized as an internal or external command"**
→ Python belum di-PATH. Uninstall Python, pasang ulang, dan **centang
"Add Python to PATH"**.

**"ModuleNotFoundError: No module named 'streamlit'"**
→ Library belum terpasang. Buka Command Prompt di folder ini lalu ketik:
```
python -m pip install -r requirements.txt
```

**Port 8501 sudah dipakai**
→ Tutup tab Streamlit yang sebelumnya terbuka, atau jalankan dengan port
lain:
```
python -m streamlit run app.py --server.port 8502
```

**Mau lihat isi kode `.py`**
→ Buka pakai Notepad (klik kanan → Open with → Notepad), atau install
**VS Code** (https://code.visualstudio.com) untuk editor yang lebih
nyaman.
