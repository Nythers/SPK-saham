"""
SPK Pemilihan Saham Undervalued — Sektor Basic Material BEI
============================================================
Sistem Pendukung Keputusan berbasis web menggunakan metode TOPSIS
dengan kriteria fundamental Benjamin Graham dan Peter Lynch.

Cara menjalankan:
    streamlit run app.py
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from topsis import CRITERIA_TYPES, run_topsis
from scraper import (
    BASIC_MATERIAL_TICKERS,
    CRITERIA_COLS as SCRAPER_CRITERIA_COLS,
    SECTORS,
    scrape_basic_material,
    preprocess,
)


# =============================================================================
# Konfigurasi halaman
# =============================================================================
st.set_page_config(
    page_title="SPK Saham Undervalued — TOPSIS",
    page_icon="📈",
    layout="wide",
)

# =============================================================================
# Palette Color
# =============================================================================
KEU = {
    "navy":       "#003d7a",
    "blue":       "#275EA8",
    "blue_light": "#3a78c2",
    "blue_dark":  "#1e4d8a",
    "gold":       "#FCB332",
    "gold_dark":  "#e09a1a",
    "gold_light": "#fdd896",
}

st.markdown(f"""
<style>
    /* ===== Global ===== */
    .stApp {{ background-color: #FFFFFF; }}
    html, body, [class*="css"] {{ color: {KEU['blue_dark']}; }}

    /* ===== Headings ===== */
    h1, h2, h3, h4 {{ color: {KEU['navy']} !important; font-weight: 700; }}
    h1 {{
        border-bottom: 4px solid {KEU['gold']};
        padding-bottom: 0.4rem;
        margin-bottom: 1rem;
    }}

    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] > div {{
        background: linear-gradient(180deg, {KEU['navy']} 0%, {KEU['blue_dark']} 100%);
    }}
    section[data-testid="stSidebar"] * {{ color: #FFFFFF !important; }}
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stFileUploader label,
    section[data-testid="stSidebar"] .stMarkdown {{ color: #FFFFFF !important; }}

    /* Sidebar buttons (download template) */
    section[data-testid="stSidebar"] .stDownloadButton button {{
        background-color: {KEU['gold']};
        color: {KEU['navy']} !important;
        border: 2px solid {KEU['gold_dark']};
        font-weight: 700;
        border-radius: 6px;
    }}
    section[data-testid="stSidebar"] .stDownloadButton button:hover {{
        background-color: {KEU['gold_dark']};
        color: #FFFFFF !important;
        border-color: {KEU['gold_dark']};
    }}

    /* Sidebar alert boxes — kembalikan teks ke gelap */
    section[data-testid="stSidebar"] [data-testid="stAlert"] * {{
        color: {KEU['navy']} !important;
    }}

    /* ===== Buttons (main area) ===== */
    .stButton button, .stDownloadButton button {{
        background-color: {KEU['navy']};
        color: #FFFFFF;
        border: none;
        border-radius: 6px;
        font-weight: 600;
    }}
    .stButton button:hover, .stDownloadButton button:hover {{
        background-color: {KEU['blue']};
        color: #FFFFFF;
    }}

    /* ===== Sliders ===== */
    .stSlider [data-baseweb="slider"] div[role="slider"] {{
        background-color: {KEU['gold']} !important;
        border-color: {KEU['gold_dark']} !important;
    }}

    /* ===== DataFrame / table styling ===== */
    .stDataFrame thead tr th {{
        background-color: {KEU['navy']} !important;
        color: #FFFFFF !important;
    }}

    /* ===== Selectbox & multiselect ===== */
    div[data-baseweb="select"] > div {{
        border-color: {KEU['blue_light']} !important;
    }}

    /* ===== Info / success / warning alerts (main) ===== */
    div[data-testid="stAlert"] {{
        border-left: 4px solid {KEU['gold']};
        background-color: {KEU['gold_light']}33;
    }}

    /* ===== Tabs ===== */
    .stTabs [data-baseweb="tab-list"] {{
        border-bottom: 2px solid {KEU['gold']};
    }}

    /* ===== Caption / footer ===== */
    .stCaption, [data-testid="stCaptionContainer"] {{
        color: {KEU['blue_dark']};
    }}
</style>
""", unsafe_allow_html=True)

DATA_PATH = Path(__file__).parent / "sample_data.csv"
TEMPLATE_PATH = Path(__file__).parent / "template_input_saham.xlsx"

CRITERIA_LIST = list(CRITERIA_TYPES.keys())  # 8 kriteria Graham-Lynch

# Pengelompokan kriteria berdasarkan acuannya
PRICE_BASED   = {"PER", "PBV", "PEG Ratio"}              # acuan: harga saham
REVENUE_BASED = {"ROE", "EPS", "Current Ratio",
                 "Net Profit Margin", "DER"}             # acuan: revenue / lap. keuangan

# Bobot awal (disarankan): dirata-ratakan
DEFAULT_WEIGHTS = {c: 0.125 for c in CRITERIA_LIST}


# =============================================================================
# Utilitas
# =============================================================================
@st.cache_data
def load_data(path: Path | None = None, uploaded: io.BytesIO | None = None,
              filename: str | None = None) -> pd.DataFrame:
    """Muat data dari file upload (CSV/XLSX) atau dari sample_data.csv default."""
    if uploaded is not None:
        name = (filename or "").lower()
        if name.endswith(".xlsx") or name.endswith(".xlsm"):
            # Baca sheet "Data Saham" jika ada, fallback ke sheet pertama.
            xls = pd.ExcelFile(uploaded)
            sheet = "Data Saham" if "Data Saham" in xls.sheet_names else xls.sheet_names[0]
            # Header di template ada di baris ke-2 (index 1), baris ke-3 indikator tipe (skip).
            df = pd.read_excel(xls, sheet_name=sheet, header=1, skiprows=[2])
            # Bersihkan nama kolom (hilangkan satuan dalam tanda kurung)
            rename_map = {
                "ROE (%)": "ROE",
                "EPS (Rp)": "EPS",
                "Net Profit Margin (%)": "Net Profit Margin",
            }
            df = df.rename(columns=rename_map)
            # Buang baris kosong / placeholder
            df = df.dropna(subset=["Tahun", "Ticker"]).reset_index(drop=True)
            df["Tahun"] = df["Tahun"].astype(int)
            return df
        return pd.read_csv(uploaded)
    if path is None:
        path = DATA_PATH
    return pd.read_csv(path)


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


@st.cache_data
def load_template_bytes() -> bytes | None:
    """Baca file template Excel sebagai bytes untuk tombol download."""
    if TEMPLATE_PATH.exists():
        return TEMPLATE_PATH.read_bytes()
    return None


def filter_by_year_sector(df: pd.DataFrame, tahun, sektor) -> pd.DataFrame:
    """Filter DataFrame berdasarkan tahun dan (opsional) sektor.

    - Jika kolom 'Sektor' tidak ada, hanya filter berdasarkan tahun.
    - Jika sektor == "(Semua)" atau None, sektor diabaikan.
    """
    out = df[df["Tahun"] == tahun]
    if sektor not in (None, "(Semua)") and "Sektor" in df.columns:
        out = out[out["Sektor"] == sektor]
    return out.reset_index(drop=True)


# =============================================================================
# Sidebar — navigasi & pengaturan global
# =============================================================================
st.sidebar.title("📈 SPK Saham Undervalued")
st.sidebar.caption("Metode TOPSIS · Kriteria Graham & Lynch")

page = st.sidebar.radio(
    "Navigasi",
    [
        "1. Scraping Data",
        "2. Input & Konfigurasi",
        "3. Hasil Perangkingan",
        "4. Detail Saham",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Template Excel")
st.sidebar.caption("Unduh template, isi data Anda, lalu upload kembali.")

tmpl_bytes = load_template_bytes()
if tmpl_bytes is not None:
    st.sidebar.download_button(
        "⬇️ Unduh template (.xlsx)",
        data=tmpl_bytes,
        file_name="template_input_saham.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
else:
    st.sidebar.warning("File template tidak ditemukan di folder aplikasi.")

st.sidebar.markdown("### 📤 Upload data")
uploaded = st.sidebar.file_uploader(
    "Pilih file .xlsx atau .csv",
    type=["xlsx", "xlsm", "csv"],
    help="Format kolom wajib: Tahun, Ticker, Nama, PER, PBV, DER, ROE, EPS, "
         "Current Ratio, Net Profit Margin, PEG Ratio",
)

try:
    if uploaded:
        df_all = load_data(uploaded=uploaded, filename=uploaded.name)
        st.sidebar.success(f"✅ {uploaded.name} berhasil dimuat ({len(df_all)} baris).")
    elif "scraped_df" in st.session_state and st.session_state["scraped_df"] is not None:
        df_all = st.session_state["scraped_df"]
        st.sidebar.success(f"✅ Menggunakan hasil scraping ({len(df_all)} emiten).")
    else:
        df_all = load_data()
        st.sidebar.info(
            "Menggunakan data contoh bawaan. Unduh template di atas atau jalankan "
            "scraper di halaman **1. Scraping Data** untuk pakai data sendiri."
        )
except Exception as exc:  # noqa: BLE001
    st.error(f"Gagal memuat data: {exc}")
    st.stop()


# =============================================================================
# Halaman 2 — Input & Konfigurasi
# =============================================================================
if "Input" in page:
    st.title("Input & Konfigurasi")
    st.markdown(
        "Aplikasi ini melakukan **screening saham undervalued** pada sektor "
        "*basic material* di Bursa Efek Indonesia menggunakan metode **TOPSIS** "
        "dengan 8 rasio fundamental Graham-Lynch."
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Periode & Sektor")
        tahun = sorted(df_all["Tahun"].unique(), reverse=True)[0]
        # Daftar sektor IDX yang tersedia. Jika data hasil scraping punya kolom
        # "Sektor", dropdown ini akan memfilter; selain itu hanya informatif.
        has_sector_col = "Sektor" in df_all.columns
        if has_sector_col:
            sektor_options = ["(Semua)"] + sorted(df_all["Sektor"].dropna().unique())
            sektor = st.selectbox("Sektor", sektor_options)
        else:
            sektor = st.selectbox(
                "Sektor (data saat ini)",
                list(SECTORS.keys()),
                index=0,  # default ke Basic Materials
                disabled=True,
                help="Aktif setelah Anda menjalankan scraping di halaman 1.",
            )

        st.subheader("Pilih kriteria")
        chosen = st.multiselect(
            "Kriteria yang dipakai",
            CRITERIA_LIST,
            default=CRITERIA_LIST,
        )

    with col2:
        st.subheader("Atur bobot tiap kriteria")
        st.caption(
            "🔒 Default semua bobot = **0**. "
            "Total bobot dijaga tidak melebihi **1.00**: jika slider digeser sampai "
            "total > 1.00, seluruh bobot otomatis di-rescale proporsional. "
            "Gunakan tombol di bawah untuk pengaturan cepat."
        )

        # -----------------------------------------------------------------
        # PENTING: inisialisasi nilai slider HARUS dilakukan SEBELUM
        # widget slider dirender. Setelah widget dibuat dengan key tertentu,
        # st.session_state[key] tidak boleh diubah lagi (kecuali via callback).
        # -----------------------------------------------------------------
        for c in CRITERIA_LIST:
            key = f"slider_{c}"
            if key not in st.session_state:
                st.session_state[key] = 0.0  # default = 0

        # Simpan daftar kriteria aktif agar callback dapat mengaksesnya
        st.session_state["_chosen_now"] = list(chosen)

        # -----------------------------------------------------------------
        # Callback-callback (dijalankan SEBELUM rerun berikutnya,
        # sehingga aman memodifikasi session_state milik widget).
        # -----------------------------------------------------------------
        def _rebalance_on_overflow() -> None:
            """Dipanggil setiap kali slider berubah.
            Rescale proporsional jika total > 1.00."""
            ch = st.session_state.get("_chosen_now", [])
            if not ch:
                return
            total = sum(st.session_state.get(f"slider_{c}", 0.0) for c in ch)
            if total > 1.0 + 1e-9:
                scale = 1.0 / total
                for c in ch:
                    st.session_state[f"slider_{c}"] = round(
                        st.session_state[f"slider_{c}"] * scale, 4
                    )

        def _reset_to_zero() -> None:
            """Set semua slider kriteria aktif ke 0."""
            for c in st.session_state.get("_chosen_now", []):
                st.session_state[f"slider_{c}"] = 0.0

        def _reset_to_equal() -> None:
            """Set semua slider kriteria aktif ke 1/n."""
            ch = st.session_state.get("_chosen_now", [])
            n = len(ch)
            if n > 0:
                equal = round(1.0 / n, 4)
                for c in ch:
                    st.session_state[f"slider_{c}"] = equal

        # -----------------------------------------------------------------
        # Render slider — dua dimensi pengelompokan:
        #   Kolom  : Revenue (kiri)   | Harga Saham (kanan)
        #   Subgrup: Benefit           | Cost
        # -----------------------------------------------------------------
        def _render_slider(c):
            w = st.slider(
                f"{c}",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                key=f"slider_{c}",
                on_change=_rebalance_on_overflow,
            )
            weights[c] = w

        weights = {}
        if not chosen:
            st.warning("Pilih minimal satu kriteria di sebelah kiri.")
        else:
            revenue_list = [c for c in chosen if c in REVENUE_BASED]
            price_list   = [c for c in chosen if c in PRICE_BASED]

            col_rev, col_price = st.columns(2)

            with col_rev:
                st.markdown("##### Revenue")
                rev_benefit = [c for c in revenue_list if CRITERIA_TYPES[c] == "benefit"]
                rev_cost    = [c for c in revenue_list if CRITERIA_TYPES[c] == "cost"]

                if rev_benefit:
                    st.markdown("**🟢 Benefit**")
                    for c in rev_benefit:
                        _render_slider(c)
                if rev_cost:
                    st.markdown("**🔴 Cost**")
                    for c in rev_cost:
                        _render_slider(c)

            with col_price:
                st.markdown("##### Harga Saham")
                price_benefit = [c for c in price_list if CRITERIA_TYPES[c] == "benefit"]
                price_cost    = [c for c in price_list if CRITERIA_TYPES[c] == "cost"]

                if price_benefit:
                    st.markdown("**🟢 Benefit**")
                    for c in price_benefit:
                        _render_slider(c)
                if price_cost:
                    st.markdown("**🔴 Cost**")
                    for c in price_cost:
                        _render_slider(c)

        # -----------------------------------------------------------------
        # Indikator total bobot + tombol pengaturan cepat.
        # -----------------------------------------------------------------
        if chosen:
            total = sum(weights.values())
            st.progress(min(total, 1.0), text=f"Total bobot: {total:.3f} / 1.000")
            if abs(total - 1.0) < 1e-3:
                st.success("✓ Total bobot tepat = 1.000")
            elif total > 1.0:
                st.error(
                    f"✗ Total {total:.3f} melebihi 1.00 — slider akan otomatis "
                    "di-rescale pada interaksi berikutnya."
                )
            elif total == 0:
                st.warning(
                    "Semua bobot masih 0. Geser slider atau klik **Bagi rata** "
                    "untuk memberikan bobot."
                )
            else:
                st.info(
                    f"Total {total:.3f} masih di bawah 1.00 — kekurangan akan "
                    "dinormalisasi otomatis saat kalkulasi TOPSIS."
                )

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                st.button(
                    "⚖️ Bagi rata (1/n)",
                    on_click=_reset_to_equal,
                    use_container_width=True,
                    help="Set semua kriteria ke 1/n sehingga total tepat = 1.00",
                )
            with btn_col2:
                st.button(
                    "0️⃣ Reset ke nol",
                    on_click=_reset_to_zero,
                    use_container_width=True,
                    help="Set semua bobot kembali ke 0",
                )

    # Simpan ke session_state untuk dipakai halaman lain
    st.session_state["tahun"] = tahun
    st.session_state["sektor"] = sektor
    st.session_state["chosen"] = chosen
    st.session_state["weights"] = weights

    st.markdown("---")
    st.subheader("Pratinjau data periode terpilih")
    df_year = filter_by_year_sector(df_all, tahun, sektor)
    st.dataframe(df_year.drop(columns=["Tahun"], errors="ignore"), use_container_width=True)
    label = f"{sektor}" if sektor not in ("(Semua)", None) and "Sektor" in df_all.columns else "semua sektor"
    st.info(
        f"Total {len(df_year)} emiten tersedia. "
        "Pindah ke halaman **3. Hasil Perangkingan** untuk menjalankan TOPSIS."
    )


# =============================================================================
# Halaman 3 — Hasil Perangkingan
# =============================================================================
elif "Hasil" in page:
    st.title("Hasil Perangkingan TOPSIS")

    tahun = st.session_state.get("tahun", df_all["Tahun"].max())
    sektor = st.session_state.get("sektor", None)
    chosen = st.session_state.get("chosen", CRITERIA_LIST)
    weights = st.session_state.get("weights", DEFAULT_WEIGHTS)

    if not chosen:
        st.warning("Silakan pilih minimal satu kriteria di halaman Input.")
        st.stop()

    if sum(weights.values()) <= 0:
        st.warning(
            "Semua bobot kriteria masih 0. Kembali ke halaman **Input & Konfigurasi**, "
            "lalu geser slider atau klik **Bagi rata** untuk memberikan bobot."
        )
        st.stop()

    df_year = filter_by_year_sector(df_all, tahun, sektor)

    try:
        result = run_topsis(
            df_year, criteria=chosen, weights=weights, types=CRITERIA_TYPES
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Gagal menjalankan TOPSIS: {exc}")
        st.stop()

    # Gabungkan dengan nama emiten
    result = result.merge(df_year[["Ticker", "Nama"]], on="Ticker", how="left")
    cols = ["Ranking", "Ticker", "Nama", "D+", "D-", "Preferensi (C)"]
    result = result[cols]

    st.subheader("Ranking saham")
    st.caption(
        f"Bobot aktif: {', '.join(f'{c}={weights[c]:.2f}' for c in chosen)}"
    )

    st.dataframe(
        result.style.format({"D+": "{:.4f}", "D-": "{:.4f}", "Preferensi (C)": "{:.4f}"}),
        use_container_width=True,
        hide_index=True,
    )

    # Visualisasi
    st.subheader("Visualisasi skor preferensi")
    top_n = st.slider("Tampilkan Top-N", 3, len(result), min(10, len(result)))
    chart_df = result.head(top_n).set_index("Ticker")["Preferensi (C)"]
    st.bar_chart(chart_df, color=KEU["navy"])

    # Heatmap nilai kriteria
    st.subheader("Heatmap nilai kriteria (Top-N)")
    top_tickers = result.head(top_n)["Ticker"].tolist()
    heat = (
        df_year[df_year["Ticker"].isin(top_tickers)]
        .set_index("Ticker")[chosen]
    )
    # Normalisasi 0-1 per kolom agar warnanya komparabel
    heat_norm = (heat - heat.min()) / (heat.max() - heat.min() + 1e-9)
    # Colormap kustom Kemenkeu: gold-light -> gold -> navy
    from matplotlib.colors import LinearSegmentedColormap
    keu_cmap = LinearSegmentedColormap.from_list(
        "keu", [KEU["gold_light"], KEU["gold"], KEU["blue"], KEU["navy"]]
    )
    st.dataframe(
        heat_norm.style.background_gradient(cmap=keu_cmap, axis=None).format("{:.2f}"),
        use_container_width=True,
    )

    # Ekspor
    st.markdown("---")
    st.subheader("Ekspor hasil")
    csv_bytes = df_to_csv_bytes(result)
    st.download_button(
        "⬇️ Unduh ranking (CSV)",
        data=csv_bytes,
        file_name=f"ranking_topsis_{tahun}.csv",
        mime="text/csv",
    )


# =============================================================================
# Halaman 4 — Detail Saham
# =============================================================================
elif "Detail" in page:
    st.title("Detail Saham")

    tahun = st.session_state.get("tahun", df_all["Tahun"].max())
    sektor = st.session_state.get("sektor", None)
    df_year = filter_by_year_sector(df_all, tahun, sektor)

    ticker = st.selectbox(
        "Pilih saham",
        df_year["Ticker"].tolist(),
    )
    row = df_year[df_year["Ticker"] == ticker].iloc[0]

    st.subheader(f"{row['Ticker']} — {row['Nama']}")

    # Ambang batas referensi Graham-Lynch (untuk evaluasi cepat)
    thresholds = {
        "PER": ("≤ 15", lambda x: x <= 15),
        "PBV": ("≤ 1.5", lambda x: x <= 1.5),
        "DER": ("≤ 1.0", lambda x: x <= 1.0),
        "ROE": ("≥ 10%", lambda x: x >= 10),
        "EPS": ("> 0", lambda x: x > 0),
        "Current Ratio": ("≥ 2.0", lambda x: x >= 2.0),
        "Net Profit Margin": ("≥ 10%", lambda x: x >= 10),
        "PEG Ratio": ("≤ 1.0", lambda x: x <= 1.0),
    }

    detail = []
    for c, (ambang, fn) in thresholds.items():
        nilai = row[c]
        status = "✅ Memenuhi" if fn(nilai) else "❌ Tidak"
        detail.append({"Kriteria": c, "Nilai": nilai, "Ambang Graham-Lynch": ambang, "Status": status})

    st.dataframe(pd.DataFrame(detail), use_container_width=True, hide_index=True)

    # Tren historis
    hist = df_all[df_all["Ticker"] == ticker].sort_values("Tahun")
    if len(hist) > 1:
        st.subheader("Tren historis rasio fundamental")
        # Warna garis bergantian: navy, gold, blue, gold-dark, blue-light, ...
        line_colors = [
            KEU["navy"], KEU["gold"], KEU["blue"], KEU["gold_dark"],
            KEU["blue_light"], KEU["blue_dark"], KEU["gold_light"], KEU["blue"],
        ]
        st.line_chart(hist.set_index("Tahun")[CRITERIA_LIST], color=line_colors)

    st.caption(
        "Ambang batas di atas adalah penyederhanaan dari rekomendasi klasik Graham & Lynch. "
        "Skor TOPSIS pada halaman *Hasil Perangkingan* menggabungkan seluruh kriteria secara bersamaan."
    )


# =============================================================================
# Halaman 1 — Scraping Data
# =============================================================================
else:
    st.title("📡 Scraping Data dari Yahoo Finance")
    st.markdown(
        "Ambil rasio fundamental terbaru emiten BEI langsung dari Yahoo Finance via "
        "`yfinance`. Pilih satu atau lebih sektor IDX, lalu sesuaikan ticker. "
        "Hasil dapat langsung dipakai sebagai data analisis."
    )

    # ---------- Pilih sektor ----------
    sektor_pilihan = st.multiselect(
        "🏷️ Sektor IDX-IC",
        options=list(SECTORS.keys()),
        default=["Basic Materials"],
        help="Pilih satu atau lebih dari 11 sektor IDX. Daftar ticker akan otomatis diisi.",
    )

    # Susun daftar ticker default dari sektor terpilih + map ticker → sektor
    default_jk = []
    ticker_to_sector = {}
    for s in sektor_pilihan:
        for t in SECTORS[s]:
            if t not in default_jk:
                default_jk.append(t)
            ticker_to_sector[t.replace(".JK", "")] = s
    default_plain = [t.replace(".JK", "") for t in default_jk]

    # ---------- Konfigurasi scraping ----------
    cfg_col1, cfg_col2 = st.columns([2, 1])

    with cfg_col1:
        st.subheader("Pilih emiten")
        selected = st.multiselect(
            f"Ticker yang akan di-scrape (tanpa .JK) — {len(default_plain)} ticker tersedia",
            options=default_plain,
            default=default_plain,
            help="Pilih ticker yang akan diambil rasionya. Bisa juga tambah ticker custom di bawah.",
        )
        extra_text = st.text_input(
            "Tambah ticker custom (pisahkan dengan koma)",
            value="",
            placeholder="contoh: HRUM, BUMI, ADRO",
        )
        extra = [t.strip().upper() for t in extra_text.split(",") if t.strip()]
        ticker_list = list(dict.fromkeys(selected + extra))  # gabung, dedup
        ticker_list_jk = [f"{t}.JK" for t in ticker_list]

    with cfg_col2:
        st.subheader("Pengaturan")
        sleep = st.slider(
            "Jeda antar request (detik)", 0.0, 2.0, 0.5, 0.1,
            help="Jeda lebih besar = lebih aman terhadap rate-limit Yahoo Finance, tapi lebih lambat.",
        )
        tahun_label = int(pd.Timestamp.today().year)
        mode_strict = st.toggle(
            "Mode strict (buang baris tidak lengkap)",
            value=False,
            help="Jika nyala: emiten dengan rasio kurang dari 8 akan dibuang. "
                 "Jika mati (default): rasio yang hilang diisi median agar SEMUA ticker tetap dipakai.",
        )
        max_missing = st.slider(
            "Maks. rasio hilang per ticker",
            0, 7, 5,
            help="Ticker yang punya lebih dari N rasio hilang akan dibuang. "
                 "Default 5 berarti minimal 3 dari 8 rasio harus ada.",
            disabled=mode_strict,
        )

    st.caption(f"Akan men-scrape **{len(ticker_list_jk)} ticker**.")

    # ---------- Tombol jalankan ----------
    if st.button("🚀 Jalankan Scraper", type="primary", use_container_width=True):
        if not ticker_list_jk:
            st.error("Belum ada ticker terpilih.")
        else:
            progress = st.progress(0.0, text="Memulai...")
            log_placeholder = st.empty()
            logs = []

            def _cb(i, total, ticker, status):
                pct = i / total
                progress.progress(pct, text=f"({i}/{total}) {ticker} — {status}")
                logs.append(f"[{i}/{total}] {ticker}: {status}")
                # Tampilkan 8 baris log terakhir
                log_placeholder.code("\n".join(logs[-8:]))

            try:
                raw = scrape_basic_material(ticker_list_jk, sleep=sleep, progress_callback=_cb)
                clean = preprocess(
                    raw,
                    impute_missing=not mode_strict,
                    max_missing_per_row=0 if mode_strict else max_missing,
                )
                if len(clean) > 0:
                    clean.insert(0, "Tahun", int(tahun_label))
                    # Tambahkan kolom Sektor berdasarkan ticker → sektor map.
                    # Ticker custom (tidak ada di map) diberi label "Lainnya".
                    clean.insert(
                        3,
                        "Sektor",
                        clean["Ticker"].map(lambda t: ticker_to_sector.get(t, "Lainnya")),
                    )
                progress.progress(1.0, text="Selesai.")

                if len(clean) == 0:
                    st.error(
                        "Tidak ada data yang valid setelah preprocessing. "
                        "Coba matikan **Mode strict** atau naikkan **Maks. rasio hilang** "
                        "agar lebih banyak ticker dipertahankan."
                    )
                else:
                    # Hitung berapa rasio yang diimputasi
                    n_input  = len(raw)
                    n_output = len(clean)
                    msg = f"Berhasil meng-scrape **{n_output} dari {n_input}** emiten."
                    if not mode_strict:
                        cols_present = [c for c in SCRAPER_CRITERIA_COLS if c in raw.columns]
                        n_imputed = int(raw[cols_present].isna().sum().sum()) if cols_present else 0
                        if n_imputed > 0:
                            msg += f" {n_imputed} nilai rasio yang hilang diisi median kolom."
                    st.success(msg)
                    st.session_state["scraped_df"] = clean
                    st.session_state["scraped_raw"] = raw

            except ImportError as exc:
                st.error(
                    f"Library yfinance belum terpasang.\n\n"
                    f"Buka Command Prompt di folder aplikasi, lalu jalankan:\n"
                    f"`pip install yfinance`\n\n"
                    f"Detail: {exc}"
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Scraping gagal: {exc}")

    # ---------- Tampilkan hasil ----------
    scraped = st.session_state.get("scraped_df")
    if scraped is not None and len(scraped) > 0:
        st.divider()
        st.subheader("Hasil Scraping")
        st.dataframe(scraped.drop(columns=["Tahun"], errors="ignore"), use_container_width=True, hide_index=True)

        # Ringkasan
        col_a, col_b = st.columns(2)
        col_a.metric("Emiten valid", len(scraped))
        col_b.metric("Kolom rasio", 8)
        # col_c.metric("Tahun label", int(scraped["Tahun"].iloc[0]))  # disembunyikan

        # Tombol ekspor
        st.subheader("Ekspor")
        exp_col1, exp_col2, exp_col3 = st.columns(3)

        csv_bytes = df_to_csv_bytes(scraped)
        exp_col1.download_button(
            "⬇️ Unduh CSV",
            data=csv_bytes,
            file_name=f"scraped_basic_material_{int(scraped['Tahun'].iloc[0])}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # Excel
        xlsx_buf = io.BytesIO()
        with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
            scraped.to_excel(writer, sheet_name="Data Saham", index=False)
        exp_col2.download_button(
            "⬇️ Unduh Excel",
            data=xlsx_buf.getvalue(),
            file_name=f"scraped_basic_material_{int(scraped['Tahun'].iloc[0])}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        if exp_col3.button("🗑️ Hapus hasil", use_container_width=True):
            st.session_state["scraped_df"] = None
            st.session_state["scraped_raw"] = None
            st.rerun()

        st.info(
            "💡 Hasil scraping ini sudah otomatis dipakai sebagai data analisis. "
            "Buka halaman **2. Input & Konfigurasi** atau **3. Hasil Perangkingan** "
            "untuk menjalankan TOPSIS dengan data baru ini."
        )

    # ---------- Catatan ----------
    with st.expander("ℹ️ Catatan penting tentang scraping"):
        st.markdown(
            "- **Snapshot terkini**: `yfinance` menyajikan rasio terkini, bukan historis "
            "per tahun. Untuk data 2021–2024 (sesuai cakupan skripsi), Anda perlu mengulang "
            "scraping di waktu berbeda atau melengkapi dari laporan tahunan resmi BEI.\n"
            "- **Konversi unit otomatis**: `ROE` dan `Net Profit Margin` dikonversi dari "
            "pecahan ke persentase (mis. 0.18 → 18.0).\n"
            "- **Baris dengan nilai hilang dibuang**: ticker yang tidak memiliki salah satu "
            "dari 8 rasio Graham-Lynch akan otomatis di-skip.\n"
            "- **Sumber data**: Yahoo Finance via library `yfinance`.\n"
            "- **Rate-limit**: jika banyak request gagal, naikkan jeda antar request "
            "ke 1.0–2.0 detik."
        )
