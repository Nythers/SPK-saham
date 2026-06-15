"""
Modul Scraping Data Laporan Keuangan
=====================================
Mengambil 8 rasio fundamental untuk saham sektor basic material BEI
menggunakan yfinance, dengan fallback key dan kalkulasi manual untuk
rasio yang hilang.

Rasio yang diekstraksi:
    PER, PBV, DER, ROE, EPS, Current Ratio, Net Profit Margin, PEG Ratio
"""

from __future__ import annotations

from logging import info
import time
import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np


# =============================================================================
# Daftar emiten per sektor IDX-IC (Indonesia Stock Exchange — Industrial
# Classification, berlaku sejak 25 Januari 2021).
# Sumber: idx.co.id. Daftar bersifat contoh, dapat diperluas sesuai kebutuhan.
# =============================================================================
SECTORS: dict[str, list[str]] = {
    "Basic Materials": [
        "AKPI.JK","ALDO.JK","ALKA.JK","ALMI.JK","ANTM.JK","APLI.JK","BAJA.JK","BMSR.JK","BRMS.JK","BRNA.JK","BRPT.JK","BTON.JK","CITA.JK","CLPI.JK","CTBN.JK","DKFT.JK","DPNS.JK","EKAD.JK","ESSA.JK","ETWA.JK","FASW.JK","FPNI.JK","GDST.JK","IGAR.JK","INAI.JK","INCI.JK","INCO.JK","INKP.JK","INRU.JK","INTD.JK","INTP.JK","IPOL.JK","ISSP.JK","KBRI.JK","KDSI.JK","KRAS.JK","LMSH.JK","LTLS.JK","MDKA.JK","NIKL.JK","OKAS.JK","PICO.JK","PSAB.JK","SIMA.JK","SMBR.JK","SMCB.JK","SMGR.JK","SPMA.JK","SQMI.JK","SRSN.JK","SULI.JK","TALF.JK","TBMS.JK","TINS.JK","TIRT.JK","TKIM.JK","TPIA.JK","TRST.JK","UNIC.JK","WTON.JK","YPAS.JK","INCF.JK","WSBP.JK","KMTR.JK","MDKI.JK","ZINC.JK","PBID.JK","TDPM.JK","SWAT.JK","MOLI.JK","HKMU.JK","KAYU.JK","SMKL.JK","GGRP.JK","OPMS.JK","PURE.JK","ESIP.JK","IFSH.JK","IFII.JK","SAMF.JK","EPAC.JK","BEBS.JK","NPGF.JK","ARCI.JK","NICL.JK","SBMA.JK","CMNT.JK","OBMD.JK","AVIA.JK","CHEM.JK","KKES.JK","PDPP.JK","FWCT.JK","PACK.JK","AMMN.JK","PPRI.JK","SMGA.JK","SOLA.JK","BATR.JK","BLES.JK","PTMR.JK","DAAZ.JK","DGWG.JK","MINE.JK","ASPR.JK","AYLS.JK","NCKL.JK","MBMA.JK","NICE.JK","SMLE.JK","EMAS.JK","ADMG.JK","AGII.JK",
    ],
    "Energy": [
        "ADRO.JK",  # Adaro Energy
        "PTBA.JK",  # Bukit Asam
        "ITMG.JK",  # Indo Tambangraya Megah
        "HRUM.JK",  # Harum Energy
        "INDY.JK",  # Indika Energy
        "BYAN.JK",  # Bayan Resources
        "MEDC.JK",  # Medco Energi Internasional
        "ENRG.JK",  # Energi Mega Persada
        "BUMI.JK",  # Bumi Resources
        "DEWA.JK",  # Darma Henwa
        "ELSA.JK",  # Elnusa
        "AKRA.JK",  # AKR Corporindo
    ],
    "Industrials": [
        "ASII.JK",  # Astra International
        "UNTR.JK",  # United Tractors
        "IMAS.JK",  # Indomobil Sukses Internasional
        "SMSM.JK",  # Selamat Sempurna
        "AUTO.JK",  # Astra Otoparts
        "BRAM.JK",  # Indo Kordsa
        "PTPP.JK",  # PP (Persero)
        "WIKA.JK",  # Wijaya Karya
        "ADHI.JK",  # Adhi Karya
        "WSKT.JK",  # Waskita Karya
        "JKON.JK",  # Jaya Konstruksi Manggala Pratama
        "TOTL.JK",  # Total Bangun Persada
    ],
    "Consumer Non-Cyclicals": [
        "UNVR.JK",  # Unilever Indonesia
        "INDF.JK",  # Indofood Sukses Makmur
        "ICBP.JK",  # Indofood CBP Sukses Makmur
        "HMSP.JK",  # H.M. Sampoerna
        "GGRM.JK",  # Gudang Garam
        "MYOR.JK",  # Mayora Indah
        "ULTJ.JK",  # Ultrajaya Milk Industry
        "ROTI.JK",  # Nippon Indosari Corpindo
        "SIDO.JK",  # Industri Jamu & Farmasi Sido Muncul
        "TBLA.JK",  # Tunas Baru Lampung
        "AALI.JK",  # Astra Agro Lestari
        "LSIP.JK",  # PP London Sumatra Indonesia
    ],
    "Consumer Cyclicals": [
        "ACES.JK",  # Ace Hardware Indonesia
        "MAPI.JK",  # Mitra Adiperkasa
        "ERAA.JK",  # Erajaya Swasembada
        "LPPF.JK",  # Matahari Department Store
        "AMRT.JK",  # Sumber Alfaria Trijaya (Alfamart)
        "RALS.JK",  # Ramayana Lestari Sentosa
        "MNCN.JK",  # Media Nusantara Citra
        "SCMA.JK",  # Surya Citra Media
        "MAPA.JK",  # MAP Aktif Adiperkasa
        "PZZA.JK",  # Sarimelati Kencana (Pizza Hut)
    ],
    "Healthcare": [
        "KLBF.JK",  # Kalbe Farma
        "KAEF.JK",  # Kimia Farma
        "INAF.JK",  # Indofarma
        "PEHA.JK",  # Phapros
        "SILO.JK",  # Siloam International Hospitals
        "HEAL.JK",  # Medikaloka Hermina
        "MIKA.JK",  # Mitra Keluarga Karyasehat
        "PRDA.JK",  # Prodia Widyahusada
        "SOHO.JK",  # Soho Global Health
        "DVLA.JK",  # Darya-Varia Laboratoria
    ],
    "Financials": [
        "BBCA.JK",  # Bank Central Asia
        "BMRI.JK",  # Bank Mandiri
        "BBRI.JK",  # Bank Rakyat Indonesia
        "BBNI.JK",  # Bank Negara Indonesia
        "BRIS.JK",  # Bank Syariah Indonesia
        "BTPS.JK",  # Bank BTPN Syariah
        "ARTO.JK",  # Bank Jago
        "BNGA.JK",  # Bank CIMB Niaga
        "BDMN.JK",  # Bank Danamon Indonesia
        "BBTN.JK",  # Bank Tabungan Negara
        "PNBN.JK",  # Bank Pan Indonesia
        "MEGA.JK",  # Bank Mega
    ],
    "Properties & Real Estate": [
        "BSDE.JK",  # Bumi Serpong Damai
        "SMRA.JK",  # Summarecon Agung
        "PWON.JK",  # Pakuwon Jati
        "LPKR.JK",  # Lippo Karawaci
        "CTRA.JK",  # Ciputra Development
        "ASRI.JK",  # Alam Sutera Realty
        "APLN.JK",  # Agung Podomoro Land
        "DUTI.JK",  # Duta Pertiwi
        "KIJA.JK",  # Kawasan Industri Jababeka
        "MDLN.JK",  # Modernland Realty
        "DILD.JK",  # Intiland Development
    ],
    "Technology": [
        "GOTO.JK",  # GoTo Gojek Tokopedia
        "BUKA.JK",  # Bukalapak.com
        "EMTK.JK",  # Elang Mahkota Teknologi
        "WIRG.JK",  # WIR ASIA
        "DCII.JK",  # DCI Indonesia
        "DMMX.JK",  # Digital Mediatama Maxima
        "MTDL.JK",  # Metrodata Electronics
        "NETV.JK",  # Net Visi Media
        "MLPT.JK",  # Multipolar Technology
    ],
    "Infrastructure": [
        "TLKM.JK",  # Telkom Indonesia
        "EXCL.JK",  # XL Axiata
        "ISAT.JK",  # Indosat
        "FREN.JK",  # Smartfren Telecom
        "TOWR.JK",  # Sarana Menara Nusantara
        "TBIG.JK",  # Tower Bersama Infrastructure
        "MTEL.JK",  # Dayamitra Telekomunikasi
        "JSMR.JK",  # Jasa Marga
        "PGAS.JK",  # Perusahaan Gas Negara
        "META.JK",  # Nusantara Infrastructure
    ],
    "Transportation & Logistic": [
        "GIAA.JK",  # Garuda Indonesia
        "BIRD.JK",  # Blue Bird
        "ASSA.JK",  # Adi Sarana Armada
        "SMDR.JK",  # Samudera Indonesia
        "TMAS.JK",  # Pelayaran Tempuran Emas
        "IPCC.JK",  # Indonesia Kendaraan Terminal
        "WEHA.JK",  # WEHA Transportasi Indonesia
        "TRUK.JK",  # Guna Timur Raya
    ],
}

