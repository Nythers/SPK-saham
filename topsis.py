"""
Modul TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)
untuk Sistem Pendukung Keputusan Pemilihan Saham Undervalued
berdasarkan kriteria Benjamin Graham dan Peter Lynch.

Tahapan TOPSIS:
1. Normalisasi matriks keputusan (vector normalization)
2. Pembobotan matriks ternormalisasi
3. Penentuan solusi ideal positif (A+) dan solusi ideal negatif (A-)
4. Perhitungan jarak Euclidean setiap alternatif ke A+ dan A-
5. Perhitungan nilai preferensi / closeness coefficient
"""

import numpy as np
import pandas as pd


# Tipe kriteria: "benefit" = makin besar makin baik, "cost" = makin kecil makin baik
# Mengacu pada kriteria Graham-Lynch:
#   PER (cost)            : nilai rendah berarti murah relatif terhadap laba
#   PBV (cost)            : nilai rendah berarti murah relatif terhadap ekuitas
#   DER (cost)            : utang lebih kecil lebih sehat
#   ROE (benefit)         : profitabilitas terhadap ekuitas
#   EPS (benefit)         : laba per saham
#   Current Ratio (benefit): likuiditas jangka pendek
#   Net Profit Margin (benefit): efisiensi laba bersih
#   PEG Ratio (cost)      : PER relatif terhadap pertumbuhan; rendah = murah
CRITERIA_TYPES = {
    "PER": "cost",
    "PBV": "cost",
    "DER": "cost",
    "ROE": "benefit",
    "EPS": "benefit",
    "Current Ratio": "benefit",
    "Net Profit Margin": "benefit",
    "PEG Ratio": "cost",
}


def normalize_matrix(matrix: np.ndarray) -> np.ndarray:
    """Tahap 1: Vector normalization.

    r_ij = x_ij / sqrt(sum_i(x_ij^2))
    """
    denom = np.sqrt(np.sum(matrix ** 2, axis=0))
    # Hindari pembagian dengan nol
    denom = np.where(denom == 0, 1e-12, denom)
    return matrix / denom


def weighted_matrix(norm_matrix: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Tahap 2: Matriks ternormalisasi terbobot.

    v_ij = w_j * r_ij
    """
    return norm_matrix * weights


def ideal_solutions(weighted: np.ndarray, criteria_types: list) -> tuple:
    """Tahap 3: Solusi ideal positif (A+) dan solusi ideal negatif (A-).

    Untuk kriteria benefit: A+ = max kolom, A- = min kolom
    Untuk kriteria cost  : A+ = min kolom, A- = max kolom
    """
    a_plus = np.zeros(weighted.shape[1])
    a_minus = np.zeros(weighted.shape[1])
    for j, ctype in enumerate(criteria_types):
        if ctype == "benefit":
            a_plus[j] = np.max(weighted[:, j])
            a_minus[j] = np.min(weighted[:, j])
        else:  # cost
            a_plus[j] = np.min(weighted[:, j])
            a_minus[j] = np.max(weighted[:, j])
    return a_plus, a_minus


def distances(weighted: np.ndarray, a_plus: np.ndarray, a_minus: np.ndarray) -> tuple:
    """Tahap 4: Jarak Euclidean ke solusi ideal."""
    d_plus = np.sqrt(np.sum((weighted - a_plus) ** 2, axis=1))
    d_minus = np.sqrt(np.sum((weighted - a_minus) ** 2, axis=1))
    return d_plus, d_minus


def preference_scores(d_plus: np.ndarray, d_minus: np.ndarray) -> np.ndarray:
    """Tahap 5: Nilai preferensi (closeness coefficient).

    C_i = D_i- / (D_i+ + D_i-)
    Semakin tinggi C_i, semakin dekat ke solusi ideal positif.
    """
    denom = d_plus + d_minus
    denom = np.where(denom == 0, 1e-12, denom)
    return d_minus / denom


def run_topsis(
    df: pd.DataFrame,
    criteria: list,
    weights: dict,
    types: dict | None = None,
    alt_column: str = "Ticker",
) -> pd.DataFrame:
    """Jalankan seluruh tahapan TOPSIS pada DataFrame.

    Args:
        df       : DataFrame berisi kolom alternatif (ticker) dan kolom-kolom kriteria.
        criteria : daftar nama kolom kriteria yang dipakai.
        weights  : dict {nama_kriteria: bobot}. Bobot akan dinormalisasi otomatis.
        types    : dict {nama_kriteria: "benefit"|"cost"}. Default mengikuti CRITERIA_TYPES.
        alt_column: kolom yang berisi nama alternatif (ticker).

    Returns:
        DataFrame berisi Ticker, skor preferensi, jarak D+ dan D-, serta ranking.
    """
    if types is None:
        types = CRITERIA_TYPES

    df = df.copy().reset_index(drop=True)
    matrix = df[criteria].to_numpy(dtype=float)

    # Validasi: nilai kriteria tidak boleh non-numeric
    if np.any(np.isnan(matrix)):
        raise ValueError("Matriks keputusan mengandung NaN. Lakukan preprocessing terlebih dahulu.")

    # Normalisasi bobot agar berjumlah 1
    w = np.array([weights[c] for c in criteria], dtype=float)
    if w.sum() == 0:
        raise ValueError("Total bobot tidak boleh 0.")
    w = w / w.sum()

    criteria_types_list = [types[c] for c in criteria]

    norm = normalize_matrix(matrix)
    weighted = weighted_matrix(norm, w)
    a_plus, a_minus = ideal_solutions(weighted, criteria_types_list)
    d_plus, d_minus = distances(weighted, a_plus, a_minus)
    scores = preference_scores(d_plus, d_minus)

    result = pd.DataFrame({
        alt_column: df[alt_column],
        "D+": d_plus,
        "D-": d_minus,
        "Preferensi (C)": scores,
    })
    result = result.sort_values("Preferensi (C)", ascending=False).reset_index(drop=True)
    result.insert(0, "Ranking", result.index + 1)
    return result


if __name__ == "__main__":
    # Contoh manual sederhana untuk validasi
    data = pd.DataFrame({
        "Ticker": ["A", "B", "C"],
        "PER": [10, 15, 8],
        "ROE": [20, 12, 18],
    })
    res = run_topsis(
        data,
        criteria=["PER", "ROE"],
        weights={"PER": 0.5, "ROE": 0.5},
        types={"PER": "cost", "ROE": "benefit"},
    )
    print(res)