# Backward compatibility — kode lain mungkin masih mengacu pada nama lama
BASIC_MATERIAL_TICKERS = SECTORS["Basic Materials"]


def get_tickers_by_sector(sector: str) -> list[str]:
    """Ambil daftar ticker untuk sektor tertentu. KeyError jika tidak ada."""
    return SECTORS[sector]

# Kolom rasio yang dipakai TOPSIS
CRITERIA_COLS = [
    "PER", "PBV", "DER", "ROE", "EPS",
    "Current Ratio", "Net Profit Margin", "PEG Ratio",
]


def _get(info: dict, *keys, default=None):
    """Ambil nilai pertama yang tidak None dari beberapa key fallback."""
    for k in keys:
        v = info.get(k)
        if v is not None:
            return v
    return default


def _safe_divide(a, b):
    """Pembagian aman, kembalikan None jika denominator nol/None/NaN."""
    try:
        if a is None or b is None or b == 0:
            return None
        if pd.isna(a) or pd.isna(b):
            return None
        return float(a) / float(b)
    except Exception:  # noqa: BLE001
        return None


def _ratio_from_financials(yf_ticker) -> dict:
    """Hitung rasio yang hilang dari laporan keuangan resmi.

    Berguna saat .info tidak menyediakan rasio tertentu.
    """
    result = {}
    try:
        bs = yf_ticker.balance_sheet
        fs = yf_ticker.financials  # income statement
        info = yf_ticker.info
        currency = info.get("financialCurrency")
        idr_rate = yf.Ticker("IDR=X").info.get("regularMarketPrice")

        if bs is None or fs is None or bs.empty or fs.empty:
            return result

        col = bs.columns[0]  # periode terbaru

        def cell(df, *names):
            for n in names:
                if n in df.index:
                    col = df.columns[0]  # periode terbaru
                    val = df.loc[n, col] if col in df.columns else None
                    if pd.notna(val):
                        return float(val)
            return None
        current_price = (_get(info, "currentPrice", "regularMarketPrice", "previousClose")) or yf_ticker.fast_info.get("lastPrice")
        shares_outstanding = yf_ticker.info.get("sharesOutstanding")
        total_debt = cell(bs, "Total Debt", "Long Term Debt")
        equity = cell(bs, "Stockholders Equity", "Total Equity Gross Minority Interest", "Common Stock Equity")
        curr_assets = cell(bs, "Current Assets", "Total Current Assets","Current Assets Total")
        curr_liab = cell(bs, "Current Liabilities", "Total Current Liabilities", "Current Liabilities Total")
        net_income = cell(fs, "Net Income", "Net Income Common Stockholders")
        revenue = cell(fs, "Total Revenue", "Operating Revenue")

        if currency == "USD" and idr_rate is not None:
            total_debt *= idr_rate
            equity *= idr_rate
            curr_assets *= idr_rate
            curr_liab *= idr_rate
            net_income *= idr_rate
            revenue *= idr_rate
        bvps = _safe_divide(equity, shares_outstanding) if shares_outstanding is not None and shares_outstanding > 0 else None
        
    
        # PBV
        v = _safe_divide(current_price, bvps)
        if v is not None:
            result["PBV"] = v
        # DER
        v = _safe_divide(total_debt, equity)
        if v is not None:
            result["DER"] = v
        # ROE (sebagai pecahan, akan dikonversi ke % di preprocess)
        v = _safe_divide(net_income, equity)
        if v is not None:
            result["ROE"] = v
        # Current Ratio
        v = _safe_divide(curr_assets, curr_liab)
        if v is not None:
            result["Current Ratio"] = v
        # Net Profit Margin (pecahan)
        v = _safe_divide(net_income, revenue)
        if v is not None:
            result["Net Profit Margin"] = v
    except Exception:  # noqa: BLE001
        pass
    return result


def fetch_one_ticker(ticker: str) -> dict | None:
    """Ambil rasio fundamental satu ticker via yfinance dengan fallback.

    Strategi pengambilan:
    1. Coba beberapa key di .info untuk tiap rasio.
    2. Bila ada yang hilang, hitung dari .balance_sheet dan .financials.
    3. Untuk PEG, hitung manual dari PER / earnings growth jika hilang.

    Return dict berisi 8 rasio + diagnostik per ticker.
    """
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError(
            "Library yfinance belum terpasang. Jalankan: pip install yfinance"
        ) from exc

    yt = yf.Ticker(ticker)
    try:
        info = yt.info or {}
    except Exception:  # noqa: BLE001
        info = {}

    # Ambil dari .info dengan fallback
    per = _get(info, "trailingPE", "forwardPE")
    pbv = None
    der = _get(info, "debtToEquity")
    roe = _get(info, "returnOnEquity")
    eps = _get(info, "trailingEps", "forwardEps")
    cr  = _get(info, "currentRatio", "quickRatio")
    npm = _get(info, "profitMargins", "grossMargins")
    peg = _get(info, "trailingPegRatio", "pegRatio")

    # Jika ada yang masih kosong, coba hitung dari laporan keuangan
    missing = [k for k, v in {
        "PBV": pbv, "DER": der, "ROE": roe, "Current Ratio": cr, "Net Profit Margin": npm
    }.items() if v is None]
    if missing:
        from_fs = _ratio_from_financials(yt)
        pbv = pbv if pbv is not None else from_fs.get("PBV")
        der = der if der is not None else from_fs.get("DER")
        roe = roe if roe is not None else from_fs.get("ROE")
        cr  = cr  if cr  is not None else from_fs.get("Current Ratio")
        npm = npm if npm is not None else from_fs.get("Net Profit Margin")

    # PEG manual: PER / (earnings growth dalam persen)
    if peg is None and per is not None:
        eg = _get(info, "earningsGrowth", "earningsQuarterlyGrowth", "revenueGrowth")
        if eg is not None and eg > 0:
            peg = float(per) / (float(eg) * 100)

    # DER yfinance kadang dalam persen (75 berarti 0.75)
    if der is not None and abs(float(der)) > 5:
        der = float(der) / 100

    row = {
        "Ticker": ticker.replace(".JK", ""),
        "Nama": info.get("longName") or info.get("shortName") or ticker,
        "PER": per,
        "PBV": pbv,
        "DER": der,
        "ROE": roe,
        "EPS": eps,
        "Current Ratio": cr,
        "Net Profit Margin": npm,
        "PEG Ratio": peg,
    }
    return row


def scrape_basic_material(tickers: list[str] | None = None,
                          sleep: float = 0.5,
                          progress_callback=None) -> pd.DataFrame:
    """Scrape seluruh emiten basic material, kembalikan DataFrame.

    progress_callback(i, total, ticker, status_str) dipanggil tiap ticker selesai.
    Status_str menjelaskan: "OK (n rasio)", "Sebagian (n/8)", atau "Gagal: ...".
    """
    tickers = tickers or BASIC_MATERIAL_TICKERS
    total = len(tickers)
    rows = []
    for i, t in enumerate(tickers, start=1):
        try:
            row = fetch_one_ticker(t)
            if row is None:
                status = "Tidak ada data"
            else:
                filled = sum(1 for c in CRITERIA_COLS if row.get(c) is not None)
                if filled == len(CRITERIA_COLS):
                    status = f"OK ({filled}/{len(CRITERIA_COLS)} rasio)"
                else:
                    status = f"Sebagian ({filled}/{len(CRITERIA_COLS)} rasio)"
                rows.append(row)
        except Exception as exc:  # noqa: BLE001
            status = f"Gagal: {exc}"
        if progress_callback is not None:
            try:
                progress_callback(i, total, t, status)
            except Exception:  # noqa: BLE001
                pass
        time.sleep(sleep)
    return pd.DataFrame(rows)


def preprocess(df: pd.DataFrame,
               impute_missing: bool = True,
               max_missing_per_row: int = 5) -> pd.DataFrame:
    """Bersihkan data hasil scraping.

    Args:
        df: DataFrame mentah dari scrape_basic_material.
        impute_missing: jika True, NaN diisi dengan median kolom.
            Jika False, baris dengan NaN dibuang (strict mode).
        max_missing_per_row: baris yang punya lebih dari N rasio kosong tetap dibuang.
            Default 5 dari 8 berarti minimal 3 rasio valid agar baris dipertahankan.

    Return DataFrame yang siap dipakai TOPSIS (semua kolom kriteria terisi).
    """
    if df is None or len(df) == 0:
        return df

    df = df.copy()

    # Konversi ROE & NPM dari pecahan ke persen (mis. 0.18 → 18.0)
    for col in ("ROE", "Net Profit Margin"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce") * 100

    # Pastikan semua kolom kriteria numerik
    for c in CRITERIA_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Buang baris dengan terlalu banyak missing
    available = [c for c in CRITERIA_COLS if c in df.columns]
    missing_per_row = df[available].isna().sum(axis=1)
    before = len(df)
    df = df[missing_per_row <= max_missing_per_row].reset_index(drop=True)
    dropped = before - len(df)
    if dropped > 0:
        print(f"[INFO] {dropped} baris dibuang (lebih dari {max_missing_per_row} rasio hilang).")

    if len(df) == 0:
        return df

    if impute_missing:
        # Isi missing dengan median per kolom
        for c in available:
            median = df[c].median()
            if pd.notna(median):
                df[c] = df[c].fillna(median)
            else:
                # Jika seluruh kolom kosong, isi dengan nilai default netral
                df[c] = df[c].fillna(0)
    else:
        # Strict: buang baris dengan NaN tersisa
        df = df.dropna(subset=available).reset_index(drop=True)

    return df


if __name__ == "__main__":
    print("Mengunduh data emiten basic material...")
    raw = scrape_basic_material()
    print(f"Hasil mentah: {len(raw)} baris")
    print(raw[["Ticker"] + CRITERIA_COLS].to_string(index=False))
    clean = preprocess(raw)
    out = "saham_basic_material.csv"
    clean.to_csv(out, index=False)
    print(f"\nTersimpan ke {out}. Total {len(clean)} emiten valid.")
